"""Valorant provider: HenrikDev API -> common PlayerStats format."""

import asyncio
import logging
import os
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

import httpx
from dotenv import load_dotenv

from statcard import cache
from statcard.models import PlayerStats

load_dotenv()

HENRIKDEV_BASE_URL = os.getenv("HENRIKDEV_BASE_URL", "https://api.henrikdev.xyz/valorant")

# Regions (affinities) accepted by the HenrikDev API
VALID_REGIONS = ("eu", "na", "ap", "kr", "br", "latam")

# Platform used by the MMR v3 endpoint
PLATFORM = "pc"

# The three upstream calls run in parallel, so a generous read timeout is cheap.
REQUEST_TIMEOUT = httpx.Timeout(30.0, connect=10.0)

CACHE_TTL_SECONDS = 10 * 60

logger = logging.getLogger(__name__)


class ValorantProviderError(Exception):
    """Raised when the API returns unexpected or missing data."""


class ValorantAuthError(ValorantProviderError):
    """HenrikDev rejected the API key (401) or the key is missing."""


class ValorantNotFoundError(ValorantProviderError):
    """The requested player does not exist (404)."""


class ValorantRateLimitedError(ValorantProviderError):
    """HenrikDev rate-limited us (429)."""


def _auth_headers() -> dict[str, str]:
    """Return authorization headers, failing early if the key is missing.

    The environment is read on every call (instead of at import time) so tests
    and long-running processes can pick up a rotated key.
    """
    key = os.getenv("HENRIKDEV_API_KEY", "").strip()
    if not key:
        raise ValorantAuthError(
            "HENRIKDEV_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return {"Authorization": key}


async def _get_json(client: httpx.AsyncClient, path: str) -> dict[str, Any]:
    """Perform a GET request against HenrikDev and return the parsed JSON body."""
    url = f"{HENRIKDEV_BASE_URL}{path}"
    try:
        response = await client.get(url, headers=_auth_headers())
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        logger.warning("HenrikDev returned %s for %s", status, path)
        if status == 401:
            raise ValorantAuthError(
                "HenrikDev rejected the API key (401). Check HENRIKDEV_API_KEY in .env."
            ) from exc
        if status == 404:
            raise ValorantNotFoundError("Player not found on HenrikDev (404).") from exc
        if status == 429:
            raise ValorantRateLimitedError(
                "Rate limit reached on HenrikDev (429). Wait a minute or rely on the cache."
            ) from exc
        raise ValorantProviderError(f"HenrikDev API error ({status}) for {path}") from exc
    except httpx.RequestError as exc:
        raise ValorantProviderError(
            "Could not reach the HenrikDev API (network down or blocked)."
        ) from exc

    try:
        return response.json()
    except ValueError as exc:
        raise ValorantProviderError("HenrikDev returned a non-JSON response.") from exc


# --- Payload slimming -------------------------------------------------------
#
# The matches endpoint returns the full round history and kill feed for every
# game: ~96% of the payload. The renderer only needs a handful of fields, so
# we trim before caching. This keeps cache entries at a few hundred KB instead
# of ~90 MB per player and makes cache hits fast.

_METADATA_FIELDS = ("map", "mode", "queue", "season_id", "game_start_patched")


def _slim_player(player: dict[str, Any]) -> dict[str, Any]:
    """Keep only the player fields used by the parser."""
    stats = player.get("stats") or {}
    return {
        "puuid": player.get("puuid"),
        "name": player.get("name"),
        "tag": player.get("tag"),
        "riot_id": player.get("riot_id"),
        "team": player.get("team"),
        "character": player.get("character"),
        "stats": {"kills": stats.get("kills", 0), "deaths": stats.get("deaths", 0)},
    }


def _slim_match(match: dict[str, Any]) -> dict[str, Any]:
    """Drop round history, kill feed and unused player fields from one match."""
    metadata = match.get("metadata") or {}
    players = match.get("players") or {}
    teams = match.get("teams") or {}

    roster = players.get("all_players") or []
    if not roster:
        # Legacy schema used allies/enemies; normalize it to all_players.
        roster = (players.get("allies") or []) + (players.get("enemies") or [])

    return {
        "metadata": {field: metadata.get(field) for field in _METADATA_FIELDS},
        "players": {"all_players": [_slim_player(player) for player in roster]},
        "teams": {
            side: {
                "has_won": (team or {}).get("has_won"),
                "rounds_won": (team or {}).get("rounds_won"),
                "rounds_lost": (team or {}).get("rounds_lost"),
            }
            for side, team in teams.items()
        },
    }


def _slim_mmr(payload: dict[str, Any]) -> dict[str, Any]:
    """Keep current/peak tiers and the first seasonal entries (used for W/L)."""
    data = payload.get("data") or {}
    current = data.get("current") or {}
    peak = data.get("peak") or {}

    seasonal = []
    for entry in (data.get("seasonal") or [])[:3]:
        season = entry.get("season") or {}
        seasonal.append(
            {
                "season": {"id": season.get("id"), "short": season.get("short")},
                "wins": entry.get("wins") or 0,
                "games": entry.get("games") or 0,
            }
        )

    return {
        "status": payload.get("status"),
        "data": {
            "current": {"tier": {"name": (current.get("tier") or {}).get("name")}},
            "peak": {"tier": {"name": (peak.get("tier") or {}).get("name")}},
            "seasonal": seasonal,
        },
    }


def _slim_payloads(payloads: dict[str, Any]) -> dict[str, Any]:
    """Trim every upstream payload down to the fields parse_stats() reads."""
    matches = payloads["matches"]
    return {
        "account": payloads["account"],
        "mmr": _slim_mmr(payloads["mmr"]),
        "matches": {
            "status": matches.get("status"),
            "data": [_slim_match(match) for match in (matches.get("data") or [])],
        },
    }


# --- Fetching ---------------------------------------------------------------


async def _fetch_payloads_with_metadata(
    name: str,
    tag: str,
    region: str = "eu",
    use_cache: bool = True,
    cache_ttl_seconds: int | None = None,
) -> tuple[dict[str, Any], datetime]:
    """Fetch (or read from cache) the payloads plus the time they were fetched."""
    name, tag = name.strip(), tag.strip()

    if not name or not tag:
        raise ValorantProviderError("Both the Riot name and the tag are required.")
    if region not in VALID_REGIONS:
        raise ValorantProviderError(
            f"Unknown region '{region}'. Valid regions: {', '.join(VALID_REGIONS)}"
        )

    cache_key = f"valorant:{region}:{name.lower()}#{tag.lower()}"
    ttl = CACHE_TTL_SECONDS if cache_ttl_seconds is None else cache_ttl_seconds
    if use_cache:
        hit = cache.get_with_metadata(cache_key, ttl)
        if hit is not None:
            payloads, saved_at = hit
            return payloads, datetime.fromtimestamp(saved_at, UTC)

    # The three endpoints are independent: run them concurrently.
    name_q, tag_q = quote(name, safe=""), quote(tag, safe="")
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        account, mmr, matches = await asyncio.gather(
            _get_json(client, f"/v1/account/{name_q}/{tag_q}"),
            _get_json(client, f"/v3/mmr/{region}/{PLATFORM}/{name_q}/{tag_q}"),
            _get_json(
                client,
                f"/v3/matches/{region}/{name_q}/{tag_q}?size=100&mode=Competitive",
            ),
        )

    payloads = _slim_payloads({"account": account, "mmr": mmr, "matches": matches})
    saved_at = cache.set(cache_key, payloads)
    # Reuse the cache timestamp so this response renders byte-identical to a
    # later cache hit (important for ETag stability).
    return payloads, datetime.fromtimestamp(saved_at, UTC)


async def fetch_raw_payloads(
    name: str,
    tag: str,
    region: str = "eu",
    use_cache: bool = True,
    cache_ttl_seconds: int | None = None,
) -> dict[str, Any]:
    """Return the provider payloads (trimmed to the fields the parser needs).

    Kept as a public entry point for scripts and future providers; the name is
    historical, the payload is no longer the complete upstream JSON.
    """
    payloads, _ = await _fetch_payloads_with_metadata(
        name,
        tag,
        region=region,
        use_cache=use_cache,
        cache_ttl_seconds=cache_ttl_seconds,
    )
    return payloads


def _is_competitive(match: dict[str, Any]) -> bool:
    """Keep only competitive matches (skip deathmatch, unrated, swiftplay...)."""
    metadata = match.get("metadata") or {}
    mode = (metadata.get("mode") or metadata.get("queue") or "").lower()
    # If the field is missing entirely, give the match the benefit of the doubt
    return not mode or mode == "competitive"


def _find_own_entry(
    match: dict[str, Any], puuid: str | None, name: str, tag: str
) -> dict[str, Any] | None:
    """Locate the requested player inside a match roster.

    Tries puuid first (stable identifier), then exact name+tag, then a
    case-insensitive name match. Supports both the v3 schema (all_players)
    and the older one (allies/enemies with riot_id).
    """
    players = match.get("players") or {}
    roster = players.get("all_players") or []
    if not roster:
        roster = (players.get("allies") or []) + (players.get("enemies") or [])

    def entry_name_tag(p: dict[str, Any]) -> tuple[Any, Any]:
        if p.get("name") is not None:
            return p.get("name"), p.get("tag")
        riot = p.get("riot_id") or {}
        return riot.get("game_name"), riot.get("tag_line")

    if puuid:
        own = next((p for p in roster if p.get("puuid") == puuid), None)
        if own is not None:
            return own

    own = next((p for p in roster if entry_name_tag(p) == (name, tag)), None)
    if own is not None:
        return own

    return next(
        (p for p in roster if (entry_name_tag(p)[0] or "").lower() == name.lower()),
        None,
    )


def _parse_recent_matches(
    payload: dict[str, Any], puuid: str | None, name: str, tag: str
) -> list[dict[str, Any]]:
    """Convert raw v3 matches into the simplified common match structure."""
    matches = payload.get("data") or []
    recent: list[dict[str, Any]] = []

    for match in matches:
        if not _is_competitive(match):
            continue
        own = _find_own_entry(match, puuid, name, tag)
        if own is None:
            continue

        metadata = match.get("metadata") or {}
        teams = match.get("teams") or {}
        own_team = (own.get("team") or "").lower()
        team_stats = teams.get(own_team) or {}
        stats = own.get("stats") or {}

        recent.append(
            {
                "map": metadata.get("map", "Unknown"),
                "mode": metadata.get("mode", "Unknown"),
                "start": metadata.get("game_start_patched", ""),
                "agent": own.get("character", "Unknown"),
                "won": team_stats.get("has_won"),
                "rounds_won": team_stats.get("rounds_won"),
                "rounds_lost": team_stats.get("rounds_lost"),
                "kills": stats.get("kills", 0),
                "deaths": stats.get("deaths", 0),
            }
        )

    return recent


def parse_stats(
    payloads: dict[str, Any],
    name: str,
    tag: str,
    fetched_at: datetime | None = None,
) -> PlayerStats:
    """Map raw HenrikDev payloads into the common PlayerStats model.

    ``fetched_at`` is the time the payloads were retrieved (a cache hit reports
    the original fetch time, not the current one).
    """
    account = payloads["account"].get("data")
    name, tag = name.strip(), tag.strip()
    if not account:
        raise ValorantNotFoundError(
            f"Player '{name}#{tag}' not found (account endpoint returned no data)."
        )

    puuid = account.get("puuid")

    mmr = payloads["mmr"].get("data") or {}
    current = mmr.get("current") or {}
    peak = mmr.get("peak") or {}
    seasonal = mmr.get("seasonal") or []

    current_rank = (current.get("tier") or {}).get("name") or "Unranked"
    peak_rank = (peak.get("tier") or {}).get("name") or "Unranked"

    # Current season stats (wins, games, season_id)
    season = seasonal[0] if seasonal else {}
    wins = season.get("wins") or 0
    games = season.get("games") or 0
    win_rate = round(wins / games * 100, 1) if games else 0.0

    # Season identifiers can come in different formats depending on the
    # endpoint (full UUID vs short code), so compare against all of them.
    season_ids = {
        (season.get("season") or {}).get("id"),
        (season.get("season") or {}).get("short"),
    }
    season_ids.discard(None)

    # Season K/D over the fetched competitive matches; if the season
    # identifiers never match (API format quirks), fall back to all the
    # fetched competitive matches so the card still shows a real K/D.
    season_kills = 0
    season_deaths = 0
    fallback_kills = 0
    fallback_deaths = 0
    for match in payloads["matches"].get("data") or []:
        if not _is_competitive(match):
            continue
        own = _find_own_entry(match, puuid, name, tag)
        if own is None:
            continue
        stats = own.get("stats") or {}
        kills = stats.get("kills", 0)
        deaths = stats.get("deaths", 0)
        fallback_kills += kills
        fallback_deaths += deaths
        if (match.get("metadata") or {}).get("season_id") in season_ids:
            season_kills += kills
            season_deaths += deaths

    if season_deaths:
        kd_ratio = round(season_kills / season_deaths, 2)
        kd_scope = "SEASON"
        total_kills, total_deaths = season_kills, season_deaths
    elif fallback_deaths:
        kd_ratio = round(fallback_kills / fallback_deaths, 2)
        kd_scope = "RECENT"
        total_kills, total_deaths = fallback_kills, fallback_deaths
    else:
        kd_ratio = 0.0
        kd_scope = "RECENT"
        total_kills, total_deaths = 0, 0

    recent_matches = _parse_recent_matches(payloads["matches"], puuid, name, tag)

    if fetched_at is not None and fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=UTC)

    return PlayerStats(
        game="valorant",
        player_name=account.get("name", name),
        player_id=f"{account.get('name', name)}#{account.get('tag', tag)}",
        current_rank=current_rank,
        peak_rank=peak_rank,
        level=account.get("account_level") or 0,
        total_matches=games,
        wins=wins,
        win_rate=win_rate,
        kills=total_kills,
        deaths=total_deaths,
        kd_ratio=kd_ratio,
        kd_scope=kd_scope,
        recent_matches=recent_matches,
        last_updated=fetched_at or datetime.now(UTC),
    )


async def fetch_valorant_stats(
    name: str,
    tag: str,
    region: str = "eu",
    use_cache: bool = True,
    cache_ttl_seconds: int | None = None,
) -> PlayerStats:
    """Public entry point: fetch and parse Valorant stats for one player."""
    payloads, fetched_at = await _fetch_payloads_with_metadata(
        name,
        tag,
        region=region,
        use_cache=use_cache,
        cache_ttl_seconds=cache_ttl_seconds,
    )
    return parse_stats(payloads, name, tag, fetched_at=fetched_at)
