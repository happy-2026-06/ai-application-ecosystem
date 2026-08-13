"""Agent orchestration service: registration, task dispatch, execution.

Supports 4 differentiated execution modes:
- pipeline: Sequential, each Agent's output feeds the next Agent's input
- parallel: All Agents run simultaneously, results merged
- vote: All Agents vote independently, majority wins
- debate: Agents debate back-and-forth, a judge Agent decides the winner

Each Agent has a unique system prompt matching its role and capability.
"""
import logging
import time
import asyncio
import httpx
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent, Task, Execution
from app.config import settings
from app.rag.prompts import TASK_DECOMPOSE_PROMPT
from app.services.action_registry import get_action, format_action_body, get_action_url_candidates

logger = logging.getLogger(__name__)

# ── Built-in agents with DIFFERENTIATED system prompts ──────────────

BUILTIN_AGENTS = [
    {
        "name": "市场分析Agent",
        "role": "分析市场趋势、竞品情报、用户画像",
        "capability": "analysis",
        "system_prompt": """你是一个资深的**电商市场分析师**，拥有10年行业经验。

你的专长：
- 分析市场趋势和竞争格局
- 解读用户画像和消费行为数据
- 发现市场机会和潜在风险
- 提供数据驱动的战略建议

回答风格：结构化、有数据支撑、给出可执行的结论。使用SWOT分析、数据对比等框架。""",
    },
    {
        "name": "内容创作Agent",
        "role": "撰写营销文案、脚本、社交媒体内容",
        "capability": "content",
        "system_prompt": """你是一个顶级的**电商内容创意总监**，擅长爆款文案创作。

你的专长：
- 撰写高转化率的小红书/抖音/公众号文案
- 设计吸引眼球的标题和钩子
- 结构化内容（痛点→解决方案→行动号召）
- 适配不同平台风格（小红书种草风、抖音快节奏、公众号深度内容）

回答风格：创意十足、有感染力、直接给出可发布的成品内容。每篇包含标题+正文+话题标签。""",
    },
    {
        "name": "数据决策Agent",
        "role": "基于数据做决策建议、风险评估",
        "capability": "decision",
        "system_prompt": """你是一个冷静理性的**数据决策顾问**，擅长用数据说话。

你的专长：
- 从数据中提炼关键洞察
- 量化评估方案的风险和收益
- 建立决策矩阵（成本/收益/风险三维度）
- 给出明确的优先级排序

回答风格：理性、客观、用数字说话。每个决策建议附带置信度和风险提示。""",
    },
    {
        "name": "执行调度Agent",
        "role": "负责任务分解、资源调度、执行监控",
        "capability": "execution",
        "system_prompt": """你是一个高效务实的**执行项目经理**，擅长把事情落地。

你的专长：
- 将大目标拆解为可执行的SOP步骤
- 制定时间线和里程碑
- 识别关键路径和依赖关系
- 资源分配和风险预案

回答风格：结构化、时间线清晰、每个步骤带负责人和截止时间。""",
    },
    {
        "name": "质量审查Agent",
        "role": "审查输出质量、合规检查、纠错",
        "capability": "general",
        "system_prompt": """你是一个严谨的**质量审查专家**，负责把关所有输出的质量。

你的专长：
- 检查事实准确性和逻辑一致性
- 审查合规风险（广告法、平台规则）
- 评估内容质量和可读性
- 给出具体的改进建议

回答风格：一针见血指出问题，同时给出建设性的修改方案。批判性思维，不妥协于低质量输出。""",
    },
]


async def seed_default_agents(db: AsyncSession) -> None:
    """Ensure built-in agents are registered with their system prompts."""
    for ag in BUILTIN_AGENTS:
        result = await db.execute(select(Agent).where(Agent.name == ag["name"]))
        existing = result.scalar_one_or_none()
        if not existing:
            agent = Agent(
                name=ag["name"], role=ag["role"],
                capability=ag["capability"], status="online",
                system_prompt=ag["system_prompt"],
            )
            db.add(agent)
        else:
            # Update system prompt if it changed
            if existing.system_prompt != ag["system_prompt"]:
                existing.system_prompt = ag["system_prompt"]
    await db.flush()


# ── Task auto-decomposition ──────────────────────────────────────────
# Each capability has keyword lists: when a keyword appears in the task
# text, the matching agent receives a focused subtask prompt.
# "general" capability (质量审查) always participates.

CAPABILITY_LABELS: dict[str, str] = {
    "analysis": "市场分析",
    "content": "内容创作",
    "decision": "数据决策",
    "execution": "执行调度",
    "general": "质量审查",
}

