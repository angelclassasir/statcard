"""Offline tests for the card renderer (layout, paths, long strings)."""

from datetime import UTC, datetime

from statcard.models import PlayerStats
from statcard.render import render_card, save_card
from statcard.themes import dark as theme


def _stats(**overrides) -> PlayerStats:
    data = {
        "game": "valorant",
        "player_name": "Horcus",
        "player_id": "Horcus#1995",
        "current_rank": "Immortal 3",
        "peak_rank": "Radiant",
        "level": 410,
        "total_matches": 140,
        "wins": 71,
        "win_rate": 50.7,
        "kills": 2600,
        "deaths": 2000,
        "kd_ratio": 1.3,
        "kd_scope": "SEASON",
        "recent_matches": [
            {
                "map": "Ascent",
                "mode": "Competitive",
                "start": "",
                "agent": "Jett",
                "won": True,
                "rounds_won": 13,
                "rounds_lost": 9,
                "kills": 24,
                "deaths": 18,
            }
        ],
        "last_updated": datetime(2026, 10, 4, 12, 0, tzinfo=UTC),
    }
    data.update(overrides)
    return PlayerStats(**data)


def test_render_card_geometry():
    img = render_card(_stats())
    assert img.size == (theme.CARD_WIDTH, theme.CARD_HEIGHT)


def test_render_handles_a_very_long_player_name():
    img = render_card(_stats(player_name="A" * 200))
    assert img.size == (theme.CARD_WIDTH, theme.CARD_HEIGHT)


def test_render_handles_no_recent_matches():
    img = render_card(_stats(recent_matches=[]))
    assert img.size == (theme.CARD_WIDTH, theme.CARD_HEIGHT)


def test_render_handles_unranked_player():
    img = render_card(
        _stats(current_rank="Unranked", peak_rank="Unranked", total_matches=0, wins=0)
    )
    assert img.size == (theme.CARD_WIDTH, theme.CARD_HEIGHT)


def test_save_card_uses_an_explicit_path(tmp_path):
    target = tmp_path / "nested" / "card.png"
    assert save_card(_stats(), target) == target
    assert target.exists()
