"""Tests for session_memory.caching — ShortTTLCache and stable_hash."""

from __future__ import annotations

import time

import pytest

from token_saver_mem.session_memory.caching import ShortTTLCache, stable_hash


class TestStableHash:
    """stable_hash() tests."""

    def test_same_input_produces_same_hash(self) -> None:
        """Given the same data, When hashed twice, Then same SHA-256 hex digest."""
        data = {"key": "value", "nested": [1, 2, 3]}
        h1 = stable_hash(data)
        h2 = stable_hash(data)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex is 64 chars
        assert all(c in "0123456789abcdef" for c in h1)

    def test_different_input_produces_different_hash(self) -> None:
        """Given different data, When hashed, Then different digests."""
        h1 = stable_hash({"a": 1})
        h2 = stable_hash({"a": 2})
        assert h1 != h2

    def test_key_order_independent(self) -> None:
        """Given same dict with different key order, When hashed, Then same digest."""
        h1 = stable_hash({"a": 1, "b": 2})
        h2 = stable_hash({"b": 2, "a": 1})
        assert h1 == h2

    def test_string_input(self) -> None:
        """Given a string, When hashed, Then produces SHA-256 hex."""
        h = stable_hash("hello world")
        assert len(h) == 64

    def test_nested_structures(self) -> None:
        """Given nested dicts/lists, When hashed, Then deterministic."""
        complex_data = {
            "ops": [
                {"name": "auth", "confidence": 0.9},
                {"name": "db", "confidence": 0.8},
            ],
            "state": {"pending": 3, "blockers": 1},
        }
        h1 = stable_hash(complex_data)
        h2 = stable_hash(complex_data)
        assert h1 == h2


class TestShortTTLCache:
    """ShortTTLCache tests."""

    def test_set_and_get(self) -> None:
        """Given a cache, When set then get, Then returns the value."""
        cache = ShortTTLCache(ttl_seconds=60)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_miss_returns_none(self) -> None:
        """Given a cache without a key, When get, Then returns None."""
        cache = ShortTTLCache(ttl_seconds=60)
        assert cache.get("nonexistent") is None

    def test_expiry_removes_item(self) -> None:
        """Given a cache with short TTL, When TTL expires, Then get returns None."""
        cache = ShortTTLCache(ttl_seconds=0.05)  # 50ms TTL
        cache.set("key1", "value1")
        # Immediately accessible
        assert cache.get("key1") == "value1"
        # Wait for expiry
        time.sleep(0.1)
        assert cache.get("key1") is None

    def test_ttl_zero_disables_cache(self) -> None:
        """Given TTL=0, When set then get, Then returns None (cache disabled)."""
        cache = ShortTTLCache(ttl_seconds=0)
        cache.set("key1", "value1")
        assert cache.get("key1") is None

    def test_stats_hits_and_misses(self) -> None:
        """Given a cache, When accessed, Then stats track hits and misses."""
        cache = ShortTTLCache(ttl_seconds=60)
        cache.set("a", 1)
        cache.get("a")  # hit
        cache.get("b")  # miss
        cache.get("c")  # miss
        assert cache.stats.hits == 1
        assert cache.stats.misses == 2
        cache.get("a")  # hit
        assert cache.stats.hits == 2

    def test_stats_on_expiry_count_as_miss(self) -> None:
        """Given expired item, When get, Then counts as miss."""
        cache = ShortTTLCache(ttl_seconds=0.01)  # 10ms
        cache.set("x", 1)
        time.sleep(0.05)
        assert cache.get("x") is None
        assert cache.stats.misses >= 1

    def test_max_size_enforced(self) -> None:
        """Given max_size=3, When more items set, Then oldest are evicted."""
        cache = ShortTTLCache(ttl_seconds=60, max_size=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)  # should evict oldest
        # With max_size enforcement, we should have at most 3 items
        found = sum(1 for k in ["a", "b", "c", "d"] if cache.get(k) is not None)
        assert found <= 3

    def test_different_types_as_keys(self) -> None:
        """Given different key types, When set and get, Then works with hashed keys."""
        cache = ShortTTLCache(ttl_seconds=60)
        cache.set({"complex": "key"}, "val1")
        cache.set([1, 2, 3], "val2")
        cache.set("simple", "val3")
        assert cache.get({"complex": "key"}) == "val1"
        assert cache.get([1, 2, 3]) == "val2"
        assert cache.get("simple") == "val3"

    def test_overwrite_updates_value(self) -> None:
        """Given existing key, When set again, Then value is updated."""
        cache = ShortTTLCache(ttl_seconds=60)
        cache.set("key", "old")
        cache.set("key", "new")
        assert cache.get("key") == "new"