CAPABILITY_KEYWORDS: dict[str, list[str]] = {
    "analysis": ["市场", "分析", "趋势", "竞品", "用户", "画像", "调研", "行业", "行情", "消费者", "品类", "受众"],
    "content": ["文案", "内容", "种草", "标题", "创作", "脚本", "推文", "公众号", "小红书", "抖音", "营销", "写", "分发", "海报"],
    "decision": ["决策", "风险", "评估", "预算", "ROI", "定价", "策略", "方案", "选择", "优先级", "数据", "投产", "效果"],
    "execution": ["执行", "计划", "排期", "流程", "调度", "SOP", "项目", "落地", "发布", "上线", "运营", "大促", "渠道", "投放", "复盘"],
    "general": ["质量", "审查", "合规", "检查", "审核", "校对", "验收"],
}


def _decompose_by_keywords(task_text: str, agents: list) -> list[dict]:
    """Fast, no-LLM task decomposition: match capability keywords against
    the task text. Matching agents get a focused subtask prompt; others keep
    the original task so they still have full context."""
    plan = []
    for a in agents:
        keywords = CAPABILITY_KEYWORDS.get(a.capability, [])
        matched = [kw for kw in keywords if kw and kw in task_text]
        if a.capability == "general" or matched:
            label = CAPABILITY_LABELS.get(a.capability, a.capability)
            subtask = f"请从{label}角度处理：{task_text[:300]}"
        else:
            subtask = task_text[:300]
        plan.append({"agent_name": a.name, "capability": a.capability, "subtask": subtask})
    return plan


def _parse_llm_decomposition(llm_text: str, agents: list, keyword_plan: list[dict]) -> list[dict]:
    """Map LLM decomposition output lines back to agents by name.
    Agents not mentioned in the LLM output fall back to their keyword subtask."""
    fallback = {p["agent_name"]: p["subtask"] for p in keyword_plan}
    parsed: dict[str, str] = {}
    for line in llm_text.splitlines():
        line = line.strip().lstrip("-*#0123456789.：: ").strip()
        if not line:
            continue
        for agent in agents:
            if agent.name in line:
                parts = line.split(agent.name, 1)
                remainder = parts[1].lstrip("：: -").strip() if len(parts) > 1 else ""
                parsed[agent.name] = remainder or fallback.get(agent.name, line)
                break
    if not parsed:
        return []
    return [
        {"agent_name": a.name, "capability": a.capability,
         "subtask": parsed.get(a.name) or fallback.get(a.name, f"请从{a.capability}角度处理任务")}
        for a in agents
    ]


async def decompose_task(task_text: str, agents: list) -> list[dict]:
    """Decompose a task into per-agent subtasks.

    Uses the LLM with TASK_DECOMPOSE_PROMPT when available; falls back to
    fast keyword matching (no LLM dependency) on any failure.

    Returns: [{"agent_name": str, "capability": str, "subtask": str}, ...]
    """
    agents = [a for a in agents if a]
    if not agents:
        return []

    keyword_plan = _decompose_by_keywords(task_text, agents)

    try:
        llm = await _get_llm()
        if llm is None:
            return keyword_plan

        agent_lines = "\n".join(
            f"- {a.name}（能力标签: {a.capability}，职责: {a.role}）" for a in agents
        )
        prompt = TASK_DECOMPOSE_PROMPT.format(question=task_text[:2000]) + (
            f"\n\n可用Agent:\n{agent_lines}\n\n"
            "请严格按以下格式为每个Agent生成一行子任务描述（不要编号，不要额外解释）:\n"
            "{Agent名称}: {子任务描述}"
        )
        resp = await llm.ainvoke(prompt)
        llm_text = resp.content if hasattr(resp, "content") else str(resp)
        plan = _parse_llm_decomposition(llm_text, agents, keyword_plan)
        if plan:
            logger.info("Task decomposed via LLM into %d subtasks", len(plan))
            return plan
    except Exception as e:
        logger.warning("LLM task decomposition failed (%s); using keyword fallback", e)

    return keyword_plan


# ── Agent heartbeat / health ─────────────────────────────────────────

HEARTBEAT_TIMEOUT_MINUTES = 5


def touch_agent_heartbeat(agent: Agent) -> None:
    """Record that an agent was used — last_heartbeat = activity timestamp."""
    agent.last_heartbeat = datetime.now(timezone.utc)


