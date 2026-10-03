"""Offline tests for the Valorant provider and the renderer.

These tests never touch the network: they replay the saved fixtures.
"""

import json
from pathlib import Path

from PIL import Image

from statcard.models import PlayerStats
from statcard.providers.valorant import parse_stats
from statcard.render import render_card
from statcard.themes import dark as theme

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _stats() -> PlayerStats:
    payloads = {
        "account": _load("valorant_account.json"),
        "mmr": _load("valorant_mmr.json"),
        "matches": _load("valorant_matches.json"),
    }
    return parse_stats(payloads, "Horcus", "1995")


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


def test_parse_stats_kd_is_positive():
    stats = _stats()
    assert stats.kd_ratio > 0
    assert stats.kd_scope in {"SEASON", "RECENT"}


def test_parse_stats_recent_matches_are_competitive():
    stats = _stats()
    assert len(stats.recent_matches) >= 5
    for match in stats.recent_matches:
        assert match["map"]
        assert match["won"] in {True, False}


def test_render_card_geometry():
    img = render_card(_stats())
    assert isinstance(img, Image.Image)
    assert img.size == (theme.CARD_WIDTH, theme.CARD_HEIGHT)
