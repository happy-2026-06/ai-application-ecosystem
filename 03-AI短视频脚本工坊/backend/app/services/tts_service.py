"""TTS (Text-to-Speech) service using Microsoft Edge TTS (free, no API key).

Uses the edge-tts library to generate natural-sounding Chinese speech
from the voiceover scripts produced by the AI script studio.

Two modes:
  1. Per-shot (推荐): generates a separate MP3 for each shot's voiceover text,
     then concatenates them. Captures the real duration of each clip so
     subtitles can be aligned precisely with the audio.
  2. Full-script (降级): reads the "完整口播稿" section and generates one MP3.
     Used when the shot table can't be parsed.
"""
import asyncio
import os
import logging
import tempfile
import time
from typing import Optional

import edge_tts

from app.config import settings

logger = logging.getLogger(__name__)

# ── Preset voice catalog ─────────────────────────────────────────────

VOICE_CATALOG = [
    # Mandarin female — 3 verified working with Edge-TTS
    {"id": "zh-CN-XiaoxiaoNeural", "name": "晓晓", "gender": "female", "style": "活泼·推荐", "tags": ["mandarin", "female"]},
    {"id": "zh-CN-XiaoyiNeural",   "name": "晓伊", "gender": "female", "style": "温柔自然", "tags": ["mandarin", "female"]},
    {"id": "zh-CN-XiaoxuanNeural", "name": "晓萱", "gender": "female", "style": "自信大方", "tags": ["mandarin", "female"]},
    # Mandarin male — 4 verified working with Edge-TTS
    {"id": "zh-CN-YunxiNeural",   "name": "云希", "gender": "male", "style": "阳光·推荐", "tags": ["mandarin", "male"]},
    {"id": "zh-CN-YunyangNeural", "name": "云扬", "gender": "male", "style": "专业新闻", "tags": ["mandarin", "male"]},
    {"id": "zh-CN-YunjianNeural", "name": "云健", "gender": "male", "style": "沉稳大叔", "tags": ["mandarin", "male"]},
    {"id": "zh-CN-YunxiaNeural",  "name": "云夏", "gender": "male", "style": "年轻活力", "tags": ["mandarin", "male"]},
    # Cantonese — 3 verified working with Edge-TTS
    {"id": "zh-HK-HiuMaanNeural", "name": "晓曼", "gender": "female", "style": "粤语女声", "tags": ["cantonese", "female"]},
    {"id": "zh-HK-HiuGaaiNeural", "name": "晓佳", "gender": "female", "style": "粤语女声", "tags": ["cantonese", "female"]},
    {"id": "zh-HK-WanLungNeural", "name": "云龙", "gender": "male",   "style": "粤语男声", "tags": ["cantonese", "male"]},
    # Taiwanese Mandarin — 3 verified working with Edge-TTS
    {"id": "zh-TW-HsiaoChenNeural", "name": "晓臻", "gender": "female", "style": "台普女声", "tags": ["taiwanese", "female"]},
    {"id": "zh-TW-HsiaoYuNeural",   "name": "晓雨", "gender": "female", "style": "台普女声", "tags": ["taiwanese", "female"]},
    {"id": "zh-TW-YunJheNeural",    "name": "云哲", "gender": "male",   "style": "台普男声", "tags": ["taiwanese", "male"]},
]

# ── Voice listing ────────────────────────────────────────────────────

def list_voices(language: str = "zh") -> list[dict]:
    """Return available Chinese voices, optionally filtered by language tag.

    Args:
        language: "zh" (all Chinese), "mandarin", "cantonese", "taiwanese"
    """
    if language == "zh":
        return VOICE_CATALOG
    return [v for v in VOICE_CATALOG if language in v.get("tags", [])]


def get_voice_by_id(voice_id: str) -> Optional[dict]:
    """Look up a single voice by its edge-tts ID."""
    for v in VOICE_CATALOG:
        if v["id"] == voice_id:
            return v
    return None


# ── Core TTS ─────────────────────────────────────────────────────────

async def _generate_tts_bytes(
    text: str,
    voice: str,
    speed: str,
    timeout_sec: float = 120.0,
) -> bytes:
    """Generate TTS audio bytes for a single text segment (no file on disk).

    Includes a timeout to prevent edge-tts from hanging indefinitely.
    """
    import asyncio as _asyncio

    async def _stream():
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=speed,
        )
        chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])
        return b"".join(chunks)

    try:
        return await _asyncio.wait_for(_stream(), timeout=timeout_sec)
    except _asyncio.TimeoutError:
        logger.error("TTS timeout for text len=%d after %.0fs", len(text), timeout_sec)
        raise RuntimeError(f"语音合成超时（{timeout_sec:.0f}秒），文本过长或网络异常，请重试")
    except Exception:
        logger.exception("TTS stream failed for text len=%d", len(text))
        raise