def is_agent_online(agent: Agent, now: datetime | None = None) -> bool:
    """An agent is online if its last heartbeat is within the timeout window,
    or if it is marked online and has never sent a heartbeat (fallback)."""
    now = now or datetime.now(timezone.utc)
    if agent.last_heartbeat is not None:
        return _as_utc(now) - _as_utc(agent.last_heartbeat) <= timedelta(minutes=HEARTBEAT_TIMEOUT_MINUTES)
    return agent.status == "online"


def _as_utc(dt: datetime) -> datetime:
    """Normalize a datetime to UTC (SQLite returns naive datetimes)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


# ── Agent lifecycle ───────────────────────────────────────────────

async def get_online_agents(db: AsyncSession) -> list[Agent]:
    result = await db.execute(select(Agent).where(Agent.status == "online"))
    return list(result.scalars().all())


# ── Task orchestration ────────────────────────────────────────────

async def execute_task(
    db: AsyncSession,
    task: Task,
    agent_ids: list[str],
) -> dict:
    """Main entry point: route to the correct mode handler."""
    mode_handlers = {
        "pipeline": _execute_pipeline,
        "parallel": _execute_parallel,
        "vote": _execute_vote,
        "debate": _execute_debate,
    }
    handler = mode_handlers.get(task.mode, _execute_parallel)
    return await handler(db, task, agent_ids)


# ── Pipeline Mode ─────────────────────────────────────────────────

async def _execute_pipeline(
    db: AsyncSession, task: Task, agent_ids: list[str],
) -> dict:
    """Sequential execution: each Agent's output feeds the next Agent."""
    # Create executions
    execs = await _create_executions(db, task, agent_ids)
    task.status = "running"
    await db.flush()

    results = []
    previous_output = f"任务目标: {task.title}\n\n任务描述: {task.description or '无'}"

    for i, exec in enumerate(execs):
        exec.status = "running"
        await db.flush()
        start = time.time()

        try:
            agent = await _get_agent(db, exec.agent_id)
            agent_prompt = _get_agent_prompt(agent.name)
            subtask = exec.input_data or f"任务: {task.title}\n描述: {task.description or ''}"

            # This agent receives the previous agent's output as input
            # (its own decomposed subtask is preserved for traceability)
            exec.input_data = f"【子任务】{subtask}\n\n【上一步输出】{previous_output[:2500]}"

            # Step 1: Try cross-project action
            action_output = await _try_cross_project_action(db, task, exec)

            if action_output:
                output = action_output
            else:
                llm = await _get_llm()
                if llm:
                    if i == 0:
                        # First agent: analyze the task
                        prompt = f"""{agent_prompt}

## 你是流水线的第 {i + 1} 步（共 {len(execs)} 步）

## 你的专属子任务（任务自动拆解）
{subtask}

## 任务信息
{previous_output}

## 请开始你的分析，输出结果将传递给下一步Agent。"""
                    else:
                        # Subsequent agents: build on previous work
                        prompt = f"""{agent_prompt}

## 你是流水线的第 {i + 1} 步（共 {len(execs)} 步）

## 你的关注点（任务自动拆解）
{subtask}

## 上一步Agent的输出
{previous_output[:2000]}

## 请基于上一步的成果继续深入，补充你的专业视角。输出将传递给下一步Agent。"""

                    response = await llm.ainvoke(prompt)
                    output = response.content if hasattr(response, "content") else str(response)
                else:
                    output = _build_mock_output(agent.name, task.title, "pipeline", i + 1)

            exec.output_data = output[:5000]
            exec.status = "completed"
            exec.duration_ms = int((time.time() - start) * 1000)
            previous_output = output  # Feed forward to next agent
            results.append({"agent_id": exec.agent_id, "agent_name": agent.name, "output": output[:5000], "status": "completed"})

        except Exception as e:
            exec.status = "failed"
            exec.output_data = str(e)
            results.append({"agent_id": exec.agent_id, "output": str(e), "status": "failed"})

        await db.flush()

    task.status = "completed"
    task.result = _aggregate_results(results, "pipeline")
    await db.flush()
    return {"task_id": str(task.id), "mode": "pipeline", "results": results, "aggregated": task.result}


# ── Parallel Mode ──────────────────────────────────────────────────

