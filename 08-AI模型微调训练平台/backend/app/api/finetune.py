"""Fine-tuning API routes."""
import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.models.message import Message
from app.models.finetune import FineTuneTask, ModelVersion, ABTest
from app.core.auth import get_current_user
from app.schemas.finetune import (
    FineTuneCreate, FineTuneResponse, ModelVersionResponse,
    ABTestCreate, ABTestResponse,
)
from app.services import finetune_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Tasks ─────────────────────────────────────────────────────────

@router.get("/tasks", response_model=list[FineTuneResponse])
async def list_tasks(page: int = 1, page_size: int = 20,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FineTuneTask).order_by(FineTuneTask.created_at.desc()).offset((page-1)*page_size).limit(page_size))
    return result.scalars().all()


@router.post("/tasks", response_model=FineTuneResponse, status_code=201)
async def create_task(request: FineTuneCreate,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    task = FineTuneTask(user_id=current_user.id, name=request.name, base_model=request.base_model,
        method=request.method, dataset_id=request.dataset_id,
        hyperparams={"learning_rate": request.learning_rate, "epochs": request.epochs, "batch_size": request.batch_size})
    db.add(task); await db.flush(); await db.refresh(task)
    task = await finetune_service.simulate_training(db, task)
    await db.refresh(task)
    return task


@router.get("/tasks/{task_id}", response_model=FineTuneResponse)
async def get_task(task_id: str,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FineTuneTask).where(FineTuneTask.id == task_id))
    t = result.scalar_one_or_none()
    if not t: raise HTTPException(status_code=404, detail="任务不存在")
    return t


@router.post("/tasks/{task_id}/stop", response_model=FineTuneResponse)
async def stop_task(task_id: str,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Stop a training task.

    NOTE on the `stop_requested` semantics: simulate_training runs
    synchronously inside the create-task request (no background worker), so a
    live run cannot actually be interrupted mid-training by this endpoint.
    Its main purpose is recovery — marking tasks that are stuck in the
    "running" state (e.g. left behind after a server crash mid-training) as
    "stopped", so the UI and dashboard reflect reality. It is idempotent:
    stopping an already-stopped task returns it unchanged.
    """
    result = await db.execute(select(FineTuneTask).where(FineTuneTask.id == task_id))
    t = result.scalar_one_or_none()
    if not t: raise HTTPException(status_code=404, detail="任务不存在")
    if t.status == "running":
        t.status = "stopped"
        await db.flush()
        await db.refresh(t)
        logger.info("Task %s stopped by user %s", task_id, current_user.id)
        return t
    if t.status == "stopped":
        return t
    raise HTTPException(status_code=400, detail=f"任务当前状态为「{t.status}」，无法停止")


# ── RLHF: Preference Data from Chat Feedback ─────────────────────

@router.get("/rlhf/preference-data")
async def get_rlhf_preference_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export chat feedback as an RLHF preference dataset.

    Feedback is collected through the chat module (POST /api/chat/feedback)
    and stored on Message.feedback ('positive' | 'negative'). This endpoint
    aggregates every rated message into a preference dataset that can feed
    reward-model training / DPO-style preference optimization, with
    positive/negative counts for a quick sanity check.
    """
    result = await db.execute(
        select(Message)
        .where(Message.feedback.isnot(None))
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()

    preferences = []
    positive = 0
    negative = 0
    for m in messages:
        is_positive = m.feedback == "positive"
        if is_positive:
            positive += 1
        else:
            negative += 1
        preferences.append({
            "message_id": str(m.id),
            "session_id": m.session_id,
            "role": m.role,
            "input": m.content,
            "preferred": "好评" if is_positive else "差评",
            "feedback": m.feedback,
            "timestamp": m.created_at.isoformat() if m.created_at else None,
        })

    return {
        "total": len(preferences),
        "positive": positive,
        "negative": negative,
        "preferences": preferences,
    }


# ── Model Versions ───────────────────────────────────────────────

@router.get("/tasks/{task_id}/models", response_model=list[ModelVersionResponse])
async def list_models(task_id: str,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ModelVersion).where(ModelVersion.task_id == task_id).order_by(ModelVersion.version_number.desc()))
    return result.scalars().all()


@router.patch("/models/{model_id}/deploy")
async def deploy_model(model_id: str,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ModelVersion).where(ModelVersion.id == model_id))
    mv = result.scalar_one_or_none()
    if not mv: raise HTTPException(status_code=404, detail="模型不存在")
    mv.is_deployed = True
    mv.api_endpoint = f"/api/v1/inference/{mv.id[:8]}"
    await db.flush()
    return {"message": "模型已部署", "endpoint": mv.api_endpoint}


