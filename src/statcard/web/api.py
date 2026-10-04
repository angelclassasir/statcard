"""HTTP API routes: Valorant stat cards as PNG or JSON."""

import io

from fastapi import APIRouter, Depends, HTTPException, Request, Response

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

router = APIRouter(prefix="/api")


def _split_riot_id(riot_id: str) -> tuple[str, str]:
    """Validate the Name#TAG shape, raising HTTP 400 when malformed."""
    name, sep, tag = riot_id.partition("#")
    if not sep or not name.strip() or not tag.strip():
        raise HTTPException(400, detail='Malformed Riot ID: expected "Name#TAG".')
    return name.strip(), tag.strip()


def _check_region(region: str) -> str:
    """Validate the region against the provider allow-list (400 otherwise)."""
    if region not in VALID_REGIONS:
        valid = ", ".join(VALID_REGIONS)
        raise HTTPException(400, detail=f"Unknown region '{region}'. Valid: {valid}.")
    return region


def _rate_limit(request: Request) -> None:
    """Dependency enforcing the per-IP and global sliding-window caps."""
    settings = request.app.state.settings
    forwarded = request.headers.get("x-forwarded-for", "")
    client = request.client.host if request.client else "unknown"
    ip = forwarded.split(",")[0].strip() or client
    retry = request.app.state.limiter.check(
        ip, settings.rate_per_min, settings.rate_global_per_min
    )
    if retry is not None:
        seconds = int(retry)
        raise HTTPException(
            status_code=429,
            detail={"message": "Rate limit exceeded.", "retry_after": seconds},
            headers={"Retry-After": str(seconds)},
        )


def _provider_error(exc: ValorantProviderError) -> HTTPException:
    """Map provider failures onto the HTTP contract (INFRASTRUCTURE.md §4)."""
    if isinstance(exc, ValorantNotFoundError):
        return HTTPException(404, detail=str(exc))
    if isinstance(exc, ValorantRateLimitedError):
        return HTTPException(503, detail="Upstream rate limited, try again soon.")
    if isinstance(exc, ValorantAuthError):
        return HTTPException(500, detail="Server misconfiguration.")
    return HTTPException(502, detail="Upstream unavailable.")


async def _fetch_stats(request: Request, name: str, tag: str, region: str) -> PlayerStats:
    ttl = request.app.state.settings.cache_ttl_seconds
    try:
        return await fetch_valorant_stats(
            name, tag, region=region, use_cache=True, cache_ttl_seconds=ttl
        )
    except ValorantProviderError as exc:
        raise _provider_error(exc) from exc


@router.get("/valorant/{riot_id}")
async def valorant_card(
    riot_id: str,
    request: Request,
    region: str = "eu",
    _limit: None = Depends(_rate_limit),
) -> Response:
    """Render the stat card and return it as a cached PNG."""
    name, tag = _split_riot_id(riot_id)
    region = _check_region(region)
    stats = await _fetch_stats(request, name, tag, region)
    buffer = io.BytesIO()
    render_card(stats).save(buffer, format="PNG")
    ttl = request.app.state.settings.cache_ttl_seconds
    return Response(
        content=buffer.getvalue(),
        media_type="image/png",
        headers={"Cache-Control": f"public, max-age={ttl}"},
    )


@router.get("/valorant/{riot_id}/json")
async def valorant_json(
    riot_id: str,
    request: Request,
    region: str = "eu",
    _limit: None = Depends(_rate_limit),
) -> dict:
    """Return the parsed stats as JSON (debug + future bot reuse)."""
    name, tag = _split_riot_id(riot_id)
    region = _check_region(region)
    stats = await _fetch_stats(request, name, tag, region)
    return stats.model_dump(mode="json")