async def _execute_parallel(
    db: AsyncSession, task: Task, agent_ids: list[str],
) -> dict:
    """All Agents execute independently on the same task.

    IMPORTANT: To avoid asyncio+PostgreSQL transaction conflicts,
    agents execute sequentially within the shared DB session.
    The 'parallel' mode is semantically parallel — each agent works on
    the SAME task independently, but DB writes are serialized.
    """
    execs = await _create_executions(db, task, agent_ids)
    task.status = "running"
    await db.flush()

    results = []
    for exec in execs:
        exec.status = "running"
        await db.flush()
        start = time.time()

        try:
            agent = await _get_agent(db, exec.agent_id)
            agent_prompt = _get_agent_prompt(agent.name)
            subtask = exec.input_data or f"任务: {task.title}\n描述: {task.description or ''}"

            action_output = await _try_cross_project_action(db, task, exec)

            if action_output:
                output = action_output
            else:
                llm = await _get_llm()
                if llm:
                    prompt = f"""{agent_prompt}

## 任务
{task.title}

## 任务详情
{task.description or '无详细描述'}

## 你的专属子任务（任务自动拆解）
{subtask}

## 请从你的专业角度出发，独立完成这个任务。不需要参考其他Agent。"""
                    response = await llm.ainvoke(prompt)
                    output = response.content if hasattr(response, "content") else str(response)
                else:
                    output = _build_mock_output(agent.name, task.title, "parallel", 1)

            exec.output_data = output[:5000]
            exec.status = "completed"
            exec.duration_ms = int((time.time() - start) * 1000)
            results.append({"agent_id": exec.agent_id, "agent_name": agent.name, "output": output[:5000], "status": "completed"})

        except Exception as e:
            exec.status = "failed"
            exec.output_data = str(e)
            results.append({"agent_id": exec.agent_id, "output": str(e), "status": "failed"})

        await db.flush()

    task.status = "completed"
    task.result = _aggregate_results(results, "parallel")
    await db.flush()
    return {"task_id": str(task.id), "mode": "parallel", "results": results, "aggregated": task.result}


# ── Vote Mode ──────────────────────────────────────────────────────

async def _execute_vote(
    db: AsyncSession, task: Task, agent_ids: list[str],
) -> dict:
    """All Agents vote independently, majority decides the best answer.

    Sequential DB execution — semantic 'vote' means each agent independently
    evaluates the same question and casts a vote. Votes are then tallied.
    """
    if len(agent_ids) < 2:
        return await _execute_parallel(db, task, agent_ids)

    execs = await _create_executions(db, task, agent_ids)
    task.status = "running"
    await db.flush()

    # Each agent casts a vote sequentially within the shared DB session
    results = []
    for exec in execs:
        exec.status = "running"
        await db.flush()
        start = time.time()

        try:
            agent = await _get_agent(db, exec.agent_id)
            agent_prompt = _get_agent_prompt(agent.name)
            subtask = exec.input_data or f"投票任务: {task.title}"

            llm = await _get_llm()
            if llm:
                prompt = f"""{agent_prompt}

## 投票任务
{task.title}

## 任务详述
{task.description or '无'}

## 你的关注点（任务自动拆解）
{subtask}

## 请独立投票
1. 先给出你的答案（方案A/方案B/自定义方案）
2. 列出你的决策理由（至少2条）
3. 标注你的置信度（0-100%）
4. 格式: 【投票】<你的方案> | 【理由】<理由列表> | 【置信度】<百分比>"""
                response = await llm.ainvoke(prompt)
                output = response.content if hasattr(response, "content") else str(response)
            else:
                options = ["方案A：激进策略", "方案B：稳健策略", "方案C：创新策略"]
                choice = options[hash(task.title + agent.name) % 3]
                output = f"【投票】{choice}\n【理由】1.基于{agent.name}的专业判断 2.综合风险评估\n【置信度】{75 + hash(task.title) % 20}%"

            exec.output_data = output[:5000]
            exec.status = "completed"
            exec.duration_ms = int((time.time() - start) * 1000)
            results.append({"agent_id": exec.agent_id, "agent_name": agent.name, "output": output[:5000], "status": "completed"})

        except Exception as e:
            exec.status = "failed"
            exec.output_data = str(e)
            results.append({"agent_id": exec.agent_id, "output": str(e), "status": "failed"})

        await db.flush()

    # Phase 2: Tally votes with LLM judge
    tally = await _tally_votes(task.title, results)

    task.status = "completed"
    task.result = tally
    await db.flush()
    return {"task_id": str(task.id), "mode": "vote", "results": results, "aggregated": tally}


