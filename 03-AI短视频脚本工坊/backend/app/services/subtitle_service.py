"""Subtitle export service: parse shot tables from AI output and generate SRT/ASS subtitle files.

Formats supported:
  - SRT (SubRip): universal, simple plain-text format
  - ASS (Advanced SubStation Alpha): styled subtitles with font/color/position info
"""
import os
import re
import logging
from dataclasses import dataclass, field
from typing import Optional

import pysrt
from pysrt import SubRipItem, SubRipFile

from app.config import settings

logger = logging.getLogger(__name__)


# ── Data models ──────────────────────────────────────────────────────

@dataclass
class ShotInfo:
    """Parsed information for one shot in the storyboard table."""
    index: int
    duration_sec: float          # shot duration in seconds
    visual_content: str = ""     # 画面内容
    voiceover_text: str = ""     # 口播文案
    subtitle_effect: str = ""    # 字幕特效


# ── Voiceover text cleaner ────────────────────────────────────────────

# Patterns that indicate a text is a director note, NOT spoken dialogue
_NON_VOICEOVER_PATTERNS = [
    # Pacing / rhythm notes (specific structure)
    r'^节奏[，,\s]+.+$',                        # 节奏，前快后稳 / 节奏：先快后慢
    r'^[前先][快慢稳缓急加][后然][快慢稳缓急加文].*$',  # 前快后稳 / 先慢后快 / 前快后文
    r'^语速[加放变][快慢缓急稳].*$',
    r'^[快慢]节奏.*$',
    # Audio / music directions
    r'^(纯\s*)?BGM[\s\+]*.*$',
    r'^(纯\s*)?ASMR[\s\+]*.*$',
    r'^配合音乐.*$',
    r'^背景音乐.*$',
    r'^音效.*$',
    r'[（(]音效[）)].*',
    # Camera / shooting directions
    r'^特写镜头.*$',
    r'^推拉摇移.*$',
    r'^(从|由).*镜头.*$',
    r'^镜头[从向].*$',
    # Pure notes (not spoken)
    r'^[（(].*[）)]$',  # parenthetical notes like "(此处留白)"
    r'^此处[留空无].*$',
    r'^[无没暫暂][有]*[口播配音对白].*$',
]

# Broad patterns: only checked for SHORT texts (≤30 chars) to avoid
# matching long, legitimate dialogue that happens to contain these words
_BROAD_NOTE_PATTERNS = [
    r'^[前先开].{0,4}[节奏语速].{0,4}[快慢稳缓急]',  # 前边节奏快 / 开头语速放慢
    r'.{0,5}[节奏语速].{0,3}[要该应].{0,3}[快慢稳缓急]',  # 节奏要快 / 语速该慢下来
    r'.{0,5}[节奏语速].{0,3}[前后然][期面头段]',  # 节奏前期快 / 语速后面放缓
]

# Keyword heuristics: if a text is short AND contains these, it's likely a note
_NOTE_KEYWORDS = [
    '节奏', '语速', '气息', '停顿', '留白',
    'BGM', 'bgm', '音效', '配乐', '背景音',
    '镜头', '特写', '运镜', '转场', '推拉',
    '配合', '剪辑', '后期', '此处',
]


def _clean_voiceover_text(text: str) -> str:
    """Remove director notes / stage directions from voiceover text.

    Returns cleaned text suitable for TTS and subtitles, or empty string
    if the entire text is a director note (not spoken dialogue).
    """
    import re as _re

    if not text or not text.strip():
        return ''

    original = text.strip()

    # Check if the ENTIRE text is a director note
    for pattern in _NON_VOICEOVER_PATTERNS:
        if _re.match(pattern, original, _re.IGNORECASE):
            logger.debug("Voiceover filter: removed pure note → %r", original[:60])
            return ''

    # Check short texts with note keywords
    if len(original) <= 15:
        for kw in _NOTE_KEYWORDS:
            if kw in original:
                logger.debug("Voiceover filter: removed short note → %r", original[:60])
                return ''

    # Check broad patterns ONLY for short texts (≤30 chars)
    # Longer texts are almost certainly spoken dialogue, not director notes
    if len(original) <= 30:
        for pattern in _BROAD_NOTE_PATTERNS:
            if _re.search(pattern, original, _re.IGNORECASE):
                logger.debug("Voiceover filter: removed broad-pattern note → %r", original[:60])
                return ''

    # Remove inline stage tags like [黄金前3秒], [痛点引爆], etc.
    cleaned = _re.sub(r'\[[^\]]*\]', '', original)

    # Remove trailing parenthetical notes like "（语速放慢）" or "(配合音乐)"
    cleaned = _re.sub(r'[（(][^)）]*(?:节奏|语速|BGM|音效|配乐|镜头|剪辑|后期|转场|停顿|留白|气息)[^)）]*[)）]', '', cleaned)

    # Collapse multiple spaces / newlines
    cleaned = _re.sub(r'\s+', ' ', cleaned).strip()

    # If after cleaning nothing meaningful remains, return empty
    if not cleaned or len(cleaned) < 2:
        return ''

    return cleaned


