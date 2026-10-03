"""Disk cache with expiration for API payloads."""

import hashlib
import json
import time
from pathlib import Path
from typing import Any

# Repository root / .cache folder (git-ignored)
CACHE_DIR = Path(__file__).resolve().parents[2] / ".cache"

DEFAULT_TTL_SECONDS = 10 * 60  # 10 minutes


def _cache_path(key: str) -> Path:
    """Map a cache key to a safe filename (player names can use any script)."""
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{digest}.json"


def get(key: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> Any | None:
    """Return the cached payload if present and fresh, else None."""
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        blob = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - float(blob.get("saved_at", 0)) > ttl_seconds:
            return None  # expired entry
        return blob.get("payload")
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None  # corrupted cache file: treat it as a miss


def set(key: str, payload: Any) -> None:
    """Store a payload in the cache with a timestamp."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    blob = {"saved_at": time.time(), "payload": payload}
    _cache_path(key).write_text(
        json.dumps(blob, ensure_ascii=False), encoding="utf-8"
    )