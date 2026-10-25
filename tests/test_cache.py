"""Offline tests for the disk cache."""

import time

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


def test_expired_entry_is_deleted_from_disk(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)
    cache.set("k", {"a": 1})
    assert cache.get("k", ttl_seconds=-1) is None
    assert list(tmp_path.glob("*.json")) == []


def test_metadata_includes_the_saved_timestamp(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)
    cache.set("k", {"a": 1})

    hit = cache.get_with_metadata("k")
    assert hit is not None
    payload, saved_at = hit
    assert payload == {"a": 1}
    assert abs(time.time() - saved_at) < 5


def test_eviction_keeps_the_newest_entries(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(cache, "MAX_ENTRIES", 2)

    for i in range(4):
        cache.set(f"k{i}", {"i": i})
        time.sleep(0.05)  # keep mtimes distinct (Windows clock resolution)

    assert len(list(tmp_path.glob("*.json"))) == 2
    assert cache.get("k3") == {"i": 3}
    assert cache.get("k2") == {"i": 2}


def test_writes_are_atomic(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)
    cache.set("k", {"a": 1})
    assert list(tmp_path.glob("*.tmp")) == []
