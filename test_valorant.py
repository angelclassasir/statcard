"""Manual smoke test for the Valorant provider (Phase 1).

Run with: uv run python test_valorant.py
"""

import asyncio
import json
from pathlib import Path

import httpx

from statcard.providers.valorant import (
    ValorantProviderError,
    fetch_raw_payloads,
    parse_stats,
)

# --- Edit these to your own account ---
RIOT_NAME = "DavidNavey고인물"
RIOT_TAG = "ntn"
REGION = "eu"  # one of: eu, na, ap, kr, br, latam

FIXTURES_DIR = Path("tests/fixtures")


async def main() -> None:
    print(f"Fetching stats for {RIOT_NAME}#{RIOT_TAG} (region: {REGION})...\n")

    try:
        payloads = await fetch_raw_payloads(RIOT_NAME, RIOT_TAG, region=REGION)
    except ValorantProviderError as exc:
        print(f"CONFIG/DATA ERROR: {exc}")
        return
    except httpx.HTTPStatusError as exc:
        print(f"HTTP ERROR {exc.response.status_code}: {exc.request.url}")
        return

    # Save raw responses as fixtures for offline tests later
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    for key, payload in payloads.items():
        fixture_path = FIXTURES_DIR / f"valorant_{key}.json"
        fixture_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        has_data = bool(payload.get("data"))
        print(f"[{key:>7}] data={'OK  ' if has_data else 'NULL'} -> {fixture_path}")

    if any(not payload.get("data") for payload in payloads.values()):
        print("\nHint: a NULL 'data' usually means REGION does not match your account.")

    print()
    stats = parse_stats(payloads, RIOT_NAME, RIOT_TAG)

    print("=" * 52)
    print(f"Player : {stats.player_name} ({stats.player_id})")
    print(f"Rank   : {stats.current_rank}  (peak: {stats.peak_rank})")
    print(f"Level  : {stats.level}")
    print(f"Season : {stats.wins}W / {stats.total_matches}G  ({stats.get_win_rate_display()})")
    print(f"K/D    : {stats.kills}K / {stats.deaths}D  ({stats.get_kd_display()}) [recent]")
    print("-" * 52)
    for i, match in enumerate(stats.recent_matches, 1):
        result = "WIN " if match["won"] else "LOSS" if match["won"] is False else "????"
        print(
            f"  {i}. {result} {match['map']:<12} "
            f"{match['rounds_won']}-{match['rounds_lost']}  "
            f"{match['kills']}K/{match['deaths']}D  {match['agent']}"
        )
    print("=" * 52)


if __name__ == "__main__":
    asyncio.run(main())