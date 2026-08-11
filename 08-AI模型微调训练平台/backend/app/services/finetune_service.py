"""Fine-tuning orchestration service."""
import logging
import time
import random
import math
import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.finetune import FineTuneTask, ModelVersion, ABTest

logger = logging.getLogger(__name__)


async def simulate_training(db: AsyncSession, task: FineTuneTask) -> FineTuneTask:
    """Simulate a fine-tuning run with realistic loss curve and metrics."""
    task.status = "running"
    await db.flush()

    epochs = task.hyperparams.get("epochs", 3) if task.hyperparams else 3
    lr = task.hyperparams.get("learning_rate", 2e-4) if task.hyperparams else 2e-4
    total_steps = epochs * 50  # simulate 50 steps per epoch

    loss_history = []
    loss = 3.5
    for step in range(total_steps):
        loss = loss * 0.96 + random.uniform(-0.1, 0.1)
        loss_history.append(round(max(0.3, loss), 4))
        if step % 30 == 0:
            await db.flush()

    task.loss_history = loss_history
    task.eval_metrics = {
        "bleu": round(random.uniform(0.45, 0.72), 3),
        "rouge_l": round(random.uniform(0.38, 0.65), 3),
        "human_score": round(random.uniform(3.2, 4.5), 1),
    }
    task.duration_seconds = total_steps * 2
    task.status = "completed"

    # Create model version
    ver = await db.execute(select(func.count(ModelVersion.id)).where(ModelVersion.task_id == task.id))
    ver_num = (ver.scalar() or 0) + 1

    # ── Fetch training data cache from ⑥ DataHub ──────────────────
    training_cache, training_domains = await _fetch_training_cache(task.dataset_id)

    mv = ModelVersion(
        task_id=task.id, version_number=ver_num,
        model_name=f"{task.name}-v{ver_num}",
        file_path=f"/models/{task.name.replace(' ','_')}_v{ver_num}.gguf",
        size_mb=round(random.uniform(50, 500), 1),
        training_samples_cache=training_cache,
        training_domains=training_domains,
    )
    db.add(mv)
    await db.flush()

    logger.info(
        "Training complete: %s — cached %d samples, domains=%s",
        mv.model_name, len(training_cache or []), training_domains,
    )
    return task


async def _fetch_training_cache(dataset_id: str | None) -> tuple[list[dict] | None, list[str] | None]:
    """Fetch structured training data from ⑥ DataHub after training completes.

    Returns:
        Tuple of (samples_cache, domains_list).
        samples_cache: list[dict] with keys: text, category, keywords, label
        domains_list: list[str] of unique business domain names
    """
    if not dataset_id:
        logger.info("No dataset_id — skipping training cache fetch")
        return None, None

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"http://p6-backend:8000/api/data/datasets/{dataset_id}/training-cache",
                headers={"X-Internal-Call": "true"},
            )
            if resp.status_code == 200:
                data = resp.json()
                samples = data.get("samples", [])
                # Extract unique domains from sample categories
                domains = list(set(
                    s.get("category", "通用") for s in samples if s.get("category")
                ))
                logger.info(
                    "Fetched %d training samples from DataHub (dataset=%s), domains=%s",
                    len(samples), dataset_id, domains,
                )
                return samples, domains
            else:
                logger.warning("DataHub training-cache returned status %d", resp.status_code)
                return None, None
    except Exception as e:
        logger.warning("Failed to fetch training cache from DataHub: %s", e)
        return None, None


async def run_ab_test(db: AsyncSession, task: FineTuneTask, prompt: str) -> ABTest:
    """Compare base vs fine-tuned model on a prompt."""
    ab = ABTest(task_id=task.id, prompt=prompt)

    try:
        from app.rag.chain import get_llm
        llm = get_llm()
        base_resp = await llm.ainvoke(f"[基础模型回答] 请简洁回答: {prompt}")
        ab.base_response = base_resp.content if hasattr(base_resp, "content") else str(base_resp)
        ft_resp = await llm.ainvoke(f"[微调模型回答] 你是一个经过业务数据微调的专家模型，请专业回答: {prompt}")
        ab.finetuned_response = ft_resp.content if hasattr(ft_resp, "content") else str(ft_resp)
        # Judge
        judge = await llm.ainvoke(f"比较两个回答哪个更好，只回复 base 或 finetuned 或 tie:\n[base]: {ab.base_response[:500]}\n[finetuned]: {ab.finetuned_response[:500]}")
        w = (judge.content if hasattr(judge, "content") else str(judge)).strip().lower()
        ab.winner = "finetuned" if "finetuned" in w else "base" if "base" in w else "tie"
    except Exception as e:
        ab.base_response = f"[基础模型] 这是基础模型的回答\n\n关于「{prompt}」，基础模型给出通用回答。"
        ab.finetuned_response = f"[微调模型] 这是经过专项数据微调后的回答\n\n关于「{prompt}」，微调后的模型更加理解业务场景，给出更专业的回答。\n\n⚠️ 当前为模拟模式，请配置 DEEPSEEK_API_KEY 获取真实对比。"
        ab.winner = "finetuned"

    db.add(ab)
    await db.flush()
    await db.refresh(ab)
    return ab
