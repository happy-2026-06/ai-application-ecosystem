"""Core function tests: prompt mode selection, chat service, script generation.

These tests verify the 视界短视频工坊 core pipeline:
- Mode guide selection (带货 / 测评 / 开箱)
- Prompt template rendering
- Chat endpoint integration
- SSE streaming integrity
"""
import json
import pytest


# ═══════════════════════════════════════════════════════════════════════
# Prompt mode selection tests
# ═══════════════════════════════════════════════════════════════════════

class TestModeGuideSelection:
    """Test that select_mode_guide picks the correct mode from user question."""

    def test_default_to_selling_mode(self):
        from app.rag.prompts import select_mode_guide, MODE_GUIDE_SELLING
        assert select_mode_guide("智能蓝牙耳机 带货") == MODE_GUIDE_SELLING
        assert select_mode_guide("帮我写个充电宝的脚本") == MODE_GUIDE_SELLING
        assert select_mode_guide("") == MODE_GUIDE_SELLING

    def test_review_keyword_detection(self):
        from app.rag.prompts import select_mode_guide, MODE_GUIDE_REVIEW
        assert select_mode_guide("测评对比蓝牙耳机") == MODE_GUIDE_REVIEW
        assert select_mode_guide("AirPods vs 华为 对比评测") == MODE_GUIDE_REVIEW
        assert select_mode_guide("做一个横评，对比三款耳机") == MODE_GUIDE_REVIEW
        assert select_mode_guide("评测 智能手表") == MODE_GUIDE_REVIEW

    def test_unboxing_keyword_detection(self):
        from app.rag.prompts import select_mode_guide, MODE_GUIDE_UNBOXING
        assert select_mode_guide("沉浸开箱 智能手表") == MODE_GUIDE_UNBOXING
        assert select_mode_guide("开箱体验 iPhone") == MODE_GUIDE_UNBOXING
        assert select_mode_guide("第一视角开箱") == MODE_GUIDE_UNBOXING

    def test_case_insensitive(self):
        from app.rag.prompts import select_mode_guide, MODE_GUIDE_REVIEW
        # Chinese doesn't have case, but we mix English keywords
        assert select_mode_guide("AirPods VS Huawei 测评") == MODE_GUIDE_REVIEW


class TestPromptTemplates:
    """Test that prompt templates contain required sections."""

    def test_video_director_prompt_has_sections(self):
        from app.rag.prompts import VIDEO_DIRECTOR_PROMPT
        assert "资深短视频导演" in VIDEO_DIRECTOR_PROMPT
        assert "{mode_guide}" in VIDEO_DIRECTOR_PROMPT
        assert "{context}" in VIDEO_DIRECTOR_PROMPT
        assert "{question}" in VIDEO_DIRECTOR_PROMPT
        assert "分镜表" in VIDEO_DIRECTOR_PROMPT
        assert "口播稿" in VIDEO_DIRECTOR_PROMPT
        assert "拍摄建议" in VIDEO_DIRECTOR_PROMPT

    def test_selling_mode_guide_has_required_parts(self):
        from app.rag.prompts import MODE_GUIDE_SELLING
        assert "黄金前3秒" in MODE_GUIDE_SELLING
        assert "价格锚点" in MODE_GUIDE_SELLING
        assert "行动号召" in MODE_GUIDE_SELLING
        assert "分镜表" in MODE_GUIDE_SELLING
        assert "口播稿" in MODE_GUIDE_SELLING

    def test_review_mode_guide_has_required_parts(self):
        from app.rag.prompts import MODE_GUIDE_REVIEW
        assert "先说结论" in MODE_GUIDE_REVIEW
        assert "实测数据" in MODE_GUIDE_REVIEW
        assert "购买建议" in MODE_GUIDE_REVIEW
        assert "适合谁" in MODE_GUIDE_REVIEW

    def test_unboxing_mode_guide_has_required_parts(self):
        from app.rag.prompts import MODE_GUIDE_UNBOXING
        assert "悬念开场" in MODE_GUIDE_UNBOXING
        assert "第一视角" in MODE_GUIDE_UNBOXING
        assert "惊喜" in MODE_GUIDE_UNBOXING
        assert "推荐" in MODE_GUIDE_UNBOXING


# ═══════════════════════════════════════════════════════════════════════
# Chat API integration tests
# ═══════════════════════════════════════════════════════════════════════

