from __future__ import annotations

import re
from pathlib import Path

from .config import settings


class TranscriptionError(RuntimeError):
    pass


def _clean_copy(text: str) -> str:
    text = re.sub(r"\s+", "", text).strip()
    text = re.sub(r"^(嗯+|呃+|啊+)[，,。.!！?？]*", "", text)
    text = re.sub(r"([。！？!?]){2,}", r"\1", text)
    text = re.sub(r"([。！？])", r"\1\n\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _looks_like_loop(text: str) -> bool:
    compact = re.sub(r"\s+", "", text)
    if len(compact) < 12:
        return False
    # 只拦截模型在音乐/静音上产生的“大段循环幻听”。正常访谈中即使
    # 某句话偶尔重复，也不应被整篇丢弃；循环内容必须覆盖全文 60% 以上。
    for match in re.finditer(r"(.{2,20}?)(?:\1){4,}", compact):
        if len(match.group(0)) / len(compact) >= 0.60:
            return True
    return False


def transcribe(audio: Path) -> str:
    try:
        import mlx_whisper
    except ImportError as exc:
        raise TranscriptionError("MLX Whisper 尚未安装，请重新运行 start.sh 完成安装。") from exc

    result = mlx_whisper.transcribe(
        str(audio),
        path_or_hf_repo=settings.model,
        language="zh",
        task="transcribe",
        fp16=True,
        verbose=None,
        condition_on_previous_text=True,
        no_speech_threshold=0.5,
        logprob_threshold=-0.8,
        hallucination_silence_threshold=1.5,
    )
    text = str(result.get("text", "")).strip()
    if not text:
        raise TranscriptionError("没有识别到有效人声。")
    if _looks_like_loop(text):
        raise TranscriptionError("这段音频主要是音乐或环境声，没有识别到可靠口播。")
    return _clean_copy(text)
