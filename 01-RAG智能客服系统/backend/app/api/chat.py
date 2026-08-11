"""Chat and session API routes."""
import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.models.session import Session
from app.models.message import Message
from app.core.auth import get_current_user
from app.schemas.chat import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    ChatRequest,
    MessageResponse,
    FeedbackRequest,
    EscalateRequest,
    EscalateResponse,
)

router = APIRouter()


# ── Session Management ────────────────────────────────────────────

@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List current user's chat sessions (sorted by last update)."""
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Session)
        .where(Session.user_id == current_user.id, Session.status == "active")
        .order_by(Session.updated_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    return result.scalars().all()


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(
    request: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new chat session."""
    session = Session(
        user_id=current_user.id,
        title=request.title or "新会话",
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a session's details."""
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == current_user.id,
        )
    )
    chat_session = result.scalar_one_or_none()
    if not chat_session:
        raise HTTPException(status_code=404, detail="会话不存在")
    return chat_session


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a session."""
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == current_user.id,
        )
    )
    chat_session = result.scalar_one_or_none()
    if not chat_session:
        raise HTTPException(status_code=404, detail="会话不存在")
    chat_session.status = "deleted"
    await db.flush()
    return {"message": "会话已删除"}


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rename a session."""
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == current_user.id,
        )
    )
    chat_session = result.scalar_one_or_none()
    if not chat_session:
        raise HTTPException(status_code=404, detail="会话不存在")
    chat_session.title = request.title
    await db.flush()
    await db.refresh(chat_session)
    return chat_session


# ── Messages ──────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    session_id: str,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get messages for a session (paginated)."""
    # Verify ownership
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == current_user.id,
        )
    )
    chat_session = result.scalar_one_or_none()
    if not chat_session:
        raise HTTPException(status_code=404, detail="会话不存在")

    offset = (page - 1) * page_size
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
        .offset(offset)
        .limit(page_size)
    )
    return result.scalars().all()


# ── Chat (SSE Streaming) ──────────────────────────────────────────

@router.post("/ask")
async def ask_question(
    request: ChatRequest,
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a question and receive a streaming answer via SSE.

    This is the core RAG endpoint. It streams the LLM response
    token-by-token via Server-Sent Events.
    """
    # Verify session ownership
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == current_user.id,
        )
    )
    chat_session = result.scalar_one_or_none()
    if not chat_session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # Auto-generate session title from first question
    if chat_session.message_count == 0:
        chat_session.title = request.question[:50] + ("..." if len(request.question) > 50 else "")

    async def generate_sse():
        from app.services.chat_service import stream_chat_response
        full_answer = ""
        async for event in stream_chat_response(
            db=db,
            session=chat_session,
            user=current_user,
            question=request.question,
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            # Collect full answer from done event for data push
            if event.get("type") == "done":
                full_answer = event.get("data", {}).get("full_answer", "")
        yield "data: [DONE]\n\n"

        # After SSE completes, push to DataHub asynchronously
        try:
            from shared.datahub_client import push_chat_to_datahub
            sources = []
            # Try to get sources from the session's latest assistant message
            import asyncio as _asyncio
            _asyncio.ensure_future(
                push_chat_to_datahub(
                    username=current_user.username,
                    question=request.question,
                    answer=full_answer,
                    sources=sources,
                )
            )
        except Exception:
            pass  # DataHub push is best-effort, don't block the chat

    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit feedback on an AI answer."""
    result = await db.execute(
        select(Message).where(
            Message.id == request.message_id,
            Message.user_id == current_user.id,  # Ownership check: prevent IDOR
        )
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")
    message.feedback = request.rating
    await db.flush()
    return {"message": "反馈已提交"}


# ── 转人工 ──────────────────────────────────────────────────────────

HUMAN_AGENT_QUEUE: list[dict] = []


@router.post("/escalate", response_model=EscalateResponse)
async def escalate_to_human(
    session_id: str = "",
    reason: str = "",
    body: EscalateRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """将当前会话转接人工客服

    支持两种传参方式：
    1. Query string: POST /api/chat/escalate?session_id=xxx
    2. JSON body: POST /api/chat/escalate  Body: {"session_id": "xxx"}

    将会话标记为待人工处理，保存转接原因。
    实际场景中会推送到客服工作台/企业微信/钉钉。
    """
    # 优先从 body 取，其次从 query string 取
    sid = (body and body.session_id) or session_id
    rsn = (body and body.reason) or reason

    if not sid:
        raise HTTPException(status_code=422, detail="缺少 session_id 参数")
    result = await db.execute(
        select(Session).where(
            Session.id == sid,
            Session.user_id == current_user.id,
        )
    )
    chat_session = result.scalar_one_or_none()
    if not chat_session:
        raise HTTPException(status_code=404, detail="会话不存在")
    ticket = {
        "session_id": sid,
        "user_id": str(current_user.id),
        "username": current_user.username,
        "reason": rsn or "用户请求人工客服",
        "status": "pending",
    }
    # NOTE: HUMAN_AGENT_QUEUE is an in-memory list — for production use,
    # this should be migrated to a database table (e.g. `human_agent_tickets`)
    # to survive server restarts and support multi-worker deployments.
    HUMAN_AGENT_QUEUE.append(ticket)

    # In the chat, insert a system message
    queue_position = len([t for t in HUMAN_AGENT_QUEUE if t["status"] == "pending"])
    if queue_position <= 1:
        wait_text = "即将为您服务"
    else:
        wait_text = f"前面有{queue_position - 1}人排队"
    system_msg = Message(
        session_id=sid,
        user_id=current_user.id,
        role="assistant",
        content=f"已为您转接人工客服，请稍候…（工单号：{len(HUMAN_AGENT_QUEUE)}）\n\n⏰ 人工客服工作时间：每天 9:00-22:00\n📞 紧急问题请拨打：400-888-6666",
    )
    db.add(system_msg)
    await db.flush()
    await db.refresh(system_msg)

    return {
        "message": "已转接人工客服",
        "ticket_id": len(HUMAN_AGENT_QUEUE),
        "queue_length": queue_position,
        "estimated_wait": wait_text,
    }
