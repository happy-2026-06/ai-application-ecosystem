"""Intent router — matches user questions to business domains for fine-tuned model routing.

Uses keyword matching against training domains. Zero-cost routing, no LLM call needed.
"""
import re
import logging

logger = logging.getLogger(__name__)

# Domain keyword maps — covers common ecommerce customer service categories
DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "退货退款": [
        "退货", "退款", "退换", "退换货", "寄回", "运费险", "退款流程",
        "收到退款", "退款到账", "拒收", "换货", "退差价",
    ],
    "促销活动": [
        "优惠", "满减", "秒杀", "折扣", "活动", "优惠券", "红包",
        "促销", "限时", "特价", "拼团", "砍价", "新人专享",
    ],
    "产品参数": [
        "规格", "参数", "尺寸", "配置", "型号", "颜色", "材质",
        "重量", "容量", "功率", "电压", "兼容", "接口",
    ],
    "物流配送": [
        "发货", "快递", "物流", "配送", "到货", "签收", "包裹",
        "运输", "送达", "自提", "配送范围", "运费", "包邮",
    ],
    "售后服务": [
        "售后", "保修", "维修", "投诉", "客服", "工单", "投诉电话",
        "质量问题", "坏了", "不能用", "故障", "破损", "损坏",
    ],
    "订单管理": [
        "订单", "下单", "取消订单", "修改订单", "订单状态", "订单号",
        "查订单", "我的订单", "待付款", "待发货", "已发货", "已完成",
    ],
    "账户问题": [
        "账号", "密码", "登录", "注册", "绑定", "修改密码", "注销",
        "手机号", "验证码", "实名", "安全", "隐私",
    ],
    "支付问题": [
        "支付", "付款", "微信支付", "支付宝", "银行卡", "分期",
        "花呗", "白条", "余额", "扣款", "支付失败", "重复扣款",
    ],
}


def match_intent(question: str, training_domains: list[str] | None = None) -> dict:
    """Match a user question to the best-fitting business domain.

    Args:
        question: The user's question text.
        training_domains: Optional list of domains this model was trained on.
                          If provided, only matches against known domains.

    Returns:
        dict with keys: domain (str), confidence (float 0-1), matched_keywords (list[str])
    """
    if not question or not question.strip():
        return {"domain": "通用咨询", "confidence": 0.0, "matched_keywords": []}

    question_lower = question.lower().strip()

    # Filter to training domains only if provided
    available_domains = DOMAIN_KEYWORDS
    if training_domains:
        available_domains = {
            k: v for k, v in DOMAIN_KEYWORDS.items()
            if k in training_domains or any(
                td in k or k in td for td in training_domains
            )
        }
        if not available_domains:
            available_domains = DOMAIN_KEYWORDS  # fallback to all

    # Score each domain by keyword matches
    scores: dict[str, tuple[int, list[str]]] = {}
    for domain, keywords in available_domains.items():
        matched = [kw for kw in keywords if kw in question_lower]
        if matched:
            scores[domain] = (len(matched), matched)

    if not scores:
        return {"domain": "通用咨询", "confidence": 0.0, "matched_keywords": []}

    # Pick the domain with the most keyword matches
    best_domain = max(scores, key=lambda d: scores[d][0])
    match_count, matched_keywords = scores[best_domain]

    # Confidence: ratio of matched keywords to total keywords for that domain
    total_keywords = len(available_domains[best_domain])
    confidence = min(1.0, match_count / max(total_keywords * 0.1, 1))

    logger.debug(
        "Intent routed: '%s' -> %s (confidence=%.2f, keywords=%s)",
        question[:60], best_domain, confidence, matched_keywords,
    )

    return {
        "domain": best_domain,
        "confidence": round(confidence, 2),
        "matched_keywords": matched_keywords,
    }


def build_domain_prompt(intent: dict, model_name: str) -> str:
    """Build a domain-specific system prompt based on the matched intent.

    Args:
        intent: The intent dict from match_intent().
        model_name: Name of the fine-tuned model.

    Returns:
        A complete system prompt string.
    """
    domain = intent.get("domain", "通用咨询")
    confidence = intent.get("confidence", 0.0)

    base = f"你是「{model_name}」，一个经过{domain}领域专项数据微调的电商AI助手。"

    domain_instructions = {
        "退货退款": (
            "你需要严格基于已学习的退货退款政策来回答。"
            "确保引用具体的退货条件（7天/15天）、退款时间线（1-7工作日）、"
            "运费承担规则等信息。语气要有同理心，理解客户的不便。"
        ),
        "促销活动": (
            "你需要准确告知当前的优惠活动规则、适用范围、叠加条件。"
            "如果训练数据中没有相关活动信息，诚实地告知客户。"
            "主动推荐最适合客户的优惠组合。"
        ),
        "产品参数": (
            "你需要准确、详细地提供产品规格参数。"
            "使用对比表格或列表展示多产品参数，方便客户比较。"
            "对于不确定的参数，建议客户查看商品详情页。"
        ),
        "物流配送": (
            "你需要告知配送范围、时效、运费标准。"
            "提供多个配送选项（标准/加急/自提）。"
            "如遇延迟，主动致歉并解释原因。"
        ),
        "售后服务": (
            "你需要展现同理心和解决问题的决心。"
            "明确告知保修期限、维修流程、客服联系方式。"
            "对于质量问题，优先安抚情绪再给出解决方案。"
        ),
        "订单管理": (
            "你需要清晰告知订单状态查询方法、修改/取消条件。"
            "引导客户提供订单号以便精准查询。"
            "对于无法自助操作的，主动建议转人工。"
        ),
        "账户问题": (
            "你需要引导客户完成账户相关操作。"
            "涉及密码/安全等敏感操作，提示安全注意事项。"
            "对于复杂问题建议转人工客服。"
        ),
        "支付问题": (
            "你需要解释支付方式、分期规则、扣款逻辑。"
            "对于支付失败，给出可能的原因和解决方案。"
            "涉及资金安全时格外谨慎，引导走官方渠道。"
        ),
        "通用咨询": (
            "你需要根据已学习的训练数据，给出专业、准确的回答。"
            "如果训练数据中没有相关信息，诚实告知并建议其他途径。"
        ),
    }

    instruction = domain_instructions.get(domain, domain_instructions["通用咨询"])

    prompt = f"""{base}

## 当前业务领域: {domain}
{instruction}

## 回答要求
1. 基于训练数据中的知识来回答，体现微调模型的专业性
2. 使用"亲"、"您好"等亲切称谓
3. 结构清晰，可适当使用列表/表格
4. 训练数据中没有的信息不要编造，建议客户通过其他途径获取"""

    return prompt