# ── Shot table parser ────────────────────────────────────────────────

def parse_shot_table(markdown_content: str, default_duration: float = 5.0) -> list[ShotInfo]:
    """Parse the Markdown shot table from an AI-generated script.

    Expected table format:
    | 镜号 | 时长 | 画面内容 | 口播文案 | 字幕特效 |
    |:--:|:--:|---------|---------|---------|

    The 时长 (duration) column can contain:
      - A bare number like "3" or "5" (treated as seconds)
      - A range like "3-5s" or "3～5秒" (takes the midpoint)

    Args:
        markdown_content: Full AI-generated Markdown output.
        default_duration: Duration in seconds to use when parsing fails.

    Returns:
        List of ShotInfo in order.
    """
    lines = markdown_content.split('\n')
    shots = []

    # Locate columns from header
    col_map = {}  # key → index
    in_table = False

    for line in lines:
        line = line.strip()
        if not line.startswith('|'):
            # Table block ended — reset so next table gets its own header detection
            in_table = False
            continue

        cells = [c.strip() for c in line.split('|')[1:-1]]

        # Skip empty rows
        if not any(cells):
            continue

        # Header detection
        if not in_table:
            header_text = ' '.join(cells).lower()
            # MUST contain 镜号 — not just '画面' or '字幕' which appear in other tables
            if '镜号' in header_text:
                in_table = True
                for i, c in enumerate(cells):
                    c_lower = c.lower()
                    if '镜号' in c_lower:
                        col_map['index'] = i
                    elif '时长' in c_lower or '时间' in c_lower:
                        col_map['duration'] = i
                    elif '画面' in c_lower:
                        col_map['visual'] = i
                    elif '口播' in c_lower:
                        col_map['voiceover'] = i
                    elif '字幕' in c_lower:
                        col_map['subtitle'] = i
                continue
            else:
                continue  # not our table yet

        # Separator row
        if all(re.match(r'^:?-+:?$', c) or c == '' for c in cells if c):
            continue

        # Data row
        if not in_table:
            continue

        # Safety: if the current row has fewer cells than our column mappings expect,
        # it's likely from a different table — reset and skip
        max_col_needed = max(col_map.values()) if col_map else 0
        if max_col_needed >= len(cells):
            in_table = False
            continue

        # Parse index
        idx_str = cells[col_map.get('index', 0)] if 'index' in col_map else '0'
        try:
            idx = int(re.sub(r'[^\d]', '', idx_str))
        except ValueError:
            idx = len(shots) + 1

        # Parse duration
        duration = default_duration
        if 'duration' in col_map:
            dur_str = cells[col_map['duration']]
            dur = _parse_duration(dur_str)
            if dur is not None:
                duration = dur

        voiceover = cells[col_map['voiceover']] if 'voiceover' in col_map else ''
        voiceover = _clean_voiceover_text(voiceover)  # strip director notes
        visual = cells[col_map['visual']] if 'visual' in col_map else ''
        subtitle_effect = cells[col_map['subtitle']] if 'subtitle' in col_map else ''

        shots.append(ShotInfo(
            index=idx,
            duration_sec=duration,
            visual_content=visual,
            voiceover_text=voiceover,
            subtitle_effect=subtitle_effect,
        ))

    return shots


