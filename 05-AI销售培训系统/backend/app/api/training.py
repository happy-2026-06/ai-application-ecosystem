"""Training API routes — role-play sessions, rounds, and SSE streaming."""
import json
import os
import re
import time
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.models.training import TrainingSession, TrainingRound
from app.core.auth import get_current_user
from app.schemas.training import (
    TrainingSessionCreate,
    TrainingSessionResponse,
    TrainingRoundResponse,
    TrainingRespondRequest,
    TrainingReportResponse,
)
from app.services.training_service import (
    CUSTOMER_TYPES,
    SCORE_DIMENSIONS,
    build_training_prompt,
    parse_ai_response,
    build_training_report_prompt,
)
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Session CRUD ───────────────────────────────────────────────────

@router.get("/sessions", response_model=list[TrainingSessionResponse])
async def list_training_sessions(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List current user's training sessions."""
    offset = (page - 1) * page_size
    result = await db.execute(
        select(TrainingSession)
        .where(TrainingSession.user_id == current_user.id)
        .order_by(TrainingSession.updated_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    return result.scalars().all()


@router.post("/sessions", response_model=TrainingSessionResponse, status_code=201)
async def create_training_session(
    request: TrainingSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new training session with customer type and product context."""
    session = TrainingSession(
        user_id=current_user.id,
        customer_type=request.customer_type,
        product_context=request.product_context,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)

    # Add AI customer opening as first round
    ctype = CUSTOMER_TYPES.get(request.customer_type, CUSTOMER_TYPES["picky"])
    opening_round = TrainingRound(
        training_session_id=session.id,
        round_number=0,
        user_response="（训练开始）",
        customer_response=ctype["opening"],
        coach_hint=None,
        scores=None,
    )
    db.add(opening_round)
    session.total_rounds = 1
    await db.flush()
    await db.refresh(session)
    return session


@router.get("/sessions/{session_id}", response_model=TrainingSessionResponse)
async def get_training_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a training session's details."""
    result = await db.execute(
        select(TrainingSession).where(
            TrainingSession.id == session_id,
            TrainingSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="训练会话不存在")
    return session


@router.delete("/sessions/{session_id}")
async def delete_training_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a training session and all its rounds."""
    result = await db.execute(
        select(TrainingSession).where(
            TrainingSession.id == session_id,
            TrainingSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="训练会话不存在")
    session.status = "deleted"
    await db.flush()
    return {"message": "训练会话已删除"}


# ── Rounds ─────────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/rounds", response_model=list[TrainingRoundResponse])
async def get_training_rounds(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all rounds for a training session."""
    # Verify ownership
    result = await db.execute(
        select(TrainingSession).where(
            TrainingSession.id == session_id,
            TrainingSession.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="训练会话不存在")

    result = await db.execute(
        select(TrainingRound)
        .where(TrainingRound.training_session_id == session_id)
        .order_by(TrainingRound.round_number.asc())
    )
    return result.scalars().all()


# ── SSE Streaming Respond ──────────────────────────────────────────

@router.post("/sessions/{session_id}/respond")
async def training_respond(
    session_id: str,
    request: TrainingRespondRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a sales response → SSE streaming returns AI customer reply + scores."""
    # Verify ownership
    result = await db.execute(
        select(TrainingSession).where(
            TrainingSession.id == session_id,
            TrainingSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="训练会话不存在")
    if session.status != "active":
        raise HTTPException(status_code=400, detail="训练会话已结束")

    current_round = session.total_rounds

    # Build conversation history
    rounds_result = await db.execute(
        select(TrainingRound)
        .where(TrainingRound.training_session_id == session_id)
        .order_by(TrainingRound.round_number.asc())
    )
    all_rounds = rounds_result.scalars().all()
    history_parts = []
    for r in all_rounds:
        if r.round_number == 0:
            history_parts.append(f"客户：{r.customer_response}")
        else:
            history_parts.append(f"销售：{r.user_response}")
            history_parts.append(f"客户：{r.customer_response}")
    history_text = "\n".join(history_parts)

    # Build prompt
    prompt = build_training_prompt(
        customer_type=session.customer_type,
        product_context=session.product_context,
        history=history_text,
        user_response=request.response,
        round_number=current_round,
    )

    async def generate_sse():
        start_time = time.time()
        raw_answer = ""

        try:
            # Try LLM
            try:
                from app.rag.chain import get_llm
                llm = get_llm()

                yield f"data: {json.dumps({'type': 'thinking', 'content': 'AI客户正在思考回应...'}, ensure_ascii=False)}\n\n"

                async for chunk in llm.astream(prompt):
                    token_text = _extract_token_text(chunk)
                    if token_text:
                        raw_answer += token_text
                        yield f"data: {json.dumps({'type': 'token', 'content': token_text}, ensure_ascii=False)}\n\n"
            except Exception as e:
                logger.warning("LLM unavailable, using fallback: %s", e)
                raw_answer = _build_fallback_response(session.customer_type, request.response, current_round)
                for char in raw_answer:
                    yield f"data: {json.dumps({'type': 'token', 'content': char}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.01)

            # Parse AI response
            parsed = parse_ai_response(raw_answer)
            customer_text = parsed["customer_response"]
            coach_hint = parsed["coach_hint"]
            scores = parsed["scores"]

            # Save round to DB
            training_round = TrainingRound(
                training_session_id=session.id,
                round_number=current_round,
                user_response=request.response,
                customer_response=customer_text,
                coach_hint=coach_hint,
                scores=scores,
            )
            db.add(training_round)
            session.total_rounds = current_round + 1

            # Update overall score
            if scores:
                all_scores = [r.scores for r in all_rounds if r.scores]
                all_scores.append(scores)
                if all_scores:
                    avg_scores = {}
                    for dim in SCORE_DIMENSIONS:
                        key = dim["key"]
                        vals = [s.get(key, 50) for s in all_scores if key in s]
                        avg_scores[key] = round(sum(vals) / len(vals)) if vals else 50
                    session.overall_score = round(sum(avg_scores.values()) / len(avg_scores))

            await db.flush()

            latency_ms = int((time.time() - start_time) * 1000)
            done_data = {
                'round_id': str(training_round.id),
                'customer_response': customer_text,
                'coach_hint': coach_hint,
                'scores': scores,
                'overall_score': session.overall_score,
                'round_number': current_round,
                'latency_ms': latency_ms,
            }
            yield f"data: {json.dumps({'type': 'done', 'data': done_data}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.exception("Training respond error: %s", e)
            yield f"data: {json.dumps({'type': 'error', 'content': '处理出错，请重试'}, ensure_ascii=False)}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── End Session & Report ───────────────────────────────────────────

@router.post("/sessions/{session_id}/end")
async def end_training_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """End a training session and compute final scores."""
    result = await db.execute(
        select(TrainingSession).where(
            TrainingSession.id == session_id,
            TrainingSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="训练会话不存在")

    session.status = "completed"
    await db.flush()

    # Push training data to DataHub
    try:
        from app.services.datahub_client import push_training_to_datahub
        rounds_result = await db.execute(
            select(TrainingRound)
            .where(TrainingRound.training_session_id == session_id)
            .order_by(TrainingRound.round_number.asc())
        )
        rounds = rounds_result.scalars().all()
        rounds_data = [
            {
                "user_response": r.user_response or "",
                "customer_response": r.customer_response or "",
                "scores": r.scores or {},
            }
            for r in rounds
        ]
        import asyncio
        asyncio.ensure_future(
            push_training_to_datahub(
                username=current_user.username,
                customer_type=session.customer_type or "unknown",
                rounds_data=rounds_data,
            )
        )
    except Exception:
        pass  # Best-effort, don't block training end

    return {"message": "训练已结束", "overall_score": session.overall_score}


@router.get("/sessions/{session_id}/report", response_model=TrainingReportResponse)
async def get_training_report(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a training summary report."""
    result = await db.execute(
        select(TrainingSession).where(
            TrainingSession.id == session_id,
            TrainingSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="训练会话不存在")

    rounds_result = await db.execute(
        select(TrainingRound)
        .where(TrainingRound.training_session_id == session_id)
        .order_by(TrainingRound.round_number.asc())
    )
    rounds = rounds_result.scalars().all()

    # Build score trend
    score_trend = []
    for r in rounds:
        if r.scores:
            entry = {"round": r.round_number, **r.scores}
            entry["overall"] = round(sum(r.scores.values()) / len(r.scores))
            score_trend.append(entry)

    # Compute averages per dimension
    avg_scores = {}
    if score_trend:
        for dim in SCORE_DIMENSIONS:
            key = dim["key"]
            vals = [s[key] for s in score_trend if key in s]
            avg_scores[key] = round(sum(vals) / len(vals)) if vals else 0

    # Generate strengths/improvements from scores
    strengths = []
    improvements = []
    for dim in SCORE_DIMENSIONS:
        key = dim["key"]
        label = dim["label"]
        val = avg_scores.get(key, 0)
        if val >= 70:
            strengths.append(f"{label}：{val}分 — 表现优秀")
        elif val < 50:
            improvements.append(f"{label}：{val}分 — 需要重点加强")

    if not strengths:
        strengths.append("多轮对话保持稳定表现")
    if not improvements:
        improvements.append("继续深化产品知识学习")

    # Recommendation based on lowest score
    lowest_dim = min(SCORE_DIMENSIONS, key=lambda d: avg_scores.get(d["key"], 0))
    recommendation = f"建议重点练习**{lowest_dim['label']}**，当前得分{avg_scores.get(lowest_dim['key'], 0)}分。可以多模拟{lowest_dim['label']}相关场景进行针对性训练。"

    return {
        "session": session,
        "rounds": rounds,
        "score_trend": score_trend,
        "strengths": strengths,
        "improvements": improvements,
        "recommendation": recommendation,
    }


# ── Customer Types Reference ───────────────────────────────────────

@router.get("/customer-types")
async def get_customer_types():
    """Get available customer types for training."""
    return [
        {
            "key": key,
            "name": ct["name"],
            "icon": ct["icon"],
            "difficulty": ct["difficulty"],
            "persona": ct["persona"],
        }
        for key, ct in CUSTOMER_TYPES.items()
    ]


# ── Private Helpers ────────────────────────────────────────────────

import asyncio

def _extract_token_text(chunk) -> str:
    """Extract text from a LangChain AIMessageChunk."""
    if hasattr(chunk, "content"):
        if isinstance(chunk.content, str) and chunk.content:
            return chunk.content
        if isinstance(chunk.content, list):
            return "".join(
                p.get("text", "") for p in chunk.content if isinstance(p, dict)
            )
    elif isinstance(chunk, str):
        return chunk
    return ""


def _build_fallback_response(customer_type: str, user_response: str, round_num: int) -> str:
    """Build a dev-mode fallback response when LLM is unavailable."""
    ctype = CUSTOMER_TYPES.get(customer_type, CUSTOMER_TYPES["picky"])
    fallbacks = {
        "picky": "你说的这些优势都是你自己说的，我凭什么相信你？有没有第三方评测的数据？",
        "price": "价格还是有点高…如果再便宜200块我就直接下单了。",
        "hesitant": "好吧，听起来还不错，但我还是想再去看看别家对比一下再决定。",
        "expert": "好的，这个解释还算合理。不过我还想知道你们的售后服务和保修政策具体是什么样的？",
    }
    customer = fallbacks.get(customer_type, "嗯，你说得挺有道理的，但我还要再想想。")
    return f"""**👤 客户**：{customer}
**💡 教练提示**：⚠️ 当前为开发模式（LLM未连接），请配置 DEEPSEEK_API_KEY 获取真实AI响应。
**📊 评分**：
- 流畅度: 60
- 说服力: 55
- 产品知识: 50
- 异议处理: 55
- 情绪控制: 65"""
