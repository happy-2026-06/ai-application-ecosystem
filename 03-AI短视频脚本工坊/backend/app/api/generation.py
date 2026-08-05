"""Generation API routes: TTS, video, subtitles, and CapCut draft export.

Mounts at /api/generation/
"""
import json
import logging
import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.models.session import Session
from app.models.message import Message
from app.core.auth import get_current_user
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Assets helpers ────────────────────────────────────────────────────────

def _append_asset(msg: Message, asset_type: str, max_per_type: int = 3, **fields) -> None:
    """Append an asset entry to a message, deduplicating by type.

    Keeps at most max_per_type entries per type (most recent wins).
    """
    if not hasattr(msg, 'assets'):
        return
    assets: list = list(msg.assets or [])
    # Remove oldest entries of this type if over the limit
    same_type = [a for a in assets if a.get("type") == asset_type]
    if len(same_type) >= max_per_type:
        # Drop the oldest entries, keep only (max_per_type - 1)
        oldest = same_type[:len(same_type) - max_per_type + 1]
        for old in oldest:
            assets.remove(old)
    assets.append({"type": asset_type, "created_at": datetime.now(timezone.utc).isoformat(), **fields})
    msg.assets = assets


# ══════════════════════════════════════════════════════════════════════════
# Request schemas
# ══════════════════════════════════════════════════════════════════════════

class TTSRequest(BaseModel):
    """Request to generate voiceover audio."""
    session_id: str = Field(..., description="Session whose last script will be voiced")
    voice: str = Field(default="zh-CN-XiaoxiaoNeural", description="Edge-TTS voice ID")
    speed: str = Field(default="+0%", description="Speed modifier, e.g. '+10%' or '-5%'")
    message_id: str | None = Field(None, description="Specific message to voice (default: latest)")


class TTSResponse(BaseModel):
    """TTS generation result."""
    file_url: str
    filename: str
    voice: str
    duration_chars: int
    total_duration_sec: float = 0
    shot_count: int = 0
    mode: str = "legacy"  # "per_shot" or "legacy"


class VideoRequest(BaseModel):
    """Request to generate AI video from shot descriptions."""
    session_id: str = Field(..., description="Session whose script provides shot descriptions")
    message_id: str | None = Field(None, description="Specific message (default: latest)")
    model: str = Field(default="cogvideox-2", description="Video generation model")
    shot_indexes: list[int] | None = Field(None, description="Which shots to generate (default: all)")


class VideoStatusResponse(BaseModel):
    """Video generation task status."""
    task_id: str
    status: str
    video_url: str | None = None
    error: str | None = None


class SubtitleRequest(BaseModel):
    """Request to export subtitles."""
    session_id: str = Field(..., description="Session whose script provides the shot table")
    message_id: str | None = Field(None, description="Specific message (default: latest)")
    format: str = Field(default="srt", pattern="^(srt|ass)$", description="Subtitle format")
    words_per_second: float = Field(default=3.5, ge=1.0, le=10.0, description="Speaking rate")


class SubtitleResponse(BaseModel):
    """Subtitle export result."""
    file_url: str
    filename: str
    format: str
    entry_count: int
    preview: str = ""  # first 2000 chars for in-browser preview
    audio_aligned: bool = False  # True if timestamps use per-shot real audio durations
    total_duration_sec: float = 0  # total subtitle duration in seconds
    alignment_mode: str = "estimated"  # "per_shot" | "scaled" | "estimated"


class CapCutDraftRequest(BaseModel):
    """Request to generate a CapCut draft."""
    session_id: str = Field(..., description="Session whose script will be converted")
    message_id: str | None = Field(None, description="Specific message (default: latest)")
    title: str = Field(default="AI生成视频", max_length=80, description="Project name in CapCut")
    include_tts_audio: bool = Field(default=False, description="Include TTS audio track if available")
    include_subtitles: bool = Field(default=True, description="Include subtitles in the draft")


class CapCutDraftResponse(BaseModel):
    """CapCut draft generation result."""
    draft_name: str
    shot_count: int
    has_audio: bool
    has_subtitles: bool
    message: str


# ══════════════════════════════════════════════════════════════════════════
# Helper: get the latest assistant message from a session
# ══════════════════════════════════════════════════════════════════════════

