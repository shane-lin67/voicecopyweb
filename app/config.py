from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
TOKEN_FILE = ROOT / ".access_token"
SKILL_ENV = Path.home() / ".codex/skills/video-to-subtitle-summary/.env"


def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _access_token() -> str:
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text(encoding="utf-8").strip()
    token = secrets.token_urlsafe(8)
    TOKEN_FILE.write_text(token, encoding="utf-8")
    TOKEN_FILE.chmod(0o600)
    return token


@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("VCW_HOST", "0.0.0.0")
    port: int = int(os.getenv("VCW_PORT", "8765"))
    model: str = os.getenv("VCW_MODEL", "mlx-community/whisper-small-mlx")
    max_upload_mb: int = int(os.getenv("VCW_MAX_UPLOAD_MB", "500"))
    token: str = _access_token()
    skill_env: dict[str, str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        object.__setattr__(self, "skill_env", _load_env_file(SKILL_ENV))
        DATA_DIR.mkdir(exist_ok=True)


settings = Settings()

