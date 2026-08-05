"""Chat service: orchestrates RAG pipeline with streaming SSE response."""
import asyncio
import os
import re
import time
import logging
from typing import AsyncGenerator

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.session import Session
from app.models.message import Message

logger = logging.getLogger(__name__)


async def stream_chat_response(
    db: AsyncSession,
    session: Session,
    user: User,
    question: str,
) -> AsyncGenerator[dict, None]:
    """Stream a RAG-enhanced chat response via SSE events.

    Events emitted:
        {"type": "thinking", "content": "..."}    - status messages
        {"type": "retrieving", "content": "..."}  - retrieval status
        {"type": "token", "content": "..."}       - streaming answer tokens
        {"type": "sources", "data": [...]}        - citation sources
        {"type": "done", "data": {...}}           - completion with metadata
        {"type": "error", "content": "..."}       - error message
    """
    start_time = time.time()

    try:
        # Step 1: Save user message
        user_msg = Message(
            session_id=session.id,
            user_id=user.id,
            role="user",
            content=question,
        )
        db.add(user_msg)
        await db.flush()

        # Step 2: Yield thinking status
        yield {"type": "thinking", "content": "正在分析问题..."}

        # Step 3: Query rewriting (optional, can be enabled)
        rewritten_query = question

        # Step 4: Retrieve relevant documents
        yield {"type": "retrieving", "content": "正在检索相关知识..."}

        retrieval_results = []
        try:
            from app.rag.retriever import retrieve_relevant_chunks
            retrieval_results = await retrieve_relevant_chunks(
                query=rewritten_query,
                top_k=5,
            )
        except Exception as e:
            logger.warning("Vector search unavailable: %s", e)

        # Fallback: use simple keyword search
        if not retrieval_results:
            try:
                from app.rag.simple_retriever import simple_search
                retrieval_results = await simple_search(query=rewritten_query, top_k=5)
                if retrieval_results:
                    logger.info("Using simple keyword search, found %d results", len(retrieval_results))
            except Exception as e2:
                logger.warning("Simple search also unavailable: %s", e2)

        # Step 5: Build prompt with context
        sources = []
        context_parts = []
        for i, result in enumerate(retrieval_results):
            source_ref = f"[来源:{i + 1}]"
            context_parts.append(
                f"{source_ref} 文档: {result.get('doc_name', '未知')}\n"
                f"内容: {result.get('content', '')}\n"
            )
            snippet = result.get("content", "")
            sources.append({
                "index": i + 1,
                "doc_name": result.get("doc_name", "未知"),
                "doc_id": result.get("doc_id"),
                "content_snippet": snippet[:200],
                "score": result.get("score"),
            })

        context = "\n---\n".join(context_parts)

        # Step 6: Yield sources to the client
        yield {"type": "sources", "data": sources}

        # Step 7: Stream LLM tokens
        raw_answer = ""

        # MOCK_LLM mode: fast path for stress tests
        if os.environ.get("MOCK_LLM", "").lower() == "true":
            raw_answer = _build_mock_answer(question, sources)
            for char in raw_answer:
                yield {"type": "token", "content": char}
                await asyncio.sleep(0.002)
        else:
            try:
                from app.rag.chain import get_rag_chain
                chain = get_rag_chain()

                async for chunk in chain.astream(
                    {"context": context, "question": question, "history": ""}
                ):
                    token_text = _extract_token_text(chunk)
                    if token_text:
                        raw_answer += token_text
                        yield {"type": "token", "content": token_text}
            except Exception as e:
                logger.warning("LLM unavailable, using dev mode fallback: %s", e)
                raw_answer = _build_fallback_answer(question, sources)
                for char in raw_answer:
                    yield {"type": "token", "content": char}

        # Step 8: Clean residual LangChain artifacts BEFORE saving to DB
        clean_answer = _clean_llm_output(raw_answer)

        # Step 9: Save assistant message with the CLEANED answer
        latency_ms = int((time.time() - start_time) * 1000)

        assistant_msg = Message(
            session_id=session.id,
            user_id=user.id,
            role="assistant",
            content=clean_answer,
            citations=sources,
            latency_ms=latency_ms,
        )
        db.add(assistant_msg)

        # Use actual message count from database, not a hardcoded +2
        count_result = await db.execute(
            select(func.count()).select_from(Message).where(
                Message.session_id == session.id
            )
        )
        session.message_count = count_result.scalar() or 0
        await db.flush()

        # Step 10: Yield completion with the CLEAN answer
        yield {
            "type": "done",
            "data": {
                "message_id": str(assistant_msg.id),
                "full_answer": clean_answer,
                "sources": sources,
                "latency_ms": latency_ms,
            },
        }

    except Exception as e:
        logger.exception("Chat streaming error for session %s: %s", session.id, e)
        yield {
            "type": "error",
            "content": "处理问题时出错，请重试",
        }


# ── Private helpers ──────────────────────────────────────────────────

def _extract_token_text(chunk) -> str:
    """Extract text content from a LangChain AIMessageChunk object.

    Handles: str content, list[dict] multi-modal content, and raw strings.
    """
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


def _clean_llm_output(text: str) -> str:
    """Remove LangChain internal artifacts from streaming output.

    These patterns clean up AIMessageChunk repr fragments that may leak
    into the concatenated output when the streaming parser encounters
    edge cases in LangChain's internal chunk formatting.
    """
    # Remove AIMessageChunk repr fragments
    text = re.sub(
        r"content=''.*?additional_kwargs=\{[^}]*\}.*?(?=content=''|$)",
        "", text, flags=re.DOTALL,
    )
    text = re.sub(
        r"response_metadata=\{[^}]*\}", "", text,
    )
    text = re.sub(
        r"id='lc_run--[a-f0-9-]+'", "", text,
    )
    text = re.sub(
        r"tool_calls=\[\] invalid_tool_calls=\[\] tool_call_chunks=\[\]", "", text,
    )
    # Collapse excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _build_mock_answer(question: str, sources: list[dict]) -> str:
    """Build a mock answer for stress testing (no API call)."""
    parts = [
        f"根据知识库检索结果，我为您找到以下相关信息：\n",
        f"\n您问的是「{question}」。经过分析，知识库中有 {len(sources)} 条相关文档片段。\n",
    ]
    for s in sources[:3]:
        parts.append(f"- {s['doc_name']}：{s['content_snippet'][:80]}...\n")
    parts.append(
        f"\n综合以上信息，建议您根据具体需求选择合适的产品。\n"
        f"\n💡 提示：这是 MOCK_LLM 模式回复（压测用），真实场景会由 DeepSeek AI 生成更详细的回答。"
    )
    return "".join(parts)


def _build_fallback_answer(question: str, sources: list[dict]) -> str:
    """Build a dev-mode fallback answer when LLM is unavailable."""
    return (
        f"👋 你好！这是开发模式回复。\n\n"
        f"你的问题是：{question}\n\n"
        f"⚠️ 当前 LLM 服务未配置，请设置 DEEPSEEK_API_KEY 环境变量来启用 AI 回答。\n\n"
        f"检索到 {len(sources)} 条相关文档片段（知识库可能为空）。"
    )
