"""Tests for token-counting measurement library."""

import pytest
from measurement import TokenCounter


@pytest.fixture
def counter():
    return TokenCounter()


class TestCountTokens:
    def test_empty_string(self, counter):
        """count_tokens("") returns 0."""
        assert counter.count_tokens("") == 0

    def test_ascii(self, counter):
        """count_tokens("hello world") returns expected value."""
        # cl100k_base: "hello" (1) + " world" (1) = 2
        assert counter.count_tokens("hello world") == 2

    def test_unicode(self, counter):
        """count_tokens("你好世界") returns expected value."""
        assert counter.count_tokens("你好世界") == 5


class TestCountDelta:
    def test_delta_zero(self, counter):
        """count_delta("same", "same") returns delta=0, delta_pct=0.0."""
        result = counter.count_delta("same", "same")
        assert result["delta"] == 0
        assert result["delta_pct"] == 0.0

    def test_delta_positive(self, counter):
        """count_delta("hello world", "hello") returns delta>0, delta_pct>0."""
        result = counter.count_delta("hello world", "hello")
        assert result["delta"] > 0
        assert result["delta_pct"] > 0.0
        assert result["with_tokens"] == 2
        assert result["without_tokens"] == 1

    def test_delta_different(self, counter):
        """count_delta between different texts returns meaningful delta."""
        result = counter.count_delta(
            "this is a longer sentence",
            "short",
        )
        assert result["with_tokens"] > result["without_tokens"]
        assert result["delta"] > 0
        assert result["delta_pct"] > 0.0


class TestCountBytes:
    def test_bytes_empty(self, counter):
        """count_bytes("") returns 0."""
        assert counter.count_bytes("") == 0

    def test_bytes_unicode(self, counter):
        """count_bytes("你好") returns expected byte count."""
        # "你好" = 6 UTF-8 bytes (3 per CJK character)
        assert counter.count_bytes("你好") == 6

    def test_bytes_ascii(self, counter):
        """count_bytes for ASCII text matches len(text)."""
        assert counter.count_bytes("hello") == 5
