"""Valorant provider: HenrikDev API -> common PlayerStats format."""
import os
from datetime import datetime
from typing import Any

import httpx
from dotenv import load_dotenv

from statcard import cache
from statcard.models import PlayerStats

load_dotenv()

HENRIKDEV_API_KEY = os.getenv("HENRIKDEV_API_KEY", "")
HENRIKDEV_BASE_URL = "https://api.henrikdev.xyz/valorant"

# Regions (affinities) accepted by the HenrikDev API
VALID_REGIONS = ("eu", "na", "ap", "kr", "br", "latam")

# Platform used by the MMR v3 endpoint
PLATFORM = "pc"


class ValorantProviderError(Exception):
    """Raised when the API returns unexpected or missing data."""


def _auth_headers() -> dict[str, str]:
    """Return authorization headers, failing early if the key is missing."""
    if not HENRIKDEV_API_KEY:
        raise ValorantProviderError(
            "HENRIKDEV_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return {"Authorization": HENRIKDEV_API_KEY}


async def _get_json(client: httpx.AsyncClient, path: str) -> dict[str, Any]:
    """Perform a GET request against HenrikDev and return the parsed JSON body."""
    url = f"{HENRIKDEV_BASE_URL}{path}"
    try:
        response = await client.get(url, headers=_auth_headers())
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status == 401:
            raise ValorantProviderError(
                "HenrikDev rejected the API key (401). Check HENRIKDEV_API_KEY in .env."
            ) from exc
        if status == 404:
            raise ValorantProviderError(f"Player not found (404): {path}") from exc
        if status == 429:
            raise ValorantProviderError(
                "Rate limit reached (429). Wait a minute or rely on the cache."
            ) from exc
        raise ValorantProviderError(f"HenrikDev API error ({status}) for {path}") from exc
    except httpx.RequestError as exc:
        raise ValorantProviderError(
            "Could not reach the HenrikDev API (network down or blocked)."
        ) from exc
    return response.json()

CACHE_TTL_SECONDS = 10 * 60

async def fetch_raw_payloads(
    name: str, tag: str, region: str = "eu", use_cache: bool = True
) -> dict[str, Any]:
    """Fetch raw JSON payloads (account, MMR, matches, lifetime) with disk cache."""
    name, tag = name.strip(), tag.strip()

    if region not in VALID_REGIONS:
        raise ValorantProviderError(
            f"Unknown region '{region}'. Valid regions: {', '.join(VALID_REGIONS)}"
        )

    cache_key = f"valorant:{region}:{name.lower()}#{tag.lower()}"
    if use_cache:
        cached = cache.get(cache_key, CACHE_TTL_SECONDS)
        if cached is not None:
            return cached

    async with httpx.AsyncClient(timeout=60.0) as client:
        account = await _get_json(client, f"/v1/account/{name}/{tag}")
        mmr = await _get_json(client, f"/v3/mmr/{region}/{PLATFORM}/{name}/{tag}")
        # One bigger competitive-only request feeds both the recent strip
        # and the season K/D aggregation
        matches = await _get_json(
            client, f"/v3/matches/{region}/{name}/{tag}?size=100&mode=Competitive"
        )

    payloads = {"account": account, "mmr": mmr, "matches": matches}
    cache.set(cache_key, payloads)
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


def parse_stats(payloads: dict[str, Any], name: str, tag: str) -> PlayerStats:
    """Map raw HenrikDev payloads into the common PlayerStats model."""
    account = payloads["account"].get("data")
    name, tag = name.strip(), tag.strip()
    if not account:
        raise ValorantProviderError(
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
    elif fallback_deaths:
        kd_ratio = round(fallback_kills / fallback_deaths, 2)
        kd_scope = "RECENT"
    else:
        kd_ratio = 0.0
        kd_scope = "RECENT"

    recent_matches = _parse_recent_matches(payloads["matches"], puuid, name, tag)

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
        kills=season_kills,
        deaths=season_deaths,
        kd_ratio=kd_ratio,
        kd_scope=kd_scope,
        recent_matches=recent_matches,
        last_updated=datetime.now(),
    )


async def fetch_valorant_stats(
    name: str, tag: str, region: str = "eu", use_cache: bool = True
) -> PlayerStats:
    """Public entry point: fetch and parse Valorant stats for one player."""
    payloads = await fetch_raw_payloads(name, tag, region=region, use_cache=use_cache)
    return parse_stats(payloads, name, tag)
