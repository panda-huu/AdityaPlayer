import asyncio
import os
import subprocess
from typing import Optional, Dict, Any

import aiohttp
from youtubesearchpython.__future__ import VideosSearch

from .. import console

# Safe defaults — crash nahi karega agar env missing ho
API_URL = getattr(console, "SHRUTI_API_URL", None) or "https://aruyt.up.railway.app"
API_KEY = getattr(console, "SHRUTI_API_KEY", None) or ""
DOWNLOAD_DIR = "downloads"


def check_duration(file_path: str) -> float:
    """ffprobe se duration nikaalo. Fail hone pe 0 return."""
    try:
        out = subprocess.check_output(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path,
            ],
            stderr=subprocess.DEVNULL,
            timeout=15,
        )
        return float(out.strip())
    except Exception:
        return 0.0


async def search(query: str) -> Optional[Dict[str, Any]]:
    """
    YouTube pe search karke title / duration / vidid / thumbnail return karta hai.
    Fail hone pe None return (crash nahi).
    """
    if not query or not str(query).strip():
        return None

    try:
        results = VideosSearch(str(query).strip(), limit=1)
        data = await results.next()
        result = data.get("result") or []
        if not result:
            return None

        r = result[0]
        return {
            "title": r.get("title") or "Unknown",
            "link": r.get("link") or "",
            "vidid": r.get("id") or "",
            "duration_min": r.get("duration") or "0:00",
            "thumbnail": (r.get("thumbnails") or [{}])[0].get("url", "").split("?")[0],
        }
    except Exception as e:
        print(f"[Youtube.search] Error: {e}", flush=True)
        return None


async def _download(vidid: str, media_type: str, ext: str, timeout_total: int) -> Optional[str]:
    """
    Common downloader. Success pe file path, fail pe None.
    Kabhi exception raise nahi karta.
    """
    if not vidid or len(str(vidid).strip()) < 3:
        return None

    vidid = str(vidid).strip()
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{vidid}.{ext}")
    loop = asyncio.get_event_loop()

    # Pehle se valid file hai to reuse
    try:
        if os.path.exists(file_path) and os.path.getsize(file_path) > 1024:
            dur = await loop.run_in_executor(None, check_duration, file_path)
            if dur and dur > 2:
                return file_path
            try:
                os.remove(file_path)
            except Exception:
                pass
    except Exception:
        pass

    if not API_KEY:
        print("[Youtube] API_KEY missing — download skip", flush=True)
        return None

    for attempt in range(3):
        try:
            timeout = aiohttp.ClientTimeout(total=timeout_total, connect=20)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    f"{API_URL.rstrip('/')}/download",
                    params={"url": vidid, "type": media_type, "api_key": API_KEY},
                ) as resp:

                    if resp.status == 429:
                        wait = 3 * (attempt + 1)
                        retry_after = resp.headers.get("Retry-After")
                        if retry_after and str(retry_after).isdigit():
                            wait = float(retry_after)
                        print(f"[Youtube] {media_type} 429 — wait {wait}s (try {attempt+1})", flush=True)
                        await asyncio.sleep(wait)
                        continue

                    if resp.status != 200:
                        body = (await resp.text())[:200]
                        print(f"[Youtube] {media_type} HTTP {resp.status}: {body} (try {attempt+1})", flush=True)
                        await asyncio.sleep(1)
                        continue

                    with open(file_path, "wb") as f:
                        async for chunk in resp.content.iter_chunked(131072):
                            f.write(chunk)

            if not (os.path.exists(file_path) and os.path.getsize(file_path) > 1024):
                continue

            dur = await loop.run_in_executor(None, check_duration, file_path)
            if dur and dur > 2:
                return file_path

            print(f"[Youtube] {media_type} invalid duration ({dur}s) — retry", flush=True)
            try:
                os.remove(file_path)
            except Exception:
                pass

        except asyncio.TimeoutError:
            print(f"[Youtube] {media_type} timeout (try {attempt+1})", flush=True)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass
        except Exception as e:
            print(f"[Youtube] {media_type} error (try {attempt+1}): {e}", flush=True)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass

        await asyncio.sleep(1)

    return None


async def download_song(vidid: str) -> Optional[str]:
    """Audio download. Fail pe None."""
    try:
        return await _download(vidid, "audio", "mp3", 90)
    except Exception as e:
        print(f"[Youtube.download_song] {e}", flush=True)
        return None


async def download_video(vidid: str) -> Optional[str]:
    """Video download. Fail pe None."""
    try:
        return await _download(vidid, "video", "mp4", 150)
    except Exception as e:
        print(f"[Youtube.download_video] {e}", flush=True)
        return None
