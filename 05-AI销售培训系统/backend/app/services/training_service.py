"""Training service: role-play engine with LLM scoring and coaching."""
import asyncio
import json
import logging
import re
import time
from typing import AsyncGenerator

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.training import TrainingSession, TrainingRound
from app.config import settings

logger = logging.getLogger(__name__)

# ── Customer type definitions ──────────────────────────────────────

CUSTOMER_TYPES = {
    "picky": {
        "name": "挑剔型",
        "icon": "🧐",
        "difficulty": 3,
        "persona": "质疑一切、吹毛求疵、反复比较竞品",
        "opening": "你们这个产品也太贵了吧？我朋友在别家买的才一半的价格。你说说，凭什么这么贵？",
    },
    "price": {
        "name": "价格敏感型",
        "icon": "💰",
        "difficulty": 2,
        "persona": "对价格极度敏感、反复砍价、犹豫不决",
        "opening": "你好，这款产品能不能便宜点？我预算有限，如果价格合适我就考虑。",
    },
    "hesitant": {
        "name": "犹豫型",
        "icon": "🤔",
        "difficulty": 4,
        "persona": "摇摆不定、需要反复确认细节、容易流失",
        "opening": "产品看着挺好的，但我不着急买，想再看看别家的对比一下。",
    },
    "expert": {
        "name": "专业型",
        "icon": "🎓",
        "difficulty": 5,
        "persona": "了解行业、问专业问题、质疑数据不实",
        "opening": "我看到你们的参数写着续航30小时，但行业标准测试条件下同类产品最多20小时，你们是怎么测出来的？",
    },
}

# ── Scoring dimensions ─────────────────────────────────────────────

SCORE_DIMENSIONS = [
    {"key": "fluency", "label": "流畅度", "icon": "🗣️", "max": 100},
    {"key": "persuasiveness", "label": "说服力", "icon": "💪", "max": 100},
    {"key": "knowledge", "label": "产品知识", "icon": "📚", "max": 100},
    {"key": "objection", "label": "异议处理", "icon": "🛡️", "max": 100},
    {"key": "emotion", "label": "情绪控制", "icon": "😌", "max": 100},
]


def build_training_prompt(
    customer_type: str,
    product_context: str | None,
    history: str,
    user_response: str,
    round_number: int,
) -> str:
    """Build the training coach prompt with full context."""
    ctype = CUSTOMER_TYPES.get(customer_type, CUSTOMER_TYPES["picky"])

    prompt = f"""你是一个专业的**AI话术教练教练**。你的任务是扮演客户角色，与销售人员进行多轮角色扮演对练，并给出实时评分和改进建议。

## 🎭 当前角色设定
- **客户类型**：{ctype['name']}（{ctype['persona']}）
- **难度等级**：{'⭐' * ctype['difficulty']}
- **当前轮次**：第 {round_number} 轮
"""
    if product_context:
        prompt += f"- **产品背景**：{product_context}\n"

    prompt += f"""
## 📝 对话历史
{history if history else "（第一轮对话，没有历史记录）"}

## 🗣️ 销售人员最新回应
"{user_response}"

## 📋 你的任务

请以两个角色同时回复，格式如下：

**👤 客户**：[以客户身份说的一句话，语气和态度要符合客户类型设定。如果销售说得好可以略微松动，说得差就更加刁难。保持真实自然。]

**💡 教练提示**：[如果销售的回应有明显的改进空间，给出一条具体建议。如果没有明显问题，写"回应不错，继续保持！"]

**📊 评分**：
- 流畅度: XX
- 说服力: XX
- 产品知识: XX
- 异议处理: XX
- 情绪控制: XX

评分规则：
- 每个维度 0-100 分
- 流畅度：表达是否自然流畅，无背诵痕迹
- 说服力：逻辑是否清晰，是否切中客户痛点
- 产品知识：对产品的了解程度，能否准确回答专业问题
- 异议处理：面对客户质疑时的应对能力和转化技巧
- 情绪控制：面对刁难客户时能否保持冷静专业

只返回上述格式的内容，不要多余的解释。"""
    return prompt


def parse_ai_response(raw_text: str) -> dict:
    """Parse the structured AI response into components."""
    result = {
        "customer_response": "嗯，你继续说。",
        "coach_hint": None,
        "scores": None,
    }

    # Extract customer response
    customer_match = re.search(r'\*\*👤\s*客户\*\*[：:]\s*(.+?)(?=\n\*\*💡|\n\*\*📊|\Z)', raw_text, re.DOTALL)
    if customer_match:
        result["customer_response"] = customer_match.group(1).strip()

    # Extract coach hint
    hint_match = re.search(r'\*\*💡\s*教练提示\*\*[：:]\s*(.+?)(?=\n\*\*📊|\Z)', raw_text, re.DOTALL)
    if hint_match:
        result["coach_hint"] = hint_match.group(1).strip()

    # Extract scores
    scores = {}
    for dim in SCORE_DIMENSIONS:
        key = dim["key"]
        label = dim["label"]
        score_match = re.search(rf'{label}[：:]\s*(\d+)', raw_text)
        if score_match:
            try:
                scores[key] = min(100, max(0, int(score_match.group(1))))
            except ValueError:
                scores[key] = 50
        else:
            scores[key] = 50

    if scores:
        result["scores"] = scores

    return result


def build_training_report_prompt(history_text: str, final_scores: dict) -> str:
    """Build prompt for final training report generation."""
    return f"""你是一个专业的AI话术教练教练。请根据以下训练记录生成总结报告。

## 训练记录
{history_text}

## 最终各维度平均分
{json.dumps(final_scores, ensure_ascii=False, indent=2)}

## 报告格式
请按以下格式输出：

**📊 综合评分**：XX 分
**💪 优势**：
- [列出2-3个表现优秀的方面]
**🔧 待改进**：
- [列出2-3个需要加强的方面]
**📈 训练建议**：
[给出后续练习方向和具体建议，50字以内]
"""
