"""Offline tests for the disk cache."""

from statcard import cache


def test_cache_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)
    cache.set("k", {"a": 1})
    assert cache.get("k") == {"a": 1}


def test_cache_miss(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)
    assert cache.get("missing") is None


def test_cache_expiry(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)
    cache.set("k", {"a": 1})
    # A negative TTL makes every entry expired
    assert cache.get("k", ttl_seconds=-1) is None