# ── A/B Tests ────────────────────────────────────────────────────

@router.get("/tasks/{task_id}/abtests", response_model=list[ABTestResponse])
async def list_abtests(task_id: str,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ABTest).where(ABTest.task_id == task_id).order_by(ABTest.created_at.desc()))
    return result.scalars().all()


@router.post("/tasks/{task_id}/abtests", response_model=ABTestResponse, status_code=201)
async def create_abtest(task_id: str, request: ABTestCreate,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FineTuneTask).where(FineTuneTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task: raise HTTPException(status_code=404, detail="任务不存在")
    ab = await finetune_service.run_ab_test(db, task, request.prompt)
    return ab


# ── Cross-Project: Active Models API (for C端 to discover) ─────

@router.get("/models/active")
async def list_active_models(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all deployed models — other projects call this to discover available LLMs."""
    result = await db.execute(
        select(ModelVersion).where(ModelVersion.is_deployed == True).order_by(ModelVersion.created_at.desc())
    )
    models = result.scalars().all()
    return [
        {
            "id": str(m.id),
            "model_name": m.model_name,
            "version": m.version_number,
            "size_mb": m.size_mb,
            "api_endpoint": m.api_endpoint,
            "proxy_url": f"http://p8-backend:8000/api/finetune/models/{m.id}/proxy",
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in models
    ]


# ── Dashboard ─────────────────────────────────────────────────────

@router.get("/dashboard")
async def dashboard(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(FineTuneTask.id)))).scalar() or 0
    running = (await db.execute(select(func.count(FineTuneTask.id)).where(FineTuneTask.status == "running"))).scalar() or 0
    completed = (await db.execute(select(func.count(FineTuneTask.id)).where(FineTuneTask.status == "completed"))).scalar() or 0
    total_m = (await db.execute(select(func.count(ModelVersion.id)))).scalar() or 0
    deployed = (await db.execute(select(func.count(ModelVersion.id)).where(ModelVersion.is_deployed == True))).scalar() or 0
    recent = (await db.execute(select(FineTuneTask).order_by(FineTuneTask.created_at.desc()).limit(5))).scalars().all()
    return {"total_tasks": total, "running_tasks": running, "completed_tasks": completed,
        "total_models": total_m, "deployed_models": deployed, "recent_tasks": list(recent)}


# ── Cross-Project: Create task from DataHub dataset ─────────────

@router.post("/tasks/from-dataset/{dataset_id}", response_model=FineTuneResponse, status_code=201)
async def create_task_from_dataset(
    dataset_id: str,
    request: FineTuneCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a finetune task pulling data from 数据中枢(⑥)."""
    # 1. Fetch dataset from DataHub (Docker service name first, localhost fallback)
    data_items = []
    import asyncio
    urls = [
        f"http://p6-backend:8000/api/data/datasets/{dataset_id}/export-for-finetune",
        f"http://localhost:8606/api/data/datasets/{dataset_id}/export-for-finetune",
    ]
    for url in urls:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    url,
                    headers={"X-Internal-Call": "ai-ecosystem-internal-2026"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    data_items = data.get("samples", [])
                    break
        except Exception:
            continue  # Try next URL; fall back to empty dataset

    # 2. Create the task with dataset reference
    task = FineTuneTask(
        user_id=current_user.id, name=request.name, base_model=request.base_model,
        method=request.method, dataset_id=dataset_id,
        hyperparams={"learning_rate": request.learning_rate, "epochs": request.epochs, "batch_size": request.batch_size,
                      "dataset_items": len(data_items), "dataset_source": "datahub"},
    )
    db.add(task); await db.flush(); await db.refresh(task)
    task = await finetune_service.simulate_training(db, task)
    await db.refresh(task)
    return task


# ── Model Inference Proxy (Smart Proxy) ───────────────────────────

@router.post("/models/{model_id}/proxy")
async def model_inference_proxy(
    model_id: str,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Smart Proxy — 三层命中机制的微调模型推理代理。

    第1层：意图路由 — 识别业务领域（退货/促销/产品...）
    第2层：训练数据Few-shot — 从训练缓存中检索相关样本注入Prompt
    第3层：响应缓存 — 高频问题秒回，不重复调API

    Accepts optional rag_context from calling systems for RAG + Fine-tune synergy.
    """
    result = await db.execute(select(ModelVersion).where(ModelVersion.id == model_id))
    mv = result.scalar_one_or_none()
    if not mv:
        raise HTTPException(status_code=404, detail="模型不存在")

    if not mv.is_deployed:
        raise HTTPException(status_code=400, detail="模型尚未部署")

    message = body.get("message", body.get("prompt", ""))
    if not message:
        raise HTTPException(status_code=400, detail="请提供 message 或 prompt")

    # Caller-provided RAG context (from ①②⑤'s own knowledge base search)
    rag_context = body.get("rag_context", None)

    # ── Layer 3: Response Cache ─────────────────────────────────
    from app.services.smart_proxy import _get_cache_key, _check_cache, _set_cache
    cache_key = _get_cache_key(message)

    cached = _check_cache(cache_key)
    if cached:
        return {
            "model": mv.model_name,
            "model_id": str(mv.id),
            "response": cached["response"],
            "cached": True,
            "intent": cached.get("intent", ""),
        }

    # ── Smart Prompt Assembly ───────────────────────────────────
    from app.services.smart_proxy import build_smart_prompt
    full_prompt, metadata = build_smart_prompt(
        message=message,
        model_name=mv.model_name,
        training_domains=mv.training_domains,
        training_samples_cache=mv.training_samples_cache,
        rag_context=rag_context,
    )

    try:
        from app.rag.chain import get_llm
        llm = get_llm()
        resp = await llm.ainvoke(full_prompt)
        answer = resp.content if hasattr(resp, "content") else str(resp)

        # ── Cache the response ──────────────────────────────────
        _set_cache(cache_key, answer, metadata.get("intent_domain", ""))

        return {
            "model": mv.model_name,
            "model_id": str(mv.id),
            "response": answer,
            "cached": False,
            "intent": metadata.get("intent_domain", ""),
            "few_shot_count": metadata.get("few_shot_count", 0),
            "has_rag_context": metadata.get("has_rag_context", False),
        }
    except Exception as e:
        logger.warning("Smart proxy LLM call failed: %s", e)
        fallback = (
            f"[微调模型 {mv.model_name}]\n\n"
            f"用户输入: {message}\n\n"
            f"⚠️ 请配置 DEEPSEEK_API_KEY 以启用真实推理。\n\n"
            f"当前已在智能代理模式下运行：\n"
            f"- 意图识别: {metadata.get('intent_domain', '未知')}\n"
            f"- Few-shot样本: {metadata.get('few_shot_count', 0)} 条\n"
            f"- 训练数据域: {metadata.get('training_domains', [])}\n"
            f"- RAG上下文: {'有' if metadata.get('has_rag_context') else '无'}"
        )
        return {
            "model": mv.model_name,
            "model_id": str(mv.id),
            "response": fallback,
            "cached": False,
            "mode": "mock",
            "intent": metadata.get("intent_domain", ""),
            "few_shot_count": metadata.get("few_shot_count", 0),
        }


# ── Cache Management ─────────────────────────────────────────────

@router.get("/models/cache-stats")
async def get_cache_stats(current_user: User = Depends(get_current_user)):
    """Get Smart Proxy response cache statistics."""
    from app.services.smart_proxy import get_cache_stats
    return get_cache_stats()


@router.post("/models/cache-clear")
async def clear_cache(current_user: User = Depends(get_current_user)):
    """Clear all cached responses."""
    from app.services.smart_proxy import clear_cache
    count = clear_cache()
    return {"message": f"已清除 {count} 条缓存", "count": count}


def _get_internal_token() -> str:
    """Get a simple internal token for cross-project API calls."""
    return "internal-cross-project-call"
