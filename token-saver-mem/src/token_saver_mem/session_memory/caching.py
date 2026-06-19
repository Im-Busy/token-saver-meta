"""Deterministic caching and hashing utilities.

Port of codex-agent-mem's runtime_efficiency.py ShortTTLCache + stable_hash.

ShortTTLCache: time-bounded cache with TTL expiry and max_size eviction.
stable_hash: deterministic SHA-256 hex digest for cache keys and pack matching.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any


# ── stable_hash ──────────────────────────────────────────────────


def stable_hash(value: Any) -> str:
    """Compute a deterministic SHA-256 hex digest for any JSON-serializable value.

    Uses sort_keys=True for key-order independence and ensure_ascii=True
    for cross-platform determinism. Non-JSON-serializable types fall back
    to str() representation.

    Args:
        value: Any JSON-serializable Python value (dict, list, str, int, etc.).

    Returns:
        64-character SHA-256 hex digest string.
    """
    return hashlib.sha256(_stable_json_dumps(value).encode("utf-8")).hexdigest()


def _stable_json_dumps(value: Any) -> str:
    """Serialize value to deterministic JSON string."""
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=str)


# ── ShortTTLCache ────────────────────────────────────────────────


@dataclass
class CacheStats:
    """Cache hit/miss statistics."""

    hits: int = 0
    misses: int = 0


class ShortTTLCache:
    """Time-bounded cache with TTL expiry and optional max_size eviction.

    Keys are hashed via stable_hash() for deterministic lookup.
    If ttl_seconds is 0, the cache is completely disabled (get always returns None).

    Attributes:
        ttl_seconds: Time-to-live in seconds. 0 disables caching.
        max_size: Maximum number of cached items. Oldest evicted on overflow.
        stats: CacheStats tracking hits and misses.
    """

    def __init__(self, ttl_seconds: int = 15, max_size: int = 100) -> None:
        """Initialize cache.

        Args:
            ttl_seconds: Time-to-live in seconds (default: 15). Set to 0 to disable.
            max_size: Maximum cache entries (default: 100). FIFO eviction on overflow.
        """
        self.ttl_seconds = max(0, ttl_seconds)
        self.max_size = max(1, max_size)
        self._items: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self.stats = CacheStats()

    def get(self, key: Any) -> Any | None:
        """Get a cached value by key.

        Args:
            key: Cache key (any hashable/stably-serializable value).

        Returns:
            Cached value if present and not expired, None otherwise.
        """
        if self.ttl_seconds <= 0:
            self.stats.misses += 1
            return None

        cache_key = stable_hash(key)
        item = self._items.get(cache_key)
        if item is None:
            self.stats.misses += 1
            return None

        expires_at, value = item
        if time.monotonic() >= expires_at:
            self._items.pop(cache_key, None)
            self.stats.misses += 1
            return None

        self.stats.hits += 1
        return value

    def set(self, key: Any, value: Any) -> None:
        """Set a cached value with TTL.

        Args:
            key: Cache key (any hashable/stably-serializable value).
            value: Value to cache.
        """
        if self.ttl_seconds <= 0:
            return

        cache_key = stable_hash(key)
        # Evict oldest if at capacity (and key is new)
        if cache_key not in self._items and len(self._items) >= self.max_size:
            self._items.popitem(last=False)  # FIFO: remove first inserted

        self._items[cache_key] = (time.monotonic() + self.ttl_seconds, value)
        # Move to end if already exists (LRU behavior)
        if cache_key in self._items:
            self._items.move_to_end(cache_key)