async def _tally_votes(title: str, results: list[dict]) -> str:
    """Use LLM as the vote tally judge."""
    ballots = "\n\n---\n\n".join(
        f"## Agent #{i + 1}: {r.get('agent_name', 'Unknown')}\n{r.get('output', '')[:800]}"
        for i, r in enumerate(results) if r["status"] == "completed"
    )

    llm = await _get_llm()
    if llm:
        judge_prompt = f"""你是一个公正的裁判。以下是 {len(results)} 个Agent对「{title}」的独立投票。

{ballots}

## 请统计并裁定：
1. **得票统计**：列出各方案得票数
2. **裁判意见**：综合各方理由，哪个方案最优？为什么？
3. **最终裁定**：宣布获胜方案，并给出综合建议

格式：🗳️ **投票结果**: ... | 👨‍⚖️ **裁判裁定**: ..."""
        resp = await llm.ainvoke(judge_prompt)
        return resp.content if hasattr(resp, "content") else str(resp)

    # Mock tally
    return f"""## 🗳️ 投票结果统计

**{len(results)} 位Agent参与投票**

{ballots}

---

👨‍⚖️ **裁判裁定**: 综合{len(results)}位专家的意见，多维度评估后给出最终建议。⚠️ (配置DEEPSEEK_API_KEY获取真实裁定)"""


# ── Debate Mode ─────────────────────────────────────────────────────

async def _execute_debate(
    db: AsyncSession, task: Task, agent_ids: list[str],
) -> dict:
    """Agents debate back-and-forth. A judge Agent summarizes and decides.

    Debate flow:
    1. Agent A makes opening argument (正方)
    2. Agent B rebuts (反方)
    3. Agent A counters (正方反驳)
    4. Agent B makes closing (反方总结)
    5. Judge delivers verdict
    """
    if len(agent_ids) < 3:
        # Need at least 3 agents for debate (2 debaters + 1 judge)
        return await _execute_parallel(db, task, agent_ids)

    execs = await _create_executions(db, task, agent_ids)
    task.status = "running"
    await db.flush()

    # Assign roles: first 2 as debaters, rest as judges
    debater_a = execs[0]
    debater_b = execs[1]
    judge_execs = execs[2:]

    agent_a = await _get_agent(db, debater_a.agent_id)
    agent_b = await _get_agent(db, debater_b.agent_id)
    prompt_a = _get_agent_prompt(agent_a.name)
    prompt_b = _get_agent_prompt(agent_b.name)

    debate_log: list[str] = []
    debate_log.append(f"# 🏛️ 辩论赛: {task.title}\n")
    debate_log.append(f"## 正方: {agent_a.name} ({agent_a.role})\n")
    debate_log.append(f"## 反方: {agent_b.name} ({agent_b.role})\n")

    llm = await _get_llm()
    topic = task.title
    description = task.description or ""

    async def agent_speak(exec: Execution, agent: Agent, system_prompt: str, role: str, context: str) -> str:
        exec.status = "running"
        await db.flush()
        start = time.time()
        subtask = exec.input_data or ""

        try:
            if llm:
                prompt = f"""{system_prompt}

## 🏛️ 你正在参加一场辩论赛

你的角色: **{role}**
辩论主题: {topic}
背景: {description}

## 你的专业关注点（任务自动拆解）
{subtask}

## 之前的辩论记录
{context[:2000]}

## 现在请发表你的{role}观点。要有理有据，直接回应对方观点。"""
                resp = await llm.ainvoke(prompt)
                speech = resp.content if hasattr(resp, "content") else str(resp)
            else:
                speech = _build_debate_mock_speech(agent.name, role, topic)

            exec.output_data = speech[:5000]
            exec.status = "completed"
            exec.duration_ms = int((time.time() - start) * 1000)
            return speech
        except Exception as e:
            exec.status = "failed"
            exec.output_data = str(e)
            return f"[{agent.name} 发言失败: {e}]"

    # Round 1: Opening arguments
    debate_log.append("\n## 🔴 Round 1: 开篇立论\n")
    speech_a1 = await agent_speak(debater_a, agent_a, prompt_a, "正方（支持方）", debate_log[-1])
    debate_log.append(f"\n### {agent_a.name} (正方):\n{speech_a1}\n")

    speech_b1 = await agent_speak(debater_b, agent_b, prompt_b, "反方（质疑方）", debate_log[-1])
    debate_log.append(f"\n### {agent_b.name} (反方):\n{speech_b1}\n")

    # Round 2: Rebuttal
    debate_log.append("\n## 🟡 Round 2: 自由辩论\n")
    speech_a2 = await agent_speak(debater_a, agent_a, prompt_a, "正方（反驳反方观点）", debate_log[-1])
    debate_log.append(f"\n### {agent_a.name} 反驳:\n{speech_a2}\n")

    speech_b2 = await agent_speak(debater_b, agent_b, prompt_b, "反方（回应正方反驳）", debate_log[-1])
    debate_log.append(f"\n### {agent_b.name} 回应:\n{speech_b2}\n")

    # Round 3: Closing statements
    debate_log.append("\n## 🟢 Round 3: 总结陈词\n")
    closing_b = await agent_speak(debater_b, agent_b, prompt_b, "反方（最终陈词）", debate_log[-1])
    debate_log.append(f"\n### {agent_b.name} 最终陈词:\n{closing_b}\n")

    closing_a = await agent_speak(debater_a, agent_a, prompt_a, "正方（最终陈词）", debate_log[-1])
    debate_log.append(f"\n### {agent_a.name} 最终陈词:\n{closing_a}\n")

    # Judge verdicts
    debate_log.append("\n## ⚖️ 裁判评议\n")
    judge_results = []
    for j_exec in judge_execs:
        judge_agent = await _get_agent(db, j_exec.agent_id)
        judge_prompt = _get_agent_prompt(judge_agent.name)

        verdict = await agent_speak(j_exec, judge_agent, judge_prompt,
            f"裁判（请根据以上辩论内容，裁定正方还是反方获胜，并说明理由）",
            debate_log[-1])
        debate_log.append(f"\n### {judge_agent.name} 裁定:\n{verdict}\n")
        judge_results.append({"agent_name": judge_agent.name, "verdict": verdict})

    # Build results
    full_transcript = "\n".join(debate_log)

    results = [
        {"agent_id": debater_a.agent_id, "agent_name": agent_a.name, "output": f"{speech_a1}\n\n---\n{speech_a2}\n\n---\n{closing_a}"[:5000], "status": "completed"},
        {"agent_id": debater_b.agent_id, "agent_name": agent_b.name, "output": f"{speech_b1}\n\n---\n{speech_b2}\n\n---\n{closing_b}"[:5000], "status": "completed"},
    ]
    for j_exec, jr in zip(judge_execs, judge_results):
        results.append({"agent_id": j_exec.agent_id, "agent_name": jr["agent_name"], "output": jr["verdict"][:5000], "status": "completed"})

    task.status = "completed"
    task.result = full_transcript[:8000]
    await db.flush()

    return {"task_id": str(task.id), "mode": "debate", "results": results, "aggregated": full_transcript[:8000]}


