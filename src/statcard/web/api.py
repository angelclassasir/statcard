"""HTTP API routes: Valorant stat cards as PNG or JSON."""

import hashlib
import io
import logging
from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from starlette.concurrency import run_in_threadpool

from statcard.models import PlayerStats
from statcard.providers.valorant import (
    VALID_REGIONS,
    ValorantAuthError,
    ValorantNotFoundError,
    ValorantProviderError,
    ValorantRateLimitedError,
    fetch_valorant_stats,
)
from statcard.render import render_card

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


@dataclass(frozen=True)
class ValorantQuery:
    """Validated path/query parameters for a Valorant card."""

    name: str
    tag: str
    region: str


def _split_riot_id(riot_id: str) -> tuple[str, str]:
    """Validate the Name#TAG shape, raising HTTP 400 when malformed."""
    name, sep, tag = riot_id.partition("#")
    if not sep or not name.strip() or not tag.strip():
        raise HTTPException(400, detail='Malformed Riot ID: expected "Name#TAG".')
    return name.strip(), tag.strip()


def _check_region(region: str) -> str:
    """Validate the region against the provider allow-list (400 otherwise)."""
    normalized = region.strip().lower()
    if normalized not in VALID_REGIONS:
        valid = ", ".join(VALID_REGIONS)
        raise HTTPException(400, detail=f"Unknown region '{region}'. Valid: {valid}.")
    return normalized


def _valorant_query(riot_id: str, region: str = "eu") -> ValorantQuery:
    """Validate before the rate limiter runs, so 400s do not consume quota."""
    name, tag = _split_riot_id(riot_id)
    return ValorantQuery(name=name, tag=tag, region=_check_region(region))


def _client_ip(request: Request) -> str:
    """Return the client IP, trusting only the last X-Forwarded-For hop.

    Render's edge proxy appends the real client IP to any header the client
    sent, so the rightmost value is the only one we can trust. This is an
    abuse deterrent, not an authentication boundary: the global cap is the
    hard ceiling.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        candidate = forwarded.split(",")[-1].strip()
        if candidate:
            return candidate
    return request.client.host if request.client else "unknown"


def _rate_limit(request: Request) -> None:
    """Dependency enforcing the per-IP and global sliding-window caps."""
    settings = request.app.state.settings
    retry = request.app.state.limiter.check(
        _client_ip(request), settings.rate_per_min, settings.rate_global_per_min
    )
    if retry is not None:
        seconds = max(1, int(retry))
        raise HTTPException(
            status_code=429,
            detail={"message": "Rate limit exceeded.", "retry_after": seconds},
            headers={"Retry-After": str(seconds)},
        )


def _provider_error(exc: ValorantProviderError) -> HTTPException:
    """Map provider failures onto the HTTP contract (INFRASTRUCTURE.md §4)."""
    if isinstance(exc, ValorantNotFoundError):
        return HTTPException(404, detail="Player not found on that region.")
    if isinstance(exc, ValorantRateLimitedError):
        return HTTPException(503, detail="Upstream rate limited, try again soon.")
    if isinstance(exc, ValorantAuthError):
        return HTTPException(500, detail="Server misconfiguration.")
    return HTTPException(502, detail="Upstream unavailable.")


async def _fetch_stats(request: Request, query: ValorantQuery) -> PlayerStats:
    settings = request.app.state.settings
    try:
        return await fetch_valorant_stats(
            query.name,
            query.tag,
            region=query.region,
            use_cache=True,
            cache_ttl_seconds=settings.cache_ttl_seconds,
        )
    except ValorantProviderError as exc:
        logger.warning(
            "Provider error for %s#%s (%s): %s",
            query.name,
            query.tag,
            query.region,
            exc,
        )
        raise _provider_error(exc) from exc


@router.get("/valorant/{riot_id}")
async def valorant_card(
    request: Request,
    query: Annotated[ValorantQuery, Depends(_valorant_query)],
    _limit: Annotated[None, Depends(_rate_limit)],
) -> Response:
    """Render the stat card and return it as a cached PNG."""
    stats = await _fetch_stats(request, query)
    image = await run_in_threadpool(render_card, stats)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    content = buffer.getvalue()

    etag = f'"{hashlib.sha256(content).hexdigest()[:32]}"'
    ttl = request.app.state.settings.cache_ttl_seconds
    headers = {"Cache-Control": f"public, max-age={ttl}", "ETag": etag}

    if etag in {tag.strip() for tag in request.headers.get("if-none-match", "").split(",")}:
        return Response(status_code=304, headers=headers)

    return Response(content=content, media_type="image/png", headers=headers)


@router.get("/valorant/{riot_id}/json")
async def valorant_json(
    request: Request,
    query: Annotated[ValorantQuery, Depends(_valorant_query)],
    _limit: Annotated[None, Depends(_rate_limit)],
) -> dict:
    """Return the parsed stats as JSON (debug + future bot reuse)."""
    stats = await _fetch_stats(request, query)
    return stats.model_dump(mode="json")
