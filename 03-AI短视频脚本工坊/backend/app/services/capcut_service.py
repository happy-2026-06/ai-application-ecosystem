"""CapCut (剪映) draft generator — ⚠️ DEPRECATED since v2.1.

剪映 11.x switched to encrypted binary draft format, making pycapcut incompatible.
The `/api/generation/capcut-draft` endpoint is marked deprecated and returns 410 Gone.

Users should instead: download MP3 + SRT → drag into 剪映 manually.
See the frontend "📖 使用指南" modal for the current workflow.

This module is kept for reference only and will be removed in v3.0.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 剪映默认草稿目录
_CAPCUT_DRAFT_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "JianyingPro", "User Data", "Projects", "com.liveditor.draft",
)

# Default canvas: 1080×1920 (竖屏短视频)
DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 1920
DEFAULT_FPS = 30


def _find_draft_dir() -> str:
    """Locate 剪映's actual draft folder, creating it if needed."""
    if os.path.isdir(_CAPCUT_DRAFT_DIR):
        return _CAPCUT_DRAFT_DIR

    # Try alternative paths
    alt = os.path.join(
        os.environ.get("LOCALAPPDATA", ""),
        "JianyingPro", "User Data", "Projects", "com.lveditor.draft",
    )
    if os.path.isdir(alt):
        return alt

    # Neither exists — create the standard one
    os.makedirs(_CAPCUT_DRAFT_DIR, exist_ok=True)
    logger.info("Created CapCut draft directory: %s", _CAPCUT_DRAFT_DIR)
    return _CAPCUT_DRAFT_DIR


# ══════════════════════════════════════════════════════════════════════════════
# Shot extraction from Markdown (delegates to subtitle_service for unified parsing + filtering)
# ══════════════════════════════════════════════════════════════════════════════

def _extract_shots(markdown: str) -> list[dict]:
    """Parse the Markdown shot table into a list of {index, visual, voiceover, duration_sec}.

    Uses subtitle_service.parse_shot_table() for unified parsing, which applies
    _clean_voiceover_text() to filter out director notes / stage directions.
    """
    from app.services.subtitle_service import parse_shot_table

    shot_infos = parse_shot_table(markdown)
    return [
        {
            "index": s.index,
            "visual_content": s.visual_content,
            "voiceover_text": s.voiceover_text,  # already filtered by _clean_voiceover_text
            "duration_sec": s.duration_sec,
        }
        for s in shot_infos
    ]


# ══════════════════════════════════════════════════════════════════════════════
# Main: build and import into CapCut
# ══════════════════════════════════════════════════════════════════════════════

def import_to_capcut(
    script_content: str,
    title: str = "AI生成视频",
    audio_path: Optional[str] = None,
    srt_path: Optional[str] = None,
    draft_dir: Optional[str] = None,
) -> dict:
    """Build a CapCut draft from AI script and import it directly into 剪映.

    The draft appears immediately in 剪映's draft list — no ZIP download needed.

    Args:
        script_content: The full AI-generated Markdown script.
        title: Project name shown in CapCut.
        audio_path: Optional path to TTS audio (MP3) for voiceover track.
        srt_path: Optional path to SRT subtitle file.
        draft_dir: Override default CapCut draft directory.

    Returns:
        dict with keys: draft_name, shot_count, has_audio, has_subtitles,
                        draft_dir, message
    """
    try:
        from pycapcut import DraftFolder
        from pycapcut import AudioMaterial, AudioSegment, TextSegment, TextStyle
        from pycapcut import Timerange, TrackType, ClipSettings
    except ImportError:
        raise ImportError(
            "剪映草稿生成需要 pycapcut 库。请运行: pip install pycapcut\n"
            "详见: https://github.com/slihao/pycapcut"
        )

    draft_dir = draft_dir or _find_draft_dir()

    if not os.path.isdir(draft_dir):
        raise FileNotFoundError(f"剪映草稿目录不存在: {draft_dir}\n请先安装并运行剪映专业版")

    shots = _extract_shots(script_content)
    if not shots:
        raise ValueError("未能从脚本中解析到分镜数据")

    # Sanitize title
    import re as _re
    safe_title = _re.sub(r'[\\/:*?"<>|]', '_', title)[:80]

    # Create draft via pycapcut
    df = DraftFolder(draft_dir)
    script = df.create_draft(safe_title, DEFAULT_WIDTH, DEFAULT_HEIGHT, DEFAULT_FPS, allow_replace=True)

    result = {
        "draft_name": safe_title,
        "shot_count": len(shots),
        "has_audio": False,
        "has_subtitles": False,
        "draft_dir": draft_dir,
        "message": "",
    }

    # ── Subtitles track ────────────────────────────────────────────
    if srt_path and os.path.isfile(srt_path):
        try:
            # Use pycapcut's built-in SRT import
            sub_style = TextStyle(
                size=7.0,
                bold=False,
                color=(1.0, 1.0, 1.0),  # white
                alpha=1.0,
                align=1,  # center
            )
            script.import_srt(srt_path, "AI字幕",
                             style_reference=None,
                             text_style=sub_style,
                             clip_settings=ClipSettings(transform_y=-0.78))
            result["has_subtitles"] = True
            logger.info("Imported SRT subtitles from %s", srt_path)
        except Exception as e:
            logger.warning("Failed to import SRT: %s", e)
            # Fallback: add text segments manually from shots
            _add_subtitle_segments(script, shots)
            result["has_subtitles"] = True
    else:
        # No SRT file → generate subtitles from shots
        _add_subtitle_segments(script, shots)
        result["has_subtitles"] = True

    # ── Audio track ────────────────────────────────────────────────
    if audio_path and os.path.isfile(audio_path):
        try:
            audio_mat = AudioMaterial(audio_path, "AI配音")
            # Add material to the script's materials
            script.materials.audios.append(audio_mat)

            # Calculate total duration from shots or use file estimate
            total_dur_us = int(sum(s.get("duration_sec", 5.0) for s in shots) * 1_000_000)

            # If audio is shorter than total, use audio's real duration
            import struct
            try:
                file_size = os.path.getsize(audio_path)
                estimated_dur_us = int(file_size / 16)  # ~128kbps MP3 ≈ 16KB/s = 16000B/s
                total_dur_us = min(total_dur_us, estimated_dur_us)
            except Exception:
                pass

            audio_seg = AudioSegment(
                material=audio_mat,
                target_timerange=Timerange(0, total_dur_us),
                volume=1.0,
            )

            script.add_track(TrackType.audio, "口播")
            script.add_segment(audio_seg, "口播")
            result["has_audio"] = True
            logger.info("Added TTS audio track: %s", audio_path)
        except Exception as e:
            logger.warning("Failed to add audio track: %s", e)

    # ── Save ───────────────────────────────────────────────────────
    script.save()

    # ═══ CRITICAL: fix empty name fields that CapCut needs ═══════════
    draft_path = os.path.join(draft_dir, safe_title)
    _fix_draft_metadata(draft_path, safe_title, len(shots))

    logger.info("CapCut draft '%s' saved to %s (%d shots, audio=%s, subs=%s)",
                safe_title, draft_dir, len(shots), result["has_audio"], result["has_subtitles"])

    parts = [f"已导入剪映「{safe_title}」"]
    parts.append(f"分镜 × {len(shots)}")
    if result["has_subtitles"]:
        parts.append("含字幕轨")
    if result["has_audio"]:
        parts.append("含配音音频")
    result["message"] = "，".join(parts)

    return result


