"""Valorant provider: HenrikDev API -> common PlayerStats format."""

import os
from datetime import datetime
from typing import Any

import httpx
from dotenv import load_dotenv

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
    response = await client.get(f"{HENRIKDEV_BASE_URL}{path}", headers=_auth_headers())
    response.raise_for_status()
    return response.json()


async def fetch_raw_payloads(name: str, tag: str, region: str = "eu") -> dict[str, Any]:
    """Fetch raw JSON payloads (account, MMR, matches) without parsing them.

    Kept separate from parsing so tests can save these payloads as fixtures.
    """
    if region not in VALID_REGIONS:
        raise ValorantProviderError(
            f"Unknown region '{region}'. Valid regions: {', '.join(VALID_REGIONS)}"
        )

    async with httpx.AsyncClient(timeout=30.0) as client:
        account = await _get_json(client, f"/v1/account/{name}/{tag}")
        mmr = await _get_json(client, f"/v3/mmr/{region}/{PLATFORM}/{name}/{tag}")
        matches = await _get_json(client, f"/v3/matches/{region}/{name}/{tag}?size=10")

    return {"account": account, "mmr": mmr, "matches": matches}


def _parse_recent_matches(
    payload: dict[str, Any], name: str, tag: str
) -> list[dict[str, Any]]:
    """Convert raw v3 matches into the simplified common match structure."""
    matches = payload.get("data") or []
    recent: list[dict[str, Any]] = []

    for match in matches:
        metadata = match.get("metadata") or {}
        teams = match.get("teams") or {}
        all_players = (match.get("players") or {}).get("all_players") or []

        # Locate the requested player inside the match roster
        own = next(
            (p for p in all_players if p.get("name") == name and p.get("tag") == tag),
            None,
        )
        if own is None:
            continue

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
    if not account:
        raise ValorantProviderError(
            f"Player '{name}#{tag}' not found (account endpoint returned no data)."
        )

    # NOTE: HenrikDev can send explicit nulls ("data": null) on some failures.
    # dict.get(key, default) only applies the default when the key is MISSING,
    # so we use `or {}` / `or []` to also replace null values with empty ones.
    mmr = payloads["mmr"].get("data") or {}
    current = mmr.get("current") or {}
    peak = mmr.get("peak") or {}
    seasonal = mmr.get("seasonal") or []

    current_rank = (current.get("tier") or {}).get("name") or "Unranked"
    peak_rank = (peak.get("tier") or {}).get("name") or "Unranked"

    # Win rate comes from the most recent competitive season entry
    season = seasonal[0] if seasonal else {}
    wins = season.get("wins") or 0
    games = season.get("games") or 0
    win_rate = round(wins / games * 100, 1) if games else 0.0

    recent_matches = _parse_recent_matches(payloads["matches"], name, tag)

    # K/D aggregated over the fetched recent matches (not career-wide yet)
    kills = sum(m["kills"] for m in recent_matches)
    deaths = sum(m["deaths"] for m in recent_matches)
    kd_ratio = round(kills / deaths, 2) if deaths else 0.0

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
        kills=kills,
        deaths=deaths,
        kd_ratio=kd_ratio,
        recent_matches=recent_matches,
        last_updated=datetime.now(),
    )


async def fetch_valorant_stats(name: str, tag: str, region: str = "eu") -> PlayerStats:
    """Public entry point: fetch and parse Valorant stats for one player."""
    payloads = await fetch_raw_payloads(name, tag, region=region)
    return parse_stats(payloads, name, tag)