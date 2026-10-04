"""Environment-driven settings for the statcard web backend."""

import os
from dataclasses import dataclass

DEFAULT_ALLOWED_ORIGINS = (
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
)


@dataclass(frozen=True)
class Settings:
    """Runtime config for the FastAPI app (docs/INFRASTRUCTURE.md §8)."""

    cache_ttl_seconds: int = 60 * 60
    rate_per_min: int = 3
    rate_global_per_min: int = 20
    allowed_origins: tuple[str, ...] = DEFAULT_ALLOWED_ORIGINS


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def load_settings() -> Settings:
    """Build Settings from environment variables with safe defaults."""
    origins_raw = os.getenv("ALLOWED_ORIGINS", "").strip()
    origins = tuple(o.strip() for o in origins_raw.split(",") if o.strip())
    return Settings(
        cache_ttl_seconds=_env_int("WEB_CACHE_TTL", 60 * 60),
        rate_per_min=_env_int("RATE_LIMIT_PER_MIN", 3),
        rate_global_per_min=_env_int("RATE_LIMIT_GLOBAL_PER_MIN", 20),
        allowed_origins=origins or DEFAULT_ALLOWED_ORIGINS,
    )