def _parse_duration(dur_str: str) -> Optional[float]:
    """Parse a duration string like '3', '5s', '3-5s', '3～5秒' → seconds float."""
    if not dur_str:
        return None
    dur_str = dur_str.replace('秒', '').replace('s', '').replace('S', '').strip()
    # Range like "3-5" → midpoint
    range_match = re.match(r'(\d+\.?\d*)\s*[-\~～]\s*(\d+\.?\d*)', dur_str)
    if range_match:
        lo = float(range_match.group(1))
        hi = float(range_match.group(2))
        return (lo + hi) / 2.0
    # Bare number
    try:
        return float(dur_str)
    except ValueError:
        return None


# ── SRT generation ───────────────────────────────────────────────────

def generate_srt(
    shots: list[ShotInfo],
    words_per_second: float = None,
    target_duration_sec: float = None,
    shot_durations: list[float] | None = None,
) -> str:
    """Generate an SRT subtitle string from parsed shots.

    Each shot's voiceover text becomes one subtitle entry.
    Timestamps are calculated cumulatively based on shot durations.

    Args:
        shots: Parsed shot data.
        words_per_second: Speaking rate for estimating duration from text length
                          when shot durations are unavailable.
        target_duration_sec: (DEPRECATED) If shot_durations is provided, this is
                             ignored. Otherwise, all segments are scaled linearly
                             so the total matches this value. Prefer shot_durations.
        shot_durations: Per-shot real audio durations (seconds), one per shot,
                        in the same order as shots. When provided, each subtitle
                        entry is timed to the exact duration of its TTS audio clip.
                        This is the MOST ACCURATE mode.

    Returns:
        SRT-formatted string (UTF-8).
    """
    wps = words_per_second or settings.SUBTITLE_DEFAULT_WPS

    # Determine which shots have voiceover text
    shot_texts = [s.voiceover_text for s in shots if len(s.voiceover_text) > 0]

    # Compute per-shot durations
    if shot_durations and len(shot_durations) > 0:
        # PRECISE mode: use real TTS per-shot audio durations
        # Map shot_durations to the filtered shot_texts list
        raw_durations = list(shot_durations[:len(shot_texts)])
        # If some shots are missing durations, fill with estimate
        while len(raw_durations) < len(shot_texts):
            t = shot_texts[len(raw_durations)]
            raw_durations.append(max(len(t) / wps, 0.5))
        scale = 1.0  # no scaling needed — we have real timings
        logger.info("SRT: using per-shot audio durations (precise mode), %d segments", len(raw_durations))
    else:
        # ESTIMATE mode: guess durations from text length or table data
        raw_durations = []
        for shot in shots:
            text_len = len(shot.voiceover_text)
            if text_len == 0:
                continue
            dur = shot.duration_sec if shot.duration_sec > 0 else max(text_len / wps, 1.0)
            raw_durations.append(dur)

        if not raw_durations:
            return ""

        # If we have a target duration, scale all segments proportionally
        total_raw = sum(raw_durations)
        if target_duration_sec and target_duration_sec > 0 and total_raw > 0:
            scale = target_duration_sec / total_raw
            logger.info("SRT: linearly scaled to match total TTS duration (%.1fs → %.1fs)", total_raw, target_duration_sec)
        else:
            scale = 1.0
            logger.info("SRT: using estimated durations (no audio alignment)")

    items = []
    current_time_sec = 0.0

    for i, dur in enumerate(raw_durations):
        scaled_dur = dur * scale
        start_ms = int(current_time_sec * 1000)
        end_ms = int((current_time_sec + scaled_dur) * 1000)

        item = SubRipItem(
            index=len(items) + 1,
            start=_ms_to_subrip_time(start_ms),
            end=_ms_to_subrip_time(end_ms),
            text=shot_texts[i],
        )
        items.append(item)
        current_time_sec += scaled_dur

    subrip_file = SubRipFile(items)
    return '\n'.join(str(item) for item in subrip_file)


def _ms_to_subrip_time(ms: int) -> pysrt.SubRipTime:
    """Convert milliseconds to pysrt SubRipTime."""
    from pysrt import SubRipTime
    hours = ms // 3600000
    ms %= 3600000
    minutes = ms // 60000
    ms %= 60000
    seconds = ms // 1000
    milliseconds = ms % 1000
    return SubRipTime(
        hours=hours,
        minutes=minutes,
        seconds=seconds,
        milliseconds=milliseconds,
    )