# ── Cross-Project Actions (action_registry) ──────────────────────────

# Task-intent keywords → registered action name (see app.services.action_registry)
ACTION_INTENTS: list[tuple[tuple[str, ...], str]] = [
    (("文案", "种草", "内容", "生成", "写"), "灵笔-生成文案"),
    (("视频", "脚本", "分镜", "短视频"), "视界-生成脚本"),
    (("图库", "素材", "图片", "搜索素材"), "图库-搜索素材"),
    (("客服", "faq", "知识库", "咨询"), "客服-搜索知识库"),
    (("训练", "话术", "培训"), "话术-创建训练"),
    (("数据", "数据集", "查询数据"), "数据-查询数据集"),
]


def _action_params(action_name: str, title: str) -> dict:
    """Build the parameter values for an action's body template."""
    if action_name == "灵笔-生成文案":
        return {"prompt": f"请生成关于「{title}」的营销文案"}
    if action_name == "视界-生成脚本":
        return {"prompt": f"请生成关于「{title}」的短视频分镜脚本"}
    if action_name == "图库-搜索素材":
        return {"query": title}
    if action_name == "客服-搜索知识库":
        return {"query": title}
    if action_name == "话术-创建训练":
        return {"context": title}
    return {}


async def _call_action(action_name: str, urls: list[str], method: str, body: dict) -> str:
    """Call a registered action across its candidate URLs — Docker service
    name first, localhost fallback second (local dev). Returns a
    human-readable result line."""
    # 数据中枢(⑥)内部认证使用共享密钥；其他项目的普通 API 仍需要 JWT，
    # 跨项目编排调用会得到 401 并优雅记录到任务结果中（预期行为）。
    headers = {"X-Internal-Call": "ai-ecosystem-internal-2026", "Content-Type": "application/json"}
    last_error = "无可用地址"
    async with httpx.AsyncClient(timeout=30.0) as client:
        for url in urls:
            try:
                if method == "GET":
                    resp = await client.get(url, headers=headers, params=body or None, timeout=30.0)
                else:
                    resp = await client.post(url, headers=headers, json=body or {}, timeout=30.0)

                if resp.status_code in (200, 201):
                    data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"text": resp.text[:2000]}
                    logger.info("Cross-project action %s succeeded via %s", action_name, url)
                    return f"[{action_name}] ✅ 成功调用 ({url})\n返回: {json.dumps(data, ensure_ascii=False)[:1000]}"
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
            except Exception as e:
                last_error = f"调用失败: {str(e)[:200]}"
                logger.debug("Cross-project action %s failed via %s: %s", action_name, url, e)
    return f"[{action_name}] ❌ {last_error}"


