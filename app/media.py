from __future__ import annotations

import json
import shutil
import subprocess
import urllib.parse
from pathlib import Path

import httpx

from .config import settings


USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


class MediaError(RuntimeError):
    pass


def _platform(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc.lower()
    if "xiaohongshu.com" in host or "xhslink.com" in host:
        return "xiaohongshu"
    if "douyin.com" in host or "tiktok.com" in host:
        return "douyin"
    if "bilibili.com" in host or "b23.tv" in host:
        return "bilibili"
    if "youtube.com" in host or "youtu.be" in host:
        return "youtube"
    return "generic"


def _download_direct(url: str, output: Path) -> Path:
    with httpx.stream("GET", url, headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=90) as response:
        response.raise_for_status()
        with output.open("wb") as target:
            for chunk in response.iter_bytes(1024 * 1024):
                target.write(chunk)
    return output


def _resolve_ai_douyin(url: str) -> list[str]:
    env = settings.skill_env
    api_key = env.get("AI_DOUYIN_API_KEY", "")
    if not api_key:
        raise MediaError("小红书/抖音链接需要已有的 AI Douyin API Key；也可以直接上传视频文件。")
    base = env.get("AI_DOUYIN_API_BASE", "https://top9.cc").rstrip("/")
    if base.endswith("/api/v1"):
        endpoint = f"{base}/video/download-url"
    elif base.endswith("/api"):
        endpoint = f"{base}/v1/video/download-url"
    else:
        endpoint = f"{base}/api/v1/video/download-url"
    response = httpx.post(endpoint, headers={"X-API-Key": api_key}, json={"url": url}, timeout=45)
    if response.status_code == 402:
        raise MediaError("AI Douyin 解析额度不足；请充值积分或直接上传视频。")
    if response.status_code == 401:
        raise MediaError("AI Douyin API Key 无效。")
    response.raise_for_status()
    data = response.json()
    candidates = data.get("download_urls") or [data.get("download_url")]
    return [item for item in candidates if item]


def _download_ytdlp(url: str, work_dir: Path) -> Path:
    command = [
        shutil.which("yt-dlp") or "yt-dlp",
        "-x", "--audio-format", "mp3", "--no-playlist",
        "--user-agent", USER_AGENT,
        "-o", str(work_dir / "source.%(ext)s"), url,
    ]
    process = subprocess.run(command, capture_output=True, text=True, timeout=300)
    if process.returncode != 0:
        detail = process.stderr.strip().splitlines()[-1] if process.stderr else "链接下载失败"
        raise MediaError(detail)
    matches = list(work_dir.glob("source.*"))
    if not matches:
        raise MediaError("下载完成但没有找到媒体文件。")
    return matches[0]


def acquire_url(url: str, work_dir: Path) -> Path:
    platform = _platform(url)
    output = work_dir / "source.mp4"
    if platform in {"xiaohongshu", "douyin", "bilibili"}:
        errors: list[str] = []
        try:
            candidates = _resolve_ai_douyin(url)
        except Exception as exc:
            candidates = []
            errors.append(str(exc))
        for candidate in candidates:
            try:
                return _download_direct(candidate, output)
            except Exception as exc:  # try every returned CDN candidate
                errors.append(str(exc))
        try:
            return _download_ytdlp(url, work_dir)
        except Exception as exc:
            errors.append(str(exc))
        raise MediaError("平台暂时不允许直接下载，请保存视频后使用“上传文件”。详情：" + "; ".join(errors[-2:]))

    return _download_ytdlp(url, work_dir)


def prepare_audio(source: Path, work_dir: Path) -> Path:
    if source.suffix.lower() in {".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg"}:
        return source
    output = work_dir / "audio.m4a"
    command = [
        shutil.which("ffmpeg") or "ffmpeg", "-y", "-i", str(source),
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "aac", "-b:a", "64k", str(output),
    ]
    process = subprocess.run(command, capture_output=True, text=True, timeout=300)
    if process.returncode != 0:
        raise MediaError("无法从视频提取音频，请确认文件包含声音。")
    return output
