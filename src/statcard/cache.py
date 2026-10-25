"""Disk cache with expiration for API payloads.

Entries are JSON files keyed by a SHA-1 of the logical key. Writes are atomic
(temp file + rename) and the store evicts the oldest entries when it grows past
a count or size budget, so a long-running web process cannot fill the disk.
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

DEFAULT_TTL_SECONDS = 10 * 60  # 10 minutes

# Eviction budget: enough for hundreds of players, small enough for a free tier.
MAX_ENTRIES = 500
MAX_BYTES = 64 * 1024 * 1024  # 64 MB


def _default_cache_dir() -> Path:
    """Cache lives at the repo root by default; STATCARD_CACHE_DIR overrides it."""
    override = os.getenv("STATCARD_CACHE_DIR", "").strip()
    if override:
        return Path(override).expanduser()
    return Path(__file__).resolve().parents[2] / ".cache"


CACHE_DIR = _default_cache_dir()


def _cache_path(key: str) -> Path:
    """Map a cache key to a safe filename (player names can use any script)."""
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{digest}.json"


def _safe_unlink(path: Path) -> bool:
    """Delete a file, ignoring races and permission errors."""
    try:
        path.unlink()
        return True
    except OSError:
        return False


def _evict_if_needed() -> None:
    """Drop the oldest entries until the store is inside its budget."""
    try:
        entries = [(path, path.stat()) for path in CACHE_DIR.glob("*.json")]
    except OSError:
        return

    total_bytes = sum(stat.st_size for _, stat in entries)
    if len(entries) <= MAX_ENTRIES and total_bytes <= MAX_BYTES:
        return

    entries.sort(key=lambda item: item[1].st_mtime)
    remaining = len(entries)
    for path, stat in entries:
        if remaining <= MAX_ENTRIES and total_bytes <= MAX_BYTES:
            break
        if _safe_unlink(path):
            remaining -= 1
            total_bytes -= stat.st_size


def get_with_metadata(key: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> tuple[Any, float] | None:
    """Return ``(payload, saved_at)`` if the entry is fresh, else None.

    Expired and corrupted entries are removed instead of being left on disk.
    """
    path = _cache_path(key)
    try:
        blob = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError, ValueError):
        _safe_unlink(path)
        return None

    try:
        saved_at = float(blob.get("saved_at", 0))
    except (TypeError, ValueError):
        _safe_unlink(path)
        return None

    payload = blob.get("payload")
    if payload is None or time.time() - saved_at > ttl_seconds:
        _safe_unlink(path)
        return None
    return payload, saved_at


def get(key: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> Any | None:
    """Return the cached payload if present and fresh, else None."""
    hit = get_with_metadata(key, ttl_seconds)
    return hit[0] if hit is not None else None


def set(key: str, payload: Any) -> float:
    """Store a payload atomically and return the timestamp saved with it.

    Callers can reuse the returned timestamp (instead of ``time.time()``) so a
    freshly fetched payload and a later cache hit render identical output.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    saved_at = time.time()
    blob = {"saved_at": saved_at, "payload": payload}
    path = _cache_path(key)

    # Write next to the target so os.replace() stays on the same filesystem.
    tmp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(json.dumps(blob, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            _safe_unlink(tmp_path)

    _evict_if_needed()
    return saved_at