class TestChatAPI:
    """Test the chat endpoints (without LLM, using mock mode)."""

    @pytest.fixture(autouse=True)
    def enable_mock_llm(self, monkeypatch):
        """Force MOCK_LLM mode so tests don't call the real DeepSeek API."""
        monkeypatch.setenv("MOCK_LLM", "true")

    async def test_create_session(self, client, admin_headers):
        resp = await client.post("/api/chat/sessions", json={
            "title": "充电宝带货脚本"
        }, headers=admin_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "充电宝带货脚本"
        assert "id" in data

    async def test_list_sessions(self, client, admin_headers):
        # Create a session first
        await client.post("/api/chat/sessions", json={
            "title": "测试会话"
        }, headers=admin_headers)
        resp = await client.get("/api/chat/sessions", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_delete_session(self, client, admin_headers):
        resp = await client.post("/api/chat/sessions", json={
            "title": "待删除"
        }, headers=admin_headers)
        session_id = resp.json()["id"]
        resp2 = await client.delete(f"/api/chat/sessions/{session_id}", headers=admin_headers)
        assert resp2.status_code == 200

    async def test_ask_question_returns_sse(self, client, admin_headers):
        """Streaming SSE endpoint should return text/event-stream."""
        # Create a session
        resp = await client.post("/api/chat/sessions", json={
            "title": "耳机带货"
        }, headers=admin_headers)
        session_id = resp.json()["id"]

        # Send a question (MOCK_LLM mode will generate mock answer)
        resp2 = await client.post(
            f"/api/chat/ask?session_id={session_id}",
            json={"question": "产品: 蓝牙耳机\n核心卖点: 降噪40dB\n模板风格: 带货\n目标平台: 抖音"},
            headers=admin_headers,
        )
        assert resp2.status_code == 200
        assert "text/event-stream" in resp2.headers.get("content-type", "")

        # Collect SSE events
        body = resp2.text
        assert "data:" in body
        # Should have at least token events and a done event (or error)
        events = [line for line in body.split("\n") if line.startswith("data: ")]
        event_types = set()
        for e in events:
            try:
                obj = json.loads(e[6:])  # strip "data: " prefix
                if isinstance(obj, dict):
                    event_types.add(obj.get("type"))
            except (json.JSONDecodeError, IndexError):
                pass
        assert "done" in event_types or "error" in event_types

    async def test_ask_question_session_not_found(self, client, admin_headers):
        resp = await client.post(
            "/api/chat/ask?session_id=nonexistent-id",
            json={"question": "test"},
            headers=admin_headers,
        )
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════
# Simple retriever tests (dev-mode in-memory retrieval)
# ═══════════════════════════════════════════════════════════════════════

class TestSimpleRetriever:
    """Test the in-memory keyword retriever used in dev mode."""

    def test_load_documents_from_dir(self):
        import os
        from app.rag.simple_retriever import load_documents_from_dir, get_doc_count
        sample_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "sample-data"
        )
        count = load_documents_from_dir(sample_dir)
        assert count > 0, "Should load at least some chunks from sample-data"
        assert get_doc_count() == count

    async def test_simple_search_returns_results(self):
        import os
        from app.rag.simple_retriever import load_documents_from_dir, simple_search
        sample_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "sample-data"
        )
        load_documents_from_dir(sample_dir)
        results = await simple_search("分镜模板 带货", top_k=3)
        assert len(results) > 0, "Should find results for 分镜模板"
        assert all("content" in r for r in results)
        assert all("score" in r for r in results)

    async def test_simple_search_low_score_for_gibberish(self):
        from app.rag.simple_retriever import simple_search
        # With purely random input, results should have very low relevance scores
        results = await simple_search("zzzqqqxxx999abcdefg", top_k=5)
        # May still return results with minimal score due to char overlap
        # (digits appear in MD tables), but scores should be very low
        if results:
            for r in results:
                assert r.get("score", 0) < 0.3, f"Gibberish query got unexpectedly high score: {r['score']}"


# ═══════════════════════════════════════════════════════════════════════
# Health check test
# ═══════════════════════════════════════════════════════════════════════

class TestHealthCheck:
    async def test_root_endpoint(self, client):
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "视界短视频工坊"
        assert data["status"] == "running"

    async def test_health_endpoint(self, client):
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"