async def _try_cross_project_action(
    db: AsyncSession,
    task: Task,
    execution: Execution,
) -> str | None:
    """Try to execute cross-project actions matched from the action registry."""
    task_text = f"{task.title} {task.description or ''}".lower()

    action_names: list[str] = []
    for keywords, action_name in ACTION_INTENTS:
        if action_name not in action_names and any(kw in task_text for kw in keywords):
            action_names.append(action_name)

    if not action_names:
        return None

    results = []
    for action_name in action_names:
        action = get_action(action_name)
        if not action:
            logger.warning("Action %s not found in registry", action_name)
            continue
        body = format_action_body(action_name, **_action_params(action_name, task.title))
        urls = get_action_url_candidates(action_name)
        results.append(await _call_action(action_name, urls, action["method"], body))

    return f"## 🌐 跨系统联动执行结果\n\n" + "\n\n".join(results)


# ── Private Helpers ────────────────────────────────────────────────

async def _create_executions(db: AsyncSession, task: Task, agent_ids: list[str]) -> list:
    """Create Execution records for a task, one per online agent.

    Each execution receives its own decomposed subtask (task auto-decomposition)
    instead of the shared task, and the agent's heartbeat is refreshed.
    """
    task_text = f"{task.title} {task.description or ''}"
    resolved: list[tuple[int, Agent]] = []
    for i, aid in enumerate(agent_ids):
        result = await db.execute(select(Agent).where(Agent.id == aid))
        agent = result.scalar_one_or_none()
        if not agent or agent.status != "online":
            continue
        resolved.append((i, agent))

    # Task auto-decomposition: each agent gets a focused subtask prompt
    plan = await decompose_task(task_text, [a for _, a in resolved])
    subtasks = {p["agent_name"]: p["subtask"] for p in plan}

    execs = []
    for i, agent in resolved:
        touch_agent_heartbeat(agent)  # Agent is being used → heartbeat update
        exec = Execution(
            task_id=task.id, agent_id=agent.id,
            step_order=i, status="queued",
            input_data=subtasks.get(agent.name) or f"任务: {task.title}\n描述: {task.description or ''}",
        )
        db.add(exec)
        execs.append(exec)
    await db.flush()
    return execs


async def _get_agent(db: AsyncSession, agent_id: str) -> Agent:
    """Get an Agent by ID. Returns a mock Agent if not found (defensive)."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if agent:
        return agent
    return Agent(name="未知Agent", role="通用执行者", capability="general", status="online")


def _get_agent_prompt(agent_name: str) -> str:
    """Get the differentiated system prompt for an agent by name."""
    for ag in BUILTIN_AGENTS:
        if ag["name"] == agent_name:
            return ag["system_prompt"]
    return "你是一个专业的AI助手，请用专业、精准的方式回答。如果需要分析，请结构化呈现。"


async def _get_llm():
    """Get the LLM singleton, or None if not configured."""
    try:
        from app.rag.chain import get_llm
        return get_llm()
    except Exception:
        return None


def _build_mock_output(agent_name: str, title: str, mode: str, step: int) -> str:
    """Mock output when LLM is unavailable."""
    mock_templates = {
        "市场分析Agent": f"""## 📊 市场分析报告

**分析对象**: {title}

### 1. 市场概况
- 当前行业规模：约500亿人民币
- 年增长率：15-20%
- 竞争格局：头部集中，腰部差异化机会明显

### 2. 目标用户画像
- 核心人群：25-35岁一线城市女性
- 消费偏好：注重品质、愿意为设计溢价
- 决策路径：小红书种草 → 比价 → 下单

### 3. 机会点
1. 内容电商渠道增速超预期
2. 下沉市场渗透率提升空间大
3. AI驱动个性化推荐尚未充分应用

⚠️ 当前为Mock模式，请配置 DEEPSEEK_API_KEY 获取真实AI分析。""",

        "内容创作Agent": f"""## ✍️ 内容创作方案

**创作主题**: {title}

### 📱 小红书种草文案
**标题**: 🔥 被问了800遍！{title}的秘密终于藏不住了

**正文**:
姐妹们！我熬夜整理的超全攻略来了！📝

