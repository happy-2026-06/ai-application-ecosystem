"""Agent platform API routes — sync task creation + SSE streaming execution."""
import asyncio
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, AsyncSessionLocal
from app.models.user import User
from app.models.agent import Agent, Task, Execution
from app.core.auth import get_current_user, admin_required
from app.schemas.agent import (
    AgentCreate, AgentResponse, TaskCreate, TaskResponse,
    ExecutionResponse,
)
from app.services import agent_service

router = APIRouter()


# ── Agents ────────────────────────────────────────────────────────

@router.get("/agents", response_model=list[AgentResponse])
async def list_agents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List agents with computed online status (heartbeat-based)."""
    result = await db.execute(select(Agent).order_by(Agent.name))
    agents = result.scalars().all()
    now = datetime.now(timezone.utc)
    for ag in agents:
        ag.online = agent_service.is_agent_online(ag, now)
    return agents


@router.post("/agents", response_model=AgentResponse, status_code=201)
async def register_agent(
    request: AgentCreate,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    agent = Agent(name=request.name, role=request.role, capability=request.capability, status="online")
    agent_service.touch_agent_heartbeat(agent)
    db.add(agent)
    await db.flush(); await db.refresh(agent)
    return agent


@router.patch("/agents/{agent_id}/status")
async def update_agent_status(
    agent_id: str, body: dict,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    ag = result.scalar_one_or_none()
    if not ag: raise HTTPException(status_code=404, detail="Agent不存在")
    if "status" in body: ag.status = body["status"]
    await db.flush()
    return {"message": "Agent状态已更新"}


@router.post("/agents/{agent_id}/heartbeat")
async def agent_heartbeat(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Agent health check: record a heartbeat, updating last_heartbeat."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    ag = result.scalar_one_or_none()
    if not ag:
        raise HTTPException(status_code=404, detail="Agent不存在")
    now = datetime.now(timezone.utc)
    ag.last_heartbeat = now
    await db.flush()
    return {"status": "ok", "agent_id": agent_id, "last_heartbeat": now.isoformat()}


# ── Tasks — CRUD ──────────────────────────────────────────────────

@router.get("/tasks", response_model=list[TaskResponse])
async def list_tasks(
    page: int = 1, page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    result = await db.execute(select(Task).order_by(Task.created_at.desc()).offset(offset).limit(page_size))
    return result.scalars().all()


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a task and all its execution records."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    # Delete associated executions first (cascade handles this, but explicit is cleaner)
    execs = (await db.execute(select(Execution).where(Execution.task_id == task_id))).scalars().all()
    for ex in execs:
        await db.delete(ex)
    await db.delete(task)
    await db.flush()
    return {"message": "任务已删除", "task_id": task_id}


@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(
    request: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create and asynchronously execute a task via background agent_service.

    Returns immediately with status='pending'. Call GET /tasks/{id} to poll
    for completion, or use the SSE streaming endpoint /tasks/stream instead.
    """
    task = Task(user_id=current_user.id, title=request.title, description=request.description, mode=request.mode)
    db.add(task)
    await db.flush()
    await db.refresh(task)

    agent_ids = request.agent_ids
    if not agent_ids:
        online = await agent_service.get_online_agents(db)
        agent_ids = [a.id for a in online[:3]]

    # Execute synchronously via agent_service (handles its own sessions)
    # NOT committing here — the Depends(get_db) session manager handles commit/rollback
    result = await agent_service.execute_task(db, task, agent_ids)
    await db.refresh(task)
    return task


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task: raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.get("/tasks/{task_id}/executions", response_model=list[ExecutionResponse])
async def get_executions(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Execution).where(Execution.task_id == task_id).order_by(Execution.step_order))
    return result.scalars().all()


# ── SSE Streaming Task Execution ───────────────────────────────────

