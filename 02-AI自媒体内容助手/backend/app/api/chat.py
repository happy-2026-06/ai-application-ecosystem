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
        await db.flush()

    async def generate_sse():
        from app.services.chat_service import stream_chat_response
        async for event in stream_chat_response(
            db=db,
            session=chat_session,
            user=current_user,
            question=request.question,
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

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


