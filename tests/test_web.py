"""Offline tests for the FastAPI backend (no API key, no network)."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from statcard.models import PlayerStats
from statcard.providers.valorant import ValorantNotFoundError
from statcard.web import api as web_api
from statcard.web.app import create_app
from statcard.web.settings import Settings


def _make_stats() -> PlayerStats:
    return PlayerStats(
        game="valorant",
        player_name="Horcus",
        player_id="Horcus#1995",
        current_rank="Immortal 3",
        peak_rank="Radiant",
        level=410,
        total_matches=140,
        wins=71,
        win_rate=50.7,
        kills=2600,
        deaths=2000,
        kd_ratio=1.3,
        kd_scope="SEASON",
        recent_matches=[
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
        last_updated=datetime(2026, 10, 4, 12, 0),
    )


async def _fake_fetch(*args: object, **kwargs: object) -> PlayerStats:
    return _make_stats()


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(web_api, "fetch_valorant_stats", _fake_fetch)
    return TestClient(create_app(Settings(rate_per_min=3, rate_global_per_min=50)))


def test_healthz(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_healthz_is_never_rate_limited(client: TestClient) -> None:
    for _ in range(10):
        assert client.get("/healthz").status_code == 200


def test_card_is_png_with_cache_header(client: TestClient) -> None:
    response = client.get("/api/valorant/Horcus%231995")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")
    assert "max-age=3600" in response.headers["cache-control"]


def test_json_endpoint_exposes_kd_scope(client: TestClient) -> None:
    payload = client.get("/api/valorant/Horcus%231995/json").json()
    assert payload["player_id"] == "Horcus#1995"
    assert payload["kd_scope"] == "SEASON"


def test_malformed_riot_id_is_400(client: TestClient) -> None:
    assert client.get("/api/valorant/NoTagHere").status_code == 400


def test_unknown_region_is_400(client: TestClient) -> None:
    assert client.get("/api/valorant/Horcus%231995?region=mars").status_code == 400


def test_not_found_maps_to_404(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def boom(*args: object, **kwargs: object) -> PlayerStats:
        raise ValorantNotFoundError("Player not found (404): x")

    monkeypatch.setattr(web_api, "fetch_valorant_stats", boom)
    assert client.get("/api/valorant/Ghost%230000").status_code == 404


def test_per_ip_rate_limit_returns_429(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(web_api, "fetch_valorant_stats", _fake_fetch)
    limited = TestClient(create_app(Settings(rate_per_min=2, rate_global_per_min=50)))
    assert limited.get("/api/valorant/Horcus%231995").status_code == 200
    assert limited.get("/api/valorant/Horcus%231995").status_code == 200
    third = limited.get("/api/valorant/Horcus%231995")
    assert third.status_code == 429
    assert third.headers["retry-after"].isdigit()
    assert third.json()["detail"]["retry_after"] >= 1


def test_global_cap_across_ips(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(web_api, "fetch_valorant_stats", _fake_fetch)
    capped = TestClient(create_app(Settings(rate_per_min=5, rate_global_per_min=2)))
    ok1 = capped.get("/api/valorant/A%23EU", headers={"x-forwarded-for": "1.1.1.1"})
    ok2 = capped.get("/api/valorant/B%23EU", headers={"x-forwarded-for": "2.2.2.2"})
    third = capped.get("/api/valorant/C%23EU", headers={"x-forwarded-for": "3.3.3.3"})
    assert ok1.status_code == 200
    assert ok2.status_code == 200
    assert third.status_code == 429