{title}这件事，90%的人都做错了...

【全文Mock模式 — 配置API Key获取真实生成】

### 🏷️ 话题标签
#好物分享 #{title} #种草 #购物攻略 #小白必看""",

        "数据决策Agent": f"""## 🧠 数据决策分析

**决策问题**: {title}

### 📈 关键数据
| 维度 | 数据 | 趋势 |
|------|------|------|
| 投产比 | 1:3.2 | ↑ |
| 点击率 | 4.8% | → |
| 转化率 | 2.1% | ↑ |

### ✅ 建议优先级
1. [高优] 内容营销投入增加30%
2. [中优] 优化落地页转化漏斗
3. [低优] 拓展新渠道测试

⚠️ Mock模式 — 配置API Key获取真实数据决策。""",

        "执行调度Agent": f"""## ⚡ 执行方案

**项目**: {title}

### 📋 执行SOP
| 步骤 | 任务 | 负责人 | 截止时间 |
|------|------|--------|----------|
| 1 | 需求确认 | PM | D+1 |
| 2 | 内容准备 | 内容团队 | D+3 |
| 3 | 渠道配置 | 运营 | D+4 |
| 4 | 发布上线 | 技术 | D+5 |
| 5 | 数据复盘 | 所有人 | D+7 |

### ⚠️ 风险预案
- 内容审核不通过 → 备选方案B
- 流量不及预期 → 追加投放预算

⚠️ Mock模式""",

        "质量审查Agent": f"""## 🔍 质量审查报告

**审查对象**: {title}

### ✅ 合规检查
- [x] 广告法合规 ✓
- [x] 平台规则 ✓
- [x] 数据引用准确 ✓

### ⚠️ 需改进
1. 语言表达可更简洁（建议减少20%副词）
2. 需补充数据来源引用
3. 标题吸引力评分：7/10 → 建议A/B测试

⚠️ Mock模式 — 配置API Key获取真实审查。""",
    }

    return mock_templates.get(
        agent_name,
        f"**{agent_name} 执行结果 (模式: {mode}, 步骤: {step})**\n\n关于「{title}」的分析已完成。\n\n⚠️ 当前为Mock模式，请配置 DEEPSEEK_API_KEY 获取真实AI分析。"
    )


def _build_debate_mock_speech(agent_name: str, role: str, topic: str) -> str:
    """Mock debate speech."""
    if "正方" in role:
        return f"""**{agent_name}（正方）发言**：

关于「{topic}」，我方的核心观点是：

1. **市场机遇明确**：当前市场正在高速增长期，先发优势至关重要
2. **用户需求真实存在**：调研数据显示超60%目标用户有明确需求
3. **成本可控**：采用MVP策略，初始投入可在3个月内验证

因此我方认为：应该积极投入，抢占先机。"""
    elif "反方" in role:
        return f"""**{agent_name}（反方）发言**：

关于「{topic}」，我方的质疑是：

1. **市场增速可能在放缓**：需要更详细的数据支撑
2. **竞争壁垒不高**：头部玩家已有先发优势
3. **ROI不确定**：缺乏具体的投入产出测算

因此我方认为：应该在决策前进行更充分的调研。"""
    else:
        return f"""**{agent_name}（裁判）裁定**：

综合双方论点和提供的证据：

- 正方论据充分度：⭐⭐⭐⭐ (4/5)
- 反方论据充分度：⭐⭐⭐ (3/5)

**最终裁定：正方（支持方）获胜**

理由：正方提供了更具体的数据支撑和可执行的方案，而反方虽然提出了合理的风险顾虑但未给出具体的替代方案。

⚠️ Mock模式辩论 — 配置API Key获取真实Agent辩论。"""


def _aggregate_results(results: list[dict], mode: str) -> str:
    """Aggregate multi-agent results for the task summary."""
    mode_labels = {
        "pipeline": "🔗 流水线模式",
        "parallel": "⚡ 并行模式",
        "vote": "🗳️ 投票模式",
        "debate": "🏛️ 辩论模式",
    }
    label = mode_labels.get(mode, mode)

    parts = [f"# {label} — 任务执行总结\n"]
    parts.append(f"共 {len(results)} 个Agent参与，{sum(1 for r in results if r['status'] == 'completed')} 个成功完成\n")

    for i, r in enumerate(results, 1):
        status = "✅" if r["status"] == "completed" else "❌"
        name = r.get("agent_name", f"Agent #{i}")
        parts.append(f"\n## {name} {status}")
        parts.append(r.get("output", "")[:3000])

    return "\n".join(parts)