# ── ASS generation ───────────────────────────────────────────────────

ASS_TEMPLATE = """[Script Info]
Title: {title}
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,{outline},0,2,10,10,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
{events}
"""


def generate_ass(
    shots: list[ShotInfo],
    title: str = "AI生成字幕",
    font_name: str = "Microsoft YaHei",
    font_size: int = 54,
    outline: float = 3.0,
    words_per_second: float = None,
    target_duration_sec: float = None,
    shot_durations: list[float] | None = None,
) -> str:
    """Generate an ASS subtitle string from parsed shots.

    Args:
        shots: Parsed shot data.
        title: Subtitle track title.
        font_name: Font family name.
        font_size: Font size in pixels.
        outline: Outline width.
        words_per_second: Speaking rate for estimating duration.
        target_duration_sec: (DEPRECATED) Prefer shot_durations instead.
        shot_durations: Per-shot real audio durations (seconds). When provided,
                        each subtitle is timed to the exact TTS clip duration.

    Returns:
        ASS-formatted string (UTF-8).
    """
    wps = words_per_second or settings.SUBTITLE_DEFAULT_WPS

    shot_texts = [s.voiceover_text for s in shots if len(s.voiceover_text) > 0]

    if shot_durations and len(shot_durations) > 0:
        raw_durations = list(shot_durations[:len(shot_texts)])
        while len(raw_durations) < len(shot_texts):
            t = shot_texts[len(raw_durations)]
            raw_durations.append(max(len(t) / wps, 0.5))
        scale = 1.0
    else:
        raw_durations = []
        for shot in shots:
            text_len = len(shot.voiceover_text)
            if text_len == 0:
                continue
            dur = shot.duration_sec if shot.duration_sec > 0 else max(text_len / wps, 1.0)
            raw_durations.append(dur)

        if not raw_durations:
            return ASS_TEMPLATE.format(
                title=title, font_name=font_name, font_size=font_size,
                outline=outline, events='',
            )

        total_raw = sum(raw_durations)
        scale = (target_duration_sec / total_raw) if (target_duration_sec and target_duration_sec > 0 and total_raw > 0) else 1.0

    event_lines = []
    current_time_sec = 0.0

    for i, dur in enumerate(raw_durations):
        scaled_dur = dur * scale
        start_str = _sec_to_ass_time(current_time_sec)
        end_str = _sec_to_ass_time(current_time_sec + scaled_dur)
        safe_text = shot_texts[i].replace('\n', '\\N')
        event_lines.append(
            f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{safe_text}"
        )
        current_time_sec += scaled_dur

    return ASS_TEMPLATE.format(
        title=title,
        font_name=font_name,
        font_size=font_size,
        outline=outline,
        events='\n'.join(event_lines),
    )


def _sec_to_ass_time(sec: float) -> str:
    """Convert seconds to ASS time string H:MM:SS.cc."""
    total_cs = int(sec * 100)  # centiseconds
    hours = total_cs // 360000
    total_cs %= 360000
    minutes = total_cs // 6000
    total_cs %= 6000
    seconds = total_cs // 100
    cs = total_cs % 100
    return f"{hours}:{minutes:02d}:{seconds:02d}.{cs:02d}"


# ── File export ──────────────────────────────────────────────────────

def export_subtitle_file(
    content: str,
    format: str,
    output_dir: str = None,
) -> str:
    """Write a subtitle string to a file.

    Args:
        content: The subtitle text in the target format.
        format: "srt" or "ass".
        output_dir: Output directory (default from settings).

    Returns:
        Absolute path to the written file.
    """
    output_dir = output_dir or settings.SUBTITLE_OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    import uuid
    ext = f".{format}"
    filename = f"subtitles_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(output_dir, filename)

    # Write with UTF-8 BOM for maximum player compatibility
    with open(filepath, 'w', encoding='utf-8-sig') as f:
        f.write(content)

    logger.info("Subtitle exported: format=%s, size=%d bytes → %s", format, len(content), filepath)
    return filepath