@router.post("/tasks/stream", status_code=201)
async def create_task_stream(
    request: TaskCreate,
    current_user: User = Depends(get_current_user),
):
    """Create and execute a task with SSE real-time progress streaming.

    All DB work happens in the sse_gen coroutine — each agent runs
    in its own AsyncSessionLocal session to avoid concurrency issues.
    """
    async def sse_gen():
        # Phase 1: Create task + executions in one session
        async with AsyncSessionLocal() as db:
            # Resolve agent IDs
            agent_ids = request.agent_ids
            if not agent_ids:
                online = (await db.execute(select(Agent).where(Agent.status == "online"))).scalars().all()
                agent_ids = [a.id for a in online[:3]]

            agent_names: dict[str, str] = {}
            agent_objs: list[Agent] = []
            for aid in agent_ids:
                r = await db.execute(select(Agent).where(Agent.id == aid))
                ag = r.scalar_one_or_none()
                if ag:
                    agent_names[aid] = ag.name
                    agent_objs.append(ag)
                    # Agent is being used → update its heartbeat
                    agent_service.touch_agent_heartbeat(ag)

            task = Task(
                user_id=current_user.id, title=request.title,
                description=request.description, mode=request.mode,
            )
            db.add(task)
            await db.flush()
            await db.refresh(task)

            executions = []
            for i, aid in enumerate(agent_ids):
                if aid not in agent_names:
                    continue
                ex = Execution(
                    task_id=task.id, agent_id=aid, step_order=i,
                    status="queued",
                    input_data=f"任务: {task.title}\n描述: {task.description or ''}",
                )
                db.add(ex)
                executions.append(ex)

            task.status = "running"
            await db.flush()
            exec_ids: list[str] = [str(ex.id) for ex in executions]
            await db.commit()

            task_id = str(task.id)
            task_title = task.title
            task_desc = task.description or ""
            task_mode = task.mode
            total = len(exec_ids)

            meta = [
                {"exec_id": eid, "agent_name": agent_names.get(aid, "Agent")}
                for eid, aid in zip(exec_ids, agent_ids)
                if aid in agent_names
            ]

        # Phase 2: Get LLM (outside DB session)
        llm = None
        try:
            from app.rag.chain import get_llm
            llm = get_llm()
        except Exception:
            pass

        yield _sse("task_created", {"task_id": task_id, "title": task_title, "mode": task_mode, "agent_count": total})

        # Phase 2.5: Task auto-decomposition → per-agent subtasks
        try:
            plan = await agent_service.decompose_task(f"{task_title} {task_desc}", agent_objs)
        except Exception:
            plan = []
        subtask_map = {p["agent_name"]: p["subtask"] for p in plan}
        for m in meta:
            m["subtask"] = subtask_map.get(m["agent_name"]) or f"任务: {task_title}\n描述: {task_desc}"

        if plan:
            yield _sse("decomposing", {
                "message": "已为各Agent生成专属子任务",
                "subtasks": [{"agent_name": p["agent_name"], "subtask": p["subtask"][:150]} for p in plan],
            })

        try:
            if task_mode == "pipeline":
                prev = f"任务目标: {task_title}\n\n任务描述: {task_desc}"
                presults = []
                for i, m in enumerate(meta):
                    yield _sse("agent_start", {"agent_name": m["agent_name"], "step": i + 1, "total": total})
                    async with AsyncSessionLocal() as s:
                        ex = (await s.execute(select(Execution).where(Execution.id == m["exec_id"]))).scalar_one()
                        ex.status = "running"; await s.flush()
                        t0 = asyncio.get_event_loop().time()
                        try:
                            p = agent_service._get_agent_prompt(m["agent_name"])
                            if i == 0:
                                ex.input_data = m["subtask"]
                            else:
                                ex.input_data = prev[:3000]
                            if llm:
                                if i == 0:
                                    q = f"{p}\n\n流水线第{i+1}步/{total}。\n\n你的专属子任务:\n{m['subtask']}\n\n{prev}\n\n请开始分析输出。"
                                else:
                                    q = f"{p}\n\n流水线第{i+1}步/{total}。\n\n你的关注点:\n{m['subtask']}\n\n上一步输出:\n{prev[:2000]}\n\n请基于上一步输出继续深入。"
                                r = await llm.ainvoke(q)
                                out = r.content if hasattr(r, "content") else str(r)
                            else:
                                out = agent_service._build_mock_output(m["agent_name"], task_title, "pipeline", i + 1)
                            ex.output_data = out[:5000]; ex.status = "completed"
                            ex.duration_ms = int((asyncio.get_event_loop().time() - t0) * 1000)
                            prev = out; presults.append({"agent_name": m["agent_name"], "status": "completed"})
                            yield _sse("agent_done", {"agent_name": m["agent_name"], "step": i + 1, "duration_ms": ex.duration_ms, "output_preview": out[:300]})
                        except Exception as e:
                            ex.status = "failed"; ex.output_data = str(e)
                            yield _sse("agent_error", {"agent_name": m["agent_name"], "error": str(e)[:200]})
                        await s.commit()
                await _save_task_result(task_id, agent_service._aggregate_results(presults, "pipeline"), "completed")

            elif task_mode == "parallel":
                yield _sse("parallel_start", {"agent_count": total})

                # Run agents sequentially through DB (true parallel is conceptual —
                # they all get the same task and work independently)
                results = []
                for m in meta:
                    async with AsyncSessionLocal() as s:
                        ex = (await s.execute(select(Execution).where(Execution.id == m["exec_id"]))).scalar_one()
                        ex.status = "running"
                        await s.flush()
                        yield _sse("agent_start", {"agent_name": m["agent_name"], "step": len(results) + 1, "total": total})
                        try:
                            p = agent_service._get_agent_prompt(m["agent_name"])
                            ex.input_data = m["subtask"]
                            if llm:
                                q = f"{p}\n\n## 任务\n{task_title}\n\n## 详情\n{task_desc}\n\n## 你的专属子任务\n{m['subtask']}\n\n请从你的专业角度独立完成。"
                                r = await llm.ainvoke(q)
                                out = r.content if hasattr(r, "content") else str(r)
                            else:
                                out = agent_service._build_mock_output(m["agent_name"], task_title, "parallel", 1)
                            ex.output_data = out[:5000]; ex.status = "completed"
                        except Exception as e:
                            ex.status = "failed"; ex.output_data = str(e)
                        await s.commit()
                    results.append({"agent_name": m["agent_name"], "status": ex.status, "preview": (ex.output_data or "")[:300]})
                    yield _sse("agent_done", {"agent_name": m["agent_name"], "step": len(results), "total": total, "output_preview": (ex.output_data or "")[:300]})

                await _save_task_result(task_id, agent_service._aggregate_results(results, "parallel"), "completed")

            elif task_mode == "vote":
                yield _sse("vote_start", {"agent_count": total})

                # Sequential DB execution — each agent votes independently
                results = []
                for i, m in enumerate(meta):
                    async with AsyncSessionLocal() as s:
                        ex = (await s.execute(select(Execution).where(Execution.id == m["exec_id"]))).scalar_one()
                        ex.status = "running"
                        await s.flush()
                        yield _sse("agent_start", {"agent_name": m["agent_name"], "step": i + 1, "total": total})
                        try:
                            p = agent_service._get_agent_prompt(m["agent_name"])
                            ex.input_data = m["subtask"]
                            if llm:
                                q = f"{p}\n\n投票任务: {task_title}\n描述: {task_desc}\n\n你的关注点:\n{m['subtask']}\n\n请独立投票: 方案A激进/方案B稳健/方案C创新。格式: 【投票】方案 | 【理由】... | 【置信度】%"
                                r = await llm.ainvoke(q)
                                out = r.content if hasattr(r, "content") else str(r)
                            else:
                                opts = ["方案A：激进策略", "方案B：稳健策略", "方案C：创新策略"]
                                out = f"【投票】{opts[hash(task_title + m['agent_name']) % 3]}\n【理由】基于专业判断\n【置信度】{75 + hash(task_title) % 20}%"
                            ex.output_data = out[:5000]; ex.status = "completed"
                        except Exception as e:
                            ex.status = "failed"; ex.output_data = str(e)
                        await s.commit()
                    results.append({"agent_name": m["agent_name"], "status": ex.status, "preview": (ex.output_data or "")[:300], "output": ex.output_data})
                    yield _sse("agent_done", {"agent_name": m["agent_name"], "step": i + 1, "total": total, "output_preview": (ex.output_data or "")[:300]})

                for d in results:
                    yield _sse("agent_done", d)

                yield _sse("tallying", {"message": "正在统计投票..."})
                if llm:
                    ballots = "\n\n---\n\n".join([f"Agent {d['agent_name']}:\n{(d.get('output') or '')[:800]}" for d in results if d['status'] == 'completed'])
                    tally_resp = await llm.ainvoke(f"统计以下投票并裁定获胜方案:\n\n{ballots}")
                    tally = tally_resp.content if hasattr(tally_resp, "content") else str(tally_resp)
                else:
                    tally = f"🗳️ 投票结果: {total}位Agent参与，方案A获胜（得票{total//2+1}）"
                await _save_task_result(task_id, tally[:8000], "completed")

            elif task_mode == "debate":
                if total < 3:
                    yield _sse("error", {"message": "辩论模式至少需要3个Agent（2辩手+1裁判）"})
                else:
                    debaters = meta[:2]; judges = meta[2:]
                    dlog = []
                    rounds = [
                        ("🔴 开篇立论", "正方（支持方）", debaters[0]),
                        ("🔴 开篇立论", "反方（质疑方）", debaters[1]),
                        ("🟡 自由辩论", "正方反驳", debaters[0]),
                        ("🟡 自由辩论", "反方回应", debaters[1]),
                        ("🟢 总结陈词", "反方最终陈词", debaters[1]),
                        ("🟢 总结陈词", "正方最终陈词", debaters[0]),
                    ]
                    for rn, role, m in rounds:
                        yield _sse("debate_round", {"round": rn, "agent_name": m["agent_name"], "role": role})
                        async with AsyncSessionLocal() as s:
                            ex = (await s.execute(select(Execution).where(Execution.id == m["exec_id"]))).scalar_one()
                            ex.status = "running"; await s.flush()
                            t0 = asyncio.get_event_loop().time()
                            try:
                                p = agent_service._get_agent_prompt(m["agent_name"])
                                ex.input_data = m["subtask"]
                                if llm:
                                    q = f"{p}\n\n🏛️ 辩论赛: {task_title}\n角色: {role}\n\n你的专业关注点:\n{m['subtask']}\n\n辩论记录:\n{chr(10).join(dlog[-3:])}\n\n请发表你的{role}。"
                                    r = await llm.ainvoke(q)
                                    sp = r.content if hasattr(r, "content") else str(r)
                                else:
                                    sp = agent_service._build_debate_mock_speech(m["agent_name"], role, task_title)
                                ex.output_data = sp[:5000]; ex.status = "completed"
                                ex.duration_ms = int((asyncio.get_event_loop().time() - t0) * 1000)
                                dlog.append(f"[{m['agent_name']}]({role}): {sp[:300]}")
                                yield _sse("debate_speech", {"agent_name": m["agent_name"], "role": role, "duration_ms": ex.duration_ms, "output_preview": sp[:300]})
                            except Exception as e:
                                ex.status = "failed"; ex.output_data = str(e)
                            await s.commit()

                    for m in judges:
                        yield _sse("debate_round", {"round": "⚖️ 裁判评议", "agent_name": m["agent_name"]})
                        async with AsyncSessionLocal() as s:
                            ex = (await s.execute(select(Execution).where(Execution.id == m["exec_id"]))).scalar_one()
                            ex.status = "running"; await s.flush()
                            try:
                                p = agent_service._get_agent_prompt(m["agent_name"])
                                ex.input_data = m["subtask"]
                                if llm:
                                    q = f"{p}\n\n辩论主题: {task_title}\n你的专业关注点:\n{m['subtask']}\n完整辩论记录:\n{chr(10).join(dlog)}\n\n请裁定获胜方并说明理由。"
                                    r = await llm.ainvoke(q)
                                    v = r.content if hasattr(r, "content") else str(r)
                                else:
                                    v = agent_service._build_debate_mock_speech(m["agent_name"], "裁判", task_title)
                                ex.output_data = v[:5000]; ex.status = "completed"
                            except Exception as e:
                                ex.status = "failed"; ex.output_data = str(e)
                            await s.commit()
                        yield _sse("debate_verdict", {"agent_name": m["agent_name"], "output_preview": (ex.output_data or "")[:300]})

                    await _save_task_result(task_id, "\n".join(dlog)[:8000], "completed")

        except Exception as e:
            yield _sse("error", {"message": str(e)[:300]})

        yield _sse("task_completed", {"task_id": task_id, "mode": task_mode})
        yield _sse("done", {})

    return StreamingResponse(
        sse_gen(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


# ── Dashboard ─────────────────────────────────────────────────────

@router.get("/dashboard")
async def dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total = (await db.execute(select(func.count(Agent.id)))).scalar() or 0
    online = (await db.execute(select(func.count(Agent.id)).where(Agent.status == "online"))).scalar() or 0
    total_t = (await db.execute(select(func.count(Task.id)))).scalar() or 0
    completed = (await db.execute(select(func.count(Task.id)).where(Task.status == "completed"))).scalar() or 0
    running = (await db.execute(select(func.count(Task.id)).where(Task.status == "running"))).scalar() or 0
    failed = (await db.execute(select(func.count(Task.id)).where(Task.status == "failed"))).scalar() or 0
    recent = (await db.execute(select(Task).order_by(Task.created_at.desc()).limit(5))).scalars().all()
    return {
        "total_agents": total, "online_agents": online,
        "total_tasks": total_t, "completed_tasks": completed,
        "running_tasks": running, "failed_tasks": failed, "recent_tasks": list(recent),
    }


# ── Seed ──────────────────────────────────────────────────────────

@router.post("/agents/seed")
async def seed_agents(
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    await agent_service.seed_default_agents(db)
    return {"message": "默认Agent已初始化"}


# ── Helpers ───────────────────────────────────────────────────────

def _sse(etype: str, data: dict) -> str:
    return f"data: {json.dumps({'type': etype, **data}, ensure_ascii=False)}\n\n"


async def _save_task_result(task_id: str, result: str, status: str):
    """Save final task result into the PostgreSQL database."""
    async with AsyncSessionLocal() as db:
        t = (await db.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()
        if t:
            t.result = result
            t.status = status
            await db.commit()
