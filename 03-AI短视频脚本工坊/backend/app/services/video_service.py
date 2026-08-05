"""AI Video Generation service using 智谱 CogVideoX API.

Generates short video clips from shot descriptions in the AI script.
CogVideoX-2 is the recommended model: good quality, official Python SDK,
50 RMB free credits for new users, no VPN needed.
"""
import asyncio
import os
import logging
import time
from typing import Optional

from zhipuai import ZhipuAI

from app.config import settings

logger = logging.getLogger(__name__)

# Lazy client singleton
_client: Optional[ZhipuAI] = None


def _get_client() -> ZhipuAI:
    """Get or create the ZhipuAI client."""
    global _client
    if _client is not None:
        return _client
    if not settings.ZHIPU_API_KEY:
        raise ValueError(
            "Zhipu API key not configured. Set ZHIPU_API_KEY in .env "
            "or via environment variable."
        )
    _client = ZhipuAI(api_key=settings.ZHIPU_API_KEY)
    logger.info("ZhipuAI client initialized")
    return _client


# ── Video generation ─────────────────────────────────────────────────

async def generate_video(
    prompt: str,
    model: str = None,
    image_url: str = None,
    size: str = "1080x1920",
    output_dir: str = None,
) -> dict:
    """Submit a video generation task to CogVideoX.

    Args:
        prompt: Text description of the desired video content (Chinese supported).
        model: Model name (default cogvideox-2).
        image_url: Optional reference image URL for image-to-video.
        size: Output resolution (default 1080x1920 for portrait video).
        output_dir: Download directory.

    Returns:
        dict: {"task_id": str, "status": "submitted", "prompt": str}
    """
    model = model or settings.ZHIPU_VIDEO_MODEL

    client = _get_client()

    kwargs = {
        "model": model,
        "prompt": prompt,
    }
    if image_url:
        kwargs["image_url"] = image_url
    if size:
        kwargs["size"] = size

    # The SDK call is synchronous; run in thread to avoid blocking
    response = await asyncio.to_thread(
        client.videos.generations,
        **kwargs,
    )

    task_id = response.id
    logger.info("Video generation submitted: model=%s, task_id=%s, prompt_len=%d",
                model, task_id, len(prompt))

    return {
        "task_id": task_id,
        "status": "submitted",
        "model": model,
        "prompt": prompt,
    }


async def query_video_status(task_id: str) -> dict:
    """Query the status of a video generation task.

    Returns:
        dict with keys: task_id, status (submitted/processing/succeeded/failed),
        video_url (when succeeded), error (when failed)
    """
    client = _get_client()

    response = await asyncio.to_thread(
        client.videos.retrieve_videos_result,
        task_id,
    )

    result = {
        "task_id": task_id,
        "status": response.task_status,
    }

    if response.task_status == "SUCCESS":
        video_url = getattr(response, "video_result", None)
        if video_url and isinstance(video_url, list) and len(video_url) > 0:
            result["video_url"] = video_url[0].url if hasattr(video_url[0], 'url') else str(video_url[0])
        else:
            result["video_url"] = getattr(response, "video_result", None)
    elif response.task_status == "FAIL":
        result["error"] = getattr(response, "task_status_msg", "Unknown error")

    return result


# ── Batch generation for all shots ──────────────────────────────────

async def generate_videos_for_shots(
    shots: list[dict],
    model: str = None,
    concurrent: int = 2,
) -> list[dict]:
    """Submit video generation tasks for multiple shots.

    Each shot dict should have:
      - index: shot number
      - visual_content: description to feed as the video prompt

    Args:
        shots: List of shot dicts.
        model: Model name.
        concurrent: Max concurrent submissions.

    Returns:
        List of result dicts with task_id for each shot.
    """
    model = model or settings.ZHIPU_VIDEO_MODEL
    semaphore = asyncio.Semaphore(concurrent)

    async def submit_one(shot: dict) -> dict:
        async with semaphore:
            prompt = shot.get("visual_content", "") or shot.get("voiceover_text", "")
            if not prompt:
                return {
                    "index": shot.get("index", 0),
                    "status": "skipped",
                    "reason": "No visual description available",
                }
            result = await generate_video(
                prompt=prompt,
                model=model,
                image_url=shot.get("image_url"),
            )
            result["index"] = shot.get("index", 0)
            return result

    tasks = [submit_one(s) for s in shots]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            output.append({
                "index": shots[i].get("index", i + 1),
                "status": "error",
                "error": str(r),
            })
        else:
            output.append(r)

    return output


# ── Download helpers ─────────────────────────────────────────────────

async def download_video(video_url: str, output_dir: str = None) -> str:
    """Download a generated video from URL to local storage.

    Args:
        video_url: The URL returned by query_video_status.
        output_dir: Where to save the file.

    Returns:
        Local file path to the downloaded video.
    """
    output_dir = output_dir or settings.VIDEO_OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    import uuid
    import aiohttp

    ext = ".mp4"
    filename = f"video_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(output_dir, filename)

    async with aiohttp.ClientSession() as session:
        async with session.get(video_url) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Download failed: HTTP {resp.status}")
            with open(filepath, 'wb') as f:
                f.write(await resp.read())

    logger.info("Video downloaded: %s → %s", video_url[:80], filepath)
    return filepath
