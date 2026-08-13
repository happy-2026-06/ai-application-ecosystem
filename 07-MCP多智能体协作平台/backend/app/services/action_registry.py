"""Action registry for cross-project orchestration by 智能运营引擎(⑦).

Defines all external system actions that ⑦'s agents can invoke.
Each action specifies the target URL (using Docker network service names),
HTTP method, and expected input format.
"""

# Action registry — all actions that the orchestration engine can invoke
# URLs use Docker service names for inter-container communication
ACTIONS = {
    # ── 客服助手(①) actions ──
    "客服-搜索知识库": {
        "url": "http://p1-backend:8000/api/kb/search",
        "method": "POST",
        "description": "搜索客服FAQ知识库",
        "body_template": {"query": "{query}", "top_k": 5},
    },

    # ── 灵笔引擎(②) actions ──
    "灵笔-生成文案": {
        "url": "http://p2-backend:8000/api/chat/ask",
        "method": "POST",
        "description": "AI生成内容文案",
        "body_template": {"message": "{prompt}", "platform": "xiaohongshu"},
    },

    # ── 视界工坊(③) actions ──
    "视界-生成脚本": {
        "url": "http://p3-backend:8000/api/chat/ask",
        "method": "POST",
        "description": "AI生成短视频分镜脚本",
        "body_template": {"message": "{prompt}", "style": "带货"},
    },

    # ── 图库管家(④) actions ──
    "图库-搜索素材": {
        "url": "http://p4-backend:8000/api/assets/public/search",
        "method": "GET",
        "description": "搜索图库素材（无需认证）",
        "body_template": {"q": "{query}", "file_type": "image"},
    },

    # ── 话术教练(⑤) actions ──
    "话术-创建训练": {
        "url": "http://p5-backend:8000/api/training/sessions",
        "method": "POST",
        "description": "创建话术训练会话",
        "body_template": {"customer_type": "picky", "product_context": "{context}"},
    },

    # ── 数据中枢(⑥) actions ──
    "数据-查询数据集": {
        "url": "http://p6-backend:8000/api/data/datasets",
        "method": "GET",
        "description": "获取数据集列表",
    },
    "数据-接入数据": {
        "url": "http://p6-backend:8000/api/data/external/ingest",
        "method": "POST",
        "description": "从外部系统接入数据",
        "body_template": {"source_project": "运营引擎", "data_type": "orchestration_result", "texts": ["{result_text}"], "dataset_name": "运营引擎-编排结果"},
    },

    # ── 模型工厂(⑧) actions ──
    "模型-微调推理": {
        "url": "http://p8-backend:8000/api/finetune/models/{model_id}/proxy",
        "method": "POST",
        "description": "使用微调模型进行推理",
        "body_template": {"message": "{prompt}"},
    },
}


def get_action(name: str) -> dict | None:
    """Get an action definition by name."""
    return ACTIONS.get(name)


def get_all_actions() -> list[dict]:
    """Get all registered actions as a list."""
    return [
        {"name": name, "url": info["url"], "method": info["method"], "description": info["description"]}
        for name, info in ACTIONS.items()
    ]


# Dev-mode fallback: Docker service name → localhost host:port.
# Ports match docker-compose.yml host mappings (all backends use :8000
# inside the Docker network). Used when running locally without Docker —
# callers try the Docker service URL first, then the localhost fallback.
LOCALHOST_FALLBACKS: dict[str, str] = {
    "p1-backend": "localhost:8101",
    "p2-backend": "localhost:8202",
    "p3-backend": "localhost:8000",
    "p4-backend": "localhost:8400",
    "p5-backend": "localhost:8505",
    "p6-backend": "localhost:8606",
    "p8-backend": "localhost:8808",
}


def get_action_url_candidates(name: str) -> list[str]:
    """Candidate URLs for an action: the Docker service URL first, followed
    by localhost fallback URLs for local development (no Docker network)."""
    action = get_action(name)
    if not action:
        return []
    url = action["url"]
    candidates = [url]
    for host, local in LOCALHOST_FALLBACKS.items():
        if f"{host}:8000" in url:
            candidates.append(url.replace(f"{host}:8000", local))
    return candidates


def format_action_body(action_name: str, **params) -> dict:
    """Format an action's request body with the given parameters."""
    action = get_action(action_name)
    if not action or "body_template" not in action:
        return {}

    body = dict(action["body_template"])
    # Simple template substitution
    for key, value in body.items():
        if isinstance(value, str) and "{" in value:
            for param_key, param_val in params.items():
                value = value.replace(f"{{{param_key}}}", str(param_val))
            body[key] = value
    return body
