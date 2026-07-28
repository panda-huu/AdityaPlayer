import asyncio
import os
import subprocess
import aiohttp
from youtubesearchpython.__future__ import VideosSearch
from .. import console

API_URL = console.SHRUTI_API_URL
API_KEY = console.SHRUTI_API_KEY
DOWNLOAD_DIR = "downloads"


def check_duration(file_path) -> float:
    try:
        out = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path,
        ])
        return float(out.strip())
    except Exception:
        return 0


async def search(query: str):
    """YouTube pe search karke title/duration/vidid/thumbnail nikalo."""
    results = VideosSearch(query, limit=1)
    result = (await results.next()).get("result", [])
    if not result:
        return None
    r = result[0]
    return {
        "title": r["title"],
        "link": r["link"],
        "vidid": r["id"],
        "duration_min": r.get("duration") or "0:00",
        "thumbnail": r["thumbnails"][0]["url"].split("?")[0],
    }


async def _download(vidid: str, media_type: str, ext: str, timeout_total: int) -> str:
    if not vidid or len(vidid) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{vidid}.{ext}")
    loop = asyncio.get_event_loop()

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        dur = await loop.run_in_executor(None, check_duration, file_path)
        if dur and dur > 2:
            return file_path
        try:
            os.remove(file_path)
        except Exception:
            pass

    for attempt in range(3):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{API_URL}/download",
                    params={"url": vidid, "type": media_type, "api_key": API_KEY},
                    timeout=aiohttp.ClientTimeout(total=timeout_total, connect=15),
                ) as resp:
                    if resp.status == 429:
                        retry_after = resp.headers.get("Retry-After")
                        wait = float(retry_after) if retry_after and retry_after.isdigit() else (3 * (attempt + 1))
                        print(f"[API] {media_type} 429, retry {wait}s (attempt {attempt+1})", flush=True)
                        await asyncio.sleep(wait)
                        continue
                    if resp.status != 200:
                        print(f"[API] {media_type} HTTP {resp.status} (attempt {attempt+1})", flush=True)
                        continue
                    with open(file_path, "wb") as f:
                        async for chunk in resp.content.iter_chunked(131072):
                            f.write(chunk)

            if not (os.path.exists(file_path) and os.path.getsize(file_path) > 0):
                continue

            dur = await loop.run_in_executor(None, check_duration, file_path)
            if dur and dur > 2:
                return file_path

            print(f"[API] {media_type} invalid ({dur}s), retry (attempt {attempt+1})", flush=True)
            try:
                os.remove(file_path)
            except Exception:
                pass
        except asyncio.TimeoutError:
            print(f"[API] {media_type} timeout (attempt {attempt+1})", flush=True)
        except Exception as e:
            print(f"[API] {media_type} error (attempt {attempt+1}): {e}", flush=True)

    return None


async def download_song(vidid: str) -> str:
    return await _download(vidid, "audio", "mp3", 90)


async def download_video(vidid: str) -> str:
    return await _download(vidid, "video", "mp4", 150)