async def _get_latest_assistant_message(
    db: AsyncSession,
    session_id: str,
    user_id: str,
    message_id: str | None = None,
) -> Message:
    """Fetch the latest (or specified) assistant message, verifying ownership."""
    # Verify session ownership
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == user_id,
        )
    )
    chat_session = result.scalar_one_or_none()
    if not chat_session:
        raise HTTPException(status_code=404, detail="会话不存在")

    if message_id:
        result = await db.execute(
            select(Message).where(Message.id == message_id, Message.session_id == session_id)
        )
        msg = result.scalar_one_or_none()
        if not msg:
            raise HTTPException(status_code=404, detail="消息不存在")
    else:
        # Get the latest assistant message
        result = await db.execute(
            select(Message)
            .where(Message.session_id == session_id, Message.role == "assistant")
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        msg = result.scalar_one_or_none()

    if not msg:
        raise HTTPException(status_code=404, detail="该会话暂无AI生成内容，请先生成脚本")

    return msg


# ══════════════════════════════════════════════════════════════════════════
# TTS endpoints
# ══════════════════════════════════════════════════════════════════════════

@router.get("/tts/voices")
async def list_tts_voices(language: str = Query("zh", description="zh / mandarin / cantonese / taiwanese")):
    """List available Chinese TTS voices."""
    from app.services.tts_service import list_voices
    voices = list_voices(language)
    return {"voices": voices, "count": len(voices)}


@router.post("/tts", response_model=TTSResponse)
async def generate_tts_audio(
    request: TTSRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate MP3 voiceover from the session's latest AI script.

    Uses per-shot mode when the script contains a parsable shot table:
    each shot's voiceover text is synthesized individually, then merged.
    This captures the real duration of each shot so subtitles can be
    aligned precisely afterwards.

    Falls back to legacy mode (full-script TTS) when no shot table is found.
    """
    msg = await _get_latest_assistant_message(db, request.session_id, current_user.id, request.message_id)

    from app.services.tts_service import (
        extract_voiceover_text,
        generate_tts,
        generate_tts_per_shot,
        get_voice_by_id,
    )
    from app.services.subtitle_service import parse_shot_table

    voice = request.voice or settings.TTS_DEFAULT_VOICE
    speed = request.speed or settings.TTS_DEFAULT_SPEED
    voice_info = get_voice_by_id(voice)
    voice_name = voice_info["name"] if voice_info else voice

    # Try per-shot mode first
    shots = parse_shot_table(msg.content)
    shot_dicts = [
        {"index": s.index, "voiceover_text": s.voiceover_text}
        for s in shots if s.voiceover_text.strip()
    ]

    if len(shot_dicts) >= 1:
        # ── PER-SHOT MODE ────────────────────────────────────────────
        try:
            result = await generate_tts_per_shot(
                shots=shot_dicts,
                voice=voice,
                speed=speed,
            )
        except RuntimeError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"TTS生成失败: {str(e)}")

        output_path = result["merged_path"]
        filename = result["filename"]

        # Store per-shot timing data + asset reference in message
        _append_asset(msg, "tts",
            filename=filename,
            voice=voice_name,
            mode="per_shot",
            duration_sec=round(result["total_duration_sec"], 1),
            shot_durations=result["shot_durations"],  # <-- KEY: per-shot audio durations
        )
        await db.flush()

        return TTSResponse(
            file_url=f"/api/generation/tts/download/{filename}",
            filename=filename,
            voice=f"{voice} ({voice_name})",
            duration_chars=sum(len(s["text"]) for s in result["shot_durations"]),
            total_duration_sec=round(result["total_duration_sec"], 1),
            shot_count=len(result["shot_durations"]),
            mode="per_shot",
        )
    else:
        # ── LEGACY MODE (fallback) ───────────────────────────────────
        voiceover_text = extract_voiceover_text(msg.content)
        if not voiceover_text or len(voiceover_text.strip()) < 2:
            raise HTTPException(status_code=400, detail="未找到口播文案，请确保脚本包含口播稿内容")

        try:
            output_path = await generate_tts(text=voiceover_text, voice=voice, speed=speed)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"TTS生成失败: {str(e)}")

        filename = os.path.basename(output_path)
        from app.services.tts_service import get_audio_duration
        audio_duration = get_audio_duration(output_path)

        _append_asset(msg, "tts",
            filename=filename,
            voice=voice_name,
            mode="legacy",
            duration_sec=round(audio_duration, 1) if audio_duration else None,
        )
        await db.flush()

        return TTSResponse(
            file_url=f"/api/generation/tts/download/{filename}",
            filename=filename,
            voice=f"{voice} ({voice_name})",
            duration_chars=len(voiceover_text),
            total_duration_sec=round(audio_duration, 1) if audio_duration else 0,
            shot_count=0,
            mode="legacy",
        )


@router.get("/tts/download/{filename}")
async def download_tts(filename: str):
    """Download a generated TTS audio file."""
    filepath = os.path.join(settings.TTS_OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在或已过期")
    return FileResponse(
        filepath,
        media_type="audio/mpeg",
        filename=filename,
    )


# ══════════════════════════════════════════════════════════════════════════
# Video generation endpoints
# ══════════════════════════════════════════════════════════════════════════

@router.post("/video")
async def submit_video_generation(
    request: VideoRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit AI video generation tasks based on the session's script shots."""
    if not settings.ZHIPU_API_KEY:
        raise HTTPException(status_code=503, detail="视频生成服务未配置（需设置 ZHIPU_API_KEY）")

    msg = await _get_latest_assistant_message(db, request.session_id, current_user.id, request.message_id)

    # Parse shots from the script
    from app.services.subtitle_service import parse_shot_table

    shots = parse_shot_table(msg.content)
    if not shots:
        raise HTTPException(status_code=400, detail="未找到分镜表，请确保脚本包含 Markdown 表格")

    # Filter by requested shot indexes
    if request.shot_indexes:
        shots = [s for s in shots if s.index in request.shot_indexes]
        if not shots:
            raise HTTPException(status_code=400, detail="指定的镜号不存在")

    # Submit video generation tasks
    from app.services.video_service import generate_videos_for_shots

    shot_dicts = [
        {
            "index": s.index,
            "visual_content": s.visual_content,
            "voiceover_text": s.voiceover_text,
        }
        for s in shots
    ]

    results = await generate_videos_for_shots(
        shots=shot_dicts,
        model=request.model or settings.ZHIPU_VIDEO_MODEL,
        concurrent=2,
    )

    # Store task IDs in message assets
    for r in results:
        if r.get("task_id"):
            _append_asset(msg, "video",
                task_id=r["task_id"],
                index=r.get("index"),
                status="submitted",
            )
    await db.flush()

    return {"tasks": results, "count": len(results)}


@router.get("/video/{task_id}", response_model=VideoStatusResponse)
async def get_video_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    """Query the status of a video generation task."""
    if not settings.ZHIPU_API_KEY:
        raise HTTPException(status_code=503, detail="视频生成服务未配置")

    from app.services.video_service import query_video_status

    try:
        result = await query_video_status(task_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

    return VideoStatusResponse(**result)


# ══════════════════════════════════════════════════════════════════════════
# Subtitle endpoints
# ══════════════════════════════════════════════════════════════════════════

@router.post("/subtitles", response_model=SubtitleResponse)
async def export_subtitles(
    request: SubtitleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export SRT or ASS subtitles from the session's AI script shot table."""
    msg = await _get_latest_assistant_message(db, request.session_id, current_user.id, request.message_id)

    from app.services.subtitle_service import (
        parse_shot_table,
        generate_srt,
        generate_ass,
        export_subtitle_file,
    )

    shots = parse_shot_table(msg.content)
    if not shots:
        raise HTTPException(status_code=400, detail="未找到分镜表，请确保脚本包含 Markdown 表格")

    wps = request.words_per_second or settings.SUBTITLE_DEFAULT_WPS

    # ── Auto-align with TTS per-shot audio if available ───────────────
    audio_duration = None
    shot_durations = None  # per-shot real audio durations (precise mode)
    alignment_mode = "estimated"  # "per_shot" | "scaled" | "estimated"

    if hasattr(msg, 'assets') and msg.assets:
        for asset in reversed(msg.assets or []):
            if asset.get("type") == "tts":
                # Check for per-shot mode (PRECISE alignment)
                if asset.get("mode") == "per_shot" and asset.get("shot_durations"):
                    shot_durations = [
                        sd["duration_sec"] for sd in asset["shot_durations"]
                    ]
                    audio_duration = float(asset.get("duration_sec", 0))
                    alignment_mode = "per_shot"
                    logger.info("Subtitle: found per-shot TTS data → PRECISE alignment (%d shots)", len(shot_durations))
                    break
                # Legacy mode fallback: total duration only (SCALED alignment)
                elif asset.get("duration_sec"):
                    audio_duration = float(asset["duration_sec"])
                    alignment_mode = "scaled"
                    logger.info("Subtitle: found legacy TTS audio → SCALED alignment (%.1fs)", audio_duration)
                    break

    if request.format == "srt":
        content = generate_srt(
            shots,
            words_per_second=wps,
            target_duration_sec=audio_duration if shot_durations is None else None,
            shot_durations=shot_durations,
        )
    else:
        title = f"AI生成字幕"
        content = generate_ass(
            shots,
            title=title,
            words_per_second=wps,
            target_duration_sec=audio_duration if shot_durations is None else None,
            shot_durations=shot_durations,
        )

    filepath = export_subtitle_file(content, format=request.format)
    filename = os.path.basename(filepath)

    # Store asset reference
    _append_asset(msg, "subtitles",
        filename=filename,
        format=request.format,
        entry_count=len(shots),
    )
    await db.flush()

    return SubtitleResponse(
        file_url=f"/api/generation/subtitles/download/{filename}",
        filename=filename,
        format=request.format,
        entry_count=len(shots),
        preview=content[:2000],
        audio_aligned=alignment_mode == "per_shot",  # only "per_shot" is truly aligned
        total_duration_sec=round(audio_duration or 0, 1),
        alignment_mode=alignment_mode,
    )


@router.get("/subtitles/download/{filename}")
async def download_subtitles(filename: str):
    """Download a generated subtitle file."""
    filepath = os.path.join(settings.SUBTITLE_OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在或已过期")
    return FileResponse(
        filepath,
        media_type="text/plain; charset=utf-8",
        filename=filename,
    )


# ══════════════════════════════════════════════════════════════════════════
# CapCut draft endpoints
# ══════════════════════════════════════════════════════════════════════════

@router.post("/capcut-draft", deprecated=True)
async def generate_capcut_draft(
    request: CapCutDraftRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """[已废弃] 剪映 11.x 采用加密二进制草稿格式，pycapcut 无法兼容。

    请引导用户手动操作：下载 MP3 + SRT → 拖入剪映。
    详见前端「📖 使用指南」弹窗。
    """
    msg = await _get_latest_assistant_message(db, request.session_id, current_user.id, request.message_id)

    # Find TTS audio if requested
    audio_path = None
    if request.include_tts_audio and hasattr(msg, 'assets') and msg.assets:
        for asset in reversed(msg.assets or []):
            if asset.get("type") == "tts" and asset.get("filename"):
                candidate = os.path.join(settings.TTS_OUTPUT_DIR, asset["filename"])
                if os.path.exists(candidate):
                    audio_path = candidate
                    break

    # Find SRT subtitle file if requested
    srt_path = None
    if request.include_subtitles and hasattr(msg, 'assets') and msg.assets:
        for asset in reversed(msg.assets or []):
            if asset.get("type") == "subtitles" and asset.get("filename"):
                candidate = os.path.join(settings.SUBTITLE_OUTPUT_DIR, asset["filename"])
                if os.path.exists(candidate):
                    srt_path = candidate
                    break

    from app.services.capcut_service import import_to_capcut

    try:
        result = import_to_capcut(
            script_content=msg.content,
            title=request.title or "AI生成视频",
            audio_path=audio_path,
            srt_path=srt_path,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"剪映导入失败: {str(e)}")

    # Store asset reference
    _append_asset(msg, "capcut",
        draft_name=result["draft_name"],
        title=request.title,
        shot_count=result["shot_count"],
        has_audio=result["has_audio"],
        has_subtitles=result["has_subtitles"],
    )
    await db.flush()

    return CapCutDraftResponse(**result)


@router.get("/capcut-draft/download/{folder_name}")
async def download_capcut_draft(folder_name: str):
    """[已废弃] 新版本已直接将草稿写入剪映目录，无需下载。"""
    raise HTTPException(status_code=410, detail="此接口已废弃，新版本直接导入剪映，无需下载")
