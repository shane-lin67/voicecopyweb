from __future__ import annotations

import asyncio
import json
import re
import shutil
import socket
import threading
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .config import DATA_DIR, ROOT, settings
from .jobs import event_json, jobs
from .media import acquire_url, prepare_audio
from .transcribe import transcribe


app = FastAPI(title="口播提取器", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=ROOT / "web"), name="static")


def _extract_url(value: str) -> str:
    match = re.search(r"https?://[^\s<>]+", value, flags=re.IGNORECASE)
    if not match:
        return value.strip()
    return match.group(0).rstrip("，。！？、；：）】》」』〉”’\"'")


def _authorized(request: Request, token: str | None) -> bool:
    if request.client and request.client.host in {"127.0.0.1", "::1"}:
        return True
    return bool(token and token == settings.token)


def require_access(request: Request, x_access_token: str | None) -> None:
    if not _authorized(request, x_access_token):
        raise HTTPException(status_code=401, detail="请输入 Mac 启动窗口显示的访问口令。")


@app.exception_handler(Exception)
async def unhandled_error(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": str(exc)}})


@app.get("/")
def index() -> FileResponse:
    return FileResponse(ROOT / "web/index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "engine": "mlx-whisper", "model": settings.model}


def _run_job(job_id: str, source_kind: str, value: str) -> None:
    job = jobs.get(job_id)
    if not job:
        return
    work_dir = DATA_DIR / job_id
    work_dir.mkdir(parents=True, exist_ok=True)
    try:
        if source_kind == "url":
            job.update("正在解析并下载视频", 12)
            source = acquire_url(value, work_dir)
        else:
            source = Path(value)
        job.update("正在提取音频", 32)
        audio = prepare_audio(source, work_dir)
        job.update("Apple 芯片正在识别人声", 48)
        result = transcribe(audio)
        job.update("正在整理文案", 92)
        (work_dir / "result.txt").write_text(result, encoding="utf-8")
        job.complete(result)
    except Exception as exc:
        job.fail(str(exc))


@app.post("/api/jobs")
async def create_job(
    request: Request,
    url: str = Form(default=""),
    file: UploadFile | None = File(default=None),
    x_access_token: str | None = Header(default=None),
) -> dict[str, str]:
    require_access(request, x_access_token)
    url = _extract_url(url)
    if not url and not file:
        raise HTTPException(status_code=422, detail="请粘贴视频链接或选择文件。")
    if url.strip() and file:
        raise HTTPException(status_code=422, detail="链接和文件请选择一种。")

    job = jobs.create()
    if file:
        suffix = Path(file.filename or "upload.mp4").suffix.lower()
        allowed = {".mp4", ".mov", ".mkv", ".webm", ".mp3", ".wav", ".m4a", ".flac", ".aac"}
        if suffix not in allowed:
            raise HTTPException(status_code=415, detail="暂不支持这种文件格式。")
        work_dir = DATA_DIR / job.id
        work_dir.mkdir(parents=True, exist_ok=True)
        target = work_dir / f"upload{suffix}"
        size = 0
        with target.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > settings.max_upload_mb * 1024 * 1024:
                    target.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail=f"文件不能超过 {settings.max_upload_mb}MB。")
                output.write(chunk)
        source_kind, value = "file", str(target)
    else:
        if not url.startswith(("http://", "https://")):
            raise HTTPException(status_code=422, detail="请输入完整的 http 或 https 链接。")
        source_kind, value = "url", url

    threading.Thread(target=_run_job, args=(job.id, source_kind, value), daemon=True).start()
    return {"job_id": job.id}


@app.get("/api/jobs/{job_id}/events")
async def job_events(request: Request, job_id: str, token: str = "") -> StreamingResponse:
    require_access(request, token)
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在。")

    async def stream():
        while True:
            if await request.is_disconnected():
                break
            try:
                event = await asyncio.to_thread(job.events.get, True, 15)
                yield event_json(event)
                if event["type"] in {"complete", "error"}:
                    break
            except Exception:
                yield ": keepalive\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


def _local_ip() -> str:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "这台Mac的局域网IP"
    finally:
        try:
            sock.close()
        except Exception:
            pass


if __name__ == "__main__":
    print("\n口播提取器已启动")
    print(f"电脑打开：http://127.0.0.1:{settings.port}")
    print(f"手机打开：http://{_local_ip()}:{settings.port}")
    print(f"手机访问口令：{settings.token}\n")
    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")