def _add_subtitle_segments(script, shots: list[dict]) -> None:
    """Add subtitle text segments to the draft (fallback when no SRT file)."""
    from pycapcut import TextSegment, TextStyle, Timerange, TrackType, ClipSettings

    script.add_track(TrackType.text, "字幕")

    style = TextStyle(
        size=7.0,
        bold=False,
        color=(1.0, 1.0, 1.0),
        alpha=1.0,
        align=1,
    )
    cs = ClipSettings(transform_y=-0.78)

    current_us = 0
    for shot in shots:
        dur_us = int(shot.get("duration_sec", 5.0) * 1_000_000)
        text = shot.get("voiceover_text", "")
        if not text:
            text = shot.get("visual_content", "")[:100]

        seg = TextSegment(
            text=text,
            timerange=Timerange(current_us, dur_us),
            style=style,
            clip_settings=cs,
        )
        script.add_segment(seg, "字幕")
        current_us += dur_us


def _fix_draft_metadata(draft_path: str, title: str, shot_count: int) -> None:
    """After pycapcut saves, patch the draft_content.json and draft_meta_info.json
    to fill in the 'name' and 'draft_name' fields that CapCut requires to display
    the draft in its project list."""
    import json as _json

    # --- Fix draft_content.json ---
    content_path = os.path.join(draft_path, "draft_content.json")
    if os.path.isfile(content_path):
        with open(content_path, "r", encoding="utf-8") as f:
            content = _json.load(f)
        # Set the project name (top-level "name" key)
        content["name"] = title
        with open(content_path, "w", encoding="utf-8") as f:
            _json.dump(content, f, ensure_ascii=False, indent=2)

    # --- Fix draft_meta_info.json ---
    meta_path = os.path.join(draft_path, "draft_meta_info.json")
    if os.path.isfile(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = _json.load(f)
        meta["draft_name"] = title
        meta["tm_duration"] = int(shot_count * 5 * 1_000_000)  # approximate
        import time as _t
        meta["tm_draft_cloud_modified"] = int(_t.time() * 1000)
        with open(meta_path, "w", encoding="utf-8") as f:
            _json.dump(meta, f, ensure_ascii=False, indent=2)

    logger.info("Fixed draft metadata: name='%s'", title)


# ══════════════════════════════════════════════════════════════════════════════
# Legacy compatibility
# ══════════════════════════════════════════════════════════════════════════════

def build_and_export(
    script_content: str,
    title: str = "AI生成视频",
    audio_path: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> str:
    """Legacy wrapper — calls import_to_capcut and returns the draft folder path."""
    result = import_to_capcut(
        script_content=script_content,
        title=title,
        audio_path=audio_path,
        draft_dir=output_dir,
    )
    import os as _os
    draft_dir = result["draft_dir"]
    return _os.path.join(draft_dir, result["draft_name"])
