"""Offline tests for the Valorant provider and the renderer.

These tests never touch the network: they replay the saved fixtures.
"""

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from statcard import cache
from statcard.models import PlayerStats
from statcard.providers import valorant as provider
from statcard.providers.valorant import parse_stats

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _payloads() -> dict:
    return {
        "account": _load("valorant_account.json"),
        "mmr": _load("valorant_mmr.json"),
        "matches": _load("valorant_matches.json"),
    }


def _stats() -> PlayerStats:
    return parse_stats(_payloads(), "Horcus", "1995")


def test_parse_stats_basic_fields():
    stats = _stats()
    assert stats.game == "valorant"
    assert stats.player_name == "Horcus"
    assert stats.current_rank == "Immortal 3"
    assert stats.peak_rank == "Radiant"
    assert stats.level == 1375
    assert stats.win_rate == 50.7
    assert stats.total_matches == 140
    assert stats.wins == 71
    assert stats.losses == 69


def test_parse_stats_kd_is_positive():
    stats = _stats()
    assert stats.kd_ratio > 0
    assert stats.kd_scope in {"SEASON", "RECENT"}


def test_parse_stats_kills_and_deaths_match_the_kd_scope():
    stats = _stats()
    assert stats.deaths > 0
    assert round(stats.kills / stats.deaths, 2) == stats.kd_ratio


def test_parse_stats_recent_matches_are_competitive():
    stats = _stats()
    assert len(stats.recent_matches) >= 5
    for match in stats.recent_matches:
        assert match["map"]
        assert match["won"] in {True, False}


def test_parse_stats_uses_the_fetch_timestamp():
    fetched_at = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)
    stats = parse_stats(_payloads(), "Horcus", "1995", fetched_at=fetched_at)
    assert stats.last_updated == fetched_at


def test_slim_payloads_drops_round_history_and_kill_feed():
    payloads = _payloads()
    slim = provider._slim_payloads(payloads)

    full_size = len(json.dumps(payloads))
    slim_size = len(json.dumps(slim))
    assert slim_size < full_size / 10

    match = slim["matches"]["data"][0]
    assert "kills" not in match
    assert "rounds" not in match
    assert match["players"]["all_players"]

    # The trimmed payload must still feed the parser.
    stats = parse_stats(slim, "Horcus", "1995")
    assert stats.kd_ratio > 0
    assert len(stats.recent_matches) >= 5


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, provider.ValorantAuthError),
        (404, provider.ValorantNotFoundError),
        (429, provider.ValorantRateLimitedError),
        (500, provider.ValorantProviderError),
    ],
)
def test_upstream_status_maps_to_specific_error(status, expected, monkeypatch):
    monkeypatch.setenv("HENRIKDEV_API_KEY", "test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json={"status": status})

    async def call() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            await provider._get_json(client, "/v1/account/Name/TAG")

    with pytest.raises(expected):
        asyncio.run(call())


def test_missing_api_key_raises_auth_error(monkeypatch):
    monkeypatch.delenv("HENRIKDEV_API_KEY", raising=False)
    with pytest.raises(provider.ValorantAuthError):
        provider._auth_headers()


def test_fresh_fetch_and_cache_hit_share_the_same_timestamp(tmp_path, monkeypatch):
    """The card footer (and therefore the PNG ETag) must not change on a hit."""
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)
    payloads = _payloads()

    async def fake_get_json(client, path):
        if "/account/" in path:
            return payloads["account"]
        if "/mmr/" in path:
            return payloads["mmr"]
        return payloads["matches"]

    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    monkeypatch.setattr(provider, "_get_json", fake_get_json)
    monkeypatch.setattr(provider.httpx, "AsyncClient", lambda **kwargs: DummyClient())

    first = asyncio.run(provider.fetch_valorant_stats("Horcus", "1995"))
    second = asyncio.run(provider.fetch_valorant_stats("Horcus", "1995"))

    assert first.last_updated == second.last_updated
    assert first.kd_ratio == second.kd_ratio