def _concat_mp3_files(mp3_paths: list[str], output_path: str) -> str:
    """Concatenate multiple MP3 files into one using pydub.

    Uses pydub (ffmpeg-backed) for robust concatenation that handles
    variable-bitrate MP3s, different sample rates, and ID3 metadata correctly.
    Falls back to raw binary concat if pydub/ffmpeg is unavailable.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Try pydub first (robust, handles all MP3 variants)
    try:
        from pydub import AudioSegment
        combined = AudioSegment.empty()
        for path in mp3_paths:
            combined += AudioSegment.from_mp3(path)
        combined.export(output_path, format="mp3")
        return output_path
    except Exception as e:
        logger.warning("pydub concat failed (%s), falling back to raw binary concat", e)

    # Fallback: raw binary concatenation (works for CBR MP3 without metadata)
    combined = bytearray()
    for i, path in enumerate(mp3_paths):
        with open(path, 'rb') as f:
            data = f.read()
        if i == 0:
            combined.extend(data)
        else:
            # Strip ID3v2 header if present (starts with 'ID3')
            if data[:3] == b'ID3' and len(data) > 9:
                size = (data[6] << 21) | (data[7] << 14) | (data[8] << 7) | data[9]
                combined.extend(data[10 + size:])
            else:
                combined.extend(data)

    with open(output_path, 'wb') as f:
        f.write(combined)
    return output_path


async def generate_tts_per_shot(
    shots: list[dict],
    voice: str = None,
    speed: str = None,
    output_dir: str = None,
) -> dict:
    """Generate TTS audio for each shot individually, then merge.

    Each dict in `shots` should have at least 'voiceover_text' and 'index'.
    The voiceover_text for each shot is read individually, so the real
    duration of each clip can be captured.

    Returns:
        {
            "merged_path": str,           # path to the full concatenated MP3
            "filename": str,              # basename of the merged file
            "shot_durations": [           # per-shot real audio durations
                {"index": 1, "duration_sec": 3.2},
                {"index": 2, "duration_sec": 5.1},
                ...
            ],
            "total_duration_sec": float,  # total merged audio duration
        }
    """
    voice = voice or settings.TTS_DEFAULT_VOICE
    speed = speed or settings.TTS_DEFAULT_SPEED
    output_dir = output_dir or settings.TTS_OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    import uuid

    from app.services.subtitle_service import _clean_voiceover_text

    shot_durations = []
    temp_files = []

    for shot in shots:
        raw_text = (shot.get('voiceover_text') or '').strip()
        # Secondary filter: ensure director notes never reach edge-tts,
        # even if the caller forgot to run _clean_voiceover_text upstream.
        text = _clean_voiceover_text(raw_text)
        if not text:
            continue

        # Generate audio bytes for this shot
        try:
            audio_bytes = await _generate_tts_bytes(text=text, voice=voice, speed=speed)
        except Exception as e:
            logger.warning("Shot %d TTS failed: %s", shot.get('index', '?'), e)
            continue

        if not audio_bytes:
            continue

        # Write to a temp MP3 so we can measure its real duration
        shot_filename = f"tts_shot_{shot.get('index', len(shot_durations) + 1)}_{uuid.uuid4().hex[:6]}.mp3"
        shot_path = os.path.join(output_dir, shot_filename)
        with open(shot_path, 'wb') as f:
            f.write(audio_bytes)

        # Measure real audio duration
        actual_dur = get_audio_duration(shot_path)
        if actual_dur is None:
            # Estimate from byte length (edge-tts ~16 kbps CBR ≈ 2000 bytes/s)
            actual_dur = len(audio_bytes) / 2000.0

        shot_durations.append({
            "index": shot.get('index', len(shot_durations) + 1),
            "duration_sec": round(actual_dur, 2),
            "text": text,
            "temp_file": shot_path,
        })
        temp_files.append(shot_path)
        logger.debug("Shot %d TTS: %.1fs for %d chars", shot.get('index', '?'), actual_dur, len(text))

    if not temp_files:
        raise RuntimeError("没有生成任何分镜配音（所有镜头口播文案为空？）")

    # Merge all shot MP3s into one
    merged_filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
    merged_path = os.path.join(output_dir, merged_filename)
    _concat_mp3_files(temp_files, merged_path)

    # Measure total merged duration
    total_dur = get_audio_duration(merged_path)
    if total_dur is None:
        total_dur = sum(d["duration_sec"] for d in shot_durations)

    # Clean up individual shot files (keep only the merged one)
    for tf in temp_files:
        try:
            os.remove(tf)
        except OSError:
            pass

    logger.info(
        "Per-shot TTS done: %d shots → %s (total %.1fs)",
        len(shot_durations), merged_filename,
        total_dur,
    )

    return {
        "merged_path": merged_path,
        "filename": merged_filename,
        "shot_durations": shot_durations,
        "total_duration_sec": round(total_dur, 2) if total_dur else 0,
    }


async def generate_tts(
    text: str,
    voice: str = None,
    speed: str = None,
    output_dir: str = None,
) -> str:
    """Generate an MP3 audio file from text using Edge TTS (legacy mode).

    NOTE: Prefer generate_tts_per_shot() for script studio use — it provides
    per-shot timing data for subtitle alignment.

    Args:
        text: The text to speak (Chinese/English).
        voice: Edge-TTS voice ID (default from settings).
        speed: Speed modifier, e.g. "+10%" or "-5%" (default from settings).
        output_dir: Where to write the MP3 file (default from settings).

    Returns:
        Absolute path to the generated .mp3 file.
    """
    voice = voice or settings.TTS_DEFAULT_VOICE
    speed = speed or settings.TTS_DEFAULT_SPEED
    output_dir = output_dir or settings.TTS_OUTPUT_DIR

    os.makedirs(output_dir, exist_ok=True)

    # Safety net: strip director notes before TTS
    from app.services.subtitle_service import _clean_voiceover_text
    text = _clean_voiceover_text(text)
    if not text or len(text.strip()) < 2:
        raise ValueError("过滤后无可口播文本（所有内容都是导演备注）")

    import uuid
    filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
    output_path = os.path.join(output_dir, filename)

    audio_bytes = await _generate_tts_bytes(text=text, voice=voice, speed=speed)

    with open(output_path, 'wb') as f:
        f.write(audio_bytes)

    logger.info("TTS generated: voice=%s, len=%d chars → %s", voice, len(text), output_path)
    return output_path


async def stream_tts_bytes(
    text: str,
    voice: str = None,
    speed: str = None,
) -> bytes:
    """Generate TTS audio and return bytes (no file on disk).

    Useful for streaming responses or in-memory use.
    """
    voice = voice or settings.TTS_DEFAULT_VOICE
    speed = speed or settings.TTS_DEFAULT_SPEED

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=speed,
    )

    # Collect chunks into a single bytes buffer
    chunks = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            chunks.append(chunk["data"])

    return b"".join(chunks)


# ── Utility: extract voiceover text from markdown script ─────────────

def extract_voiceover_text(markdown_content: str) -> str:
    """Extract the full voiceover script from an AI-generated Markdown result.

    Looks for the '完整口播稿' section (wrapped in ``` code block),
    stripping stage-direction tags like [黄金前3秒] but keeping the spoken text.
    Also filters out director notes / stage directions that are not spoken dialogue.
    """
    import re

    # Strategy 1: try to find the full-voiceover code block
    # Matches ``` ... ``` after "口播稿" heading
    code_block_pat = re.compile(
        r'口播稿\s*```[^\n]*\n(.*?)```',
        re.DOTALL,
    )
    m = code_block_pat.search(markdown_content)
    if m:
        raw = m.group(1).strip()
        # Strip stage tags like [黄金前3秒], [痛点引爆], etc.
        raw = re.sub(r'\[[^\]]*\]', '', raw)
        # Collapse whitespace
        raw = re.sub(r'\n{3,}', '\n\n', raw)
        raw = raw.strip()

        # Filter out lines that are director notes, not spoken dialogue
        from app.services.subtitle_service import _clean_voiceover_text
        cleaned_lines = []
        for line in raw.split('\n'):
            cleaned = _clean_voiceover_text(line)
            if cleaned:
                cleaned_lines.append(cleaned)
        if cleaned_lines:
            return '\n'.join(cleaned_lines)
        # If ALL lines were filtered out, fall through to strategy 2

    # Strategy 2: extract all 口播文案 cells from the shot table
    # Look for the shot table and extract the 口播文案 column
    from app.services.subtitle_service import _clean_voiceover_text

    lines = markdown_content.split('\n')
    voiceover_lines = []
    in_table = False
    voiceover_col = -1

    for line in lines:
        line = line.strip()
        if '|' not in line:
            continue
        if not line.startswith('|'):
            continue

        cells = [c.strip() for c in line.split('|')[1:-1]]

        # Detect header row
        if '镜号' in line or '口播' in line:
            in_table = True
            for i, c in enumerate(cells):
                if '口播' in c:
                    voiceover_col = i
                    break
            continue

        # Separator row
        if '---' in line or ':--:' in line:
            continue

        if not in_table or voiceover_col < 0:
            continue

        if voiceover_col < len(cells) and cells[voiceover_col]:
            cleaned = _clean_voiceover_text(cells[voiceover_col])
            if cleaned:
                voiceover_lines.append(cleaned)

    if voiceover_lines:
        return '\n'.join(voiceover_lines)

    # Fallback: return the raw content (user will get what they see)
    return markdown_content


# ── Audio duration extraction ──────────────────────────────────────────

def get_audio_duration(filepath: str) -> Optional[float]:
    """Read the actual audio duration from an MP3 file using mutagen.

    Returns duration in seconds, or None if the file can't be read.
    """
    try:
        from mutagen.mp3 import MP3
        audio = MP3(filepath)
        return audio.info.length
    except Exception as e:
        logger.warning("Failed to read audio duration from %s: %s", filepath, e)
        return None
