"""Tests for tscg.core.utils."""

import math
import pytest
from tscg.core.utils import estimate_tokens, estimate_diff


class TestEstimateTokens:
    """estimate_tokens uses chars/4 heuristic with ceil rounding."""

    def test_ascii_text(self):
        """Given: ASCII text
        When: estimate_tokens is called
        Then: returns ceil(chars/4)"""
        assert estimate_tokens("hello world") == math.ceil(len("hello world") / 4)

    def test_empty_string(self):
        """Given: empty string
        When: estimate_tokens is called
        Then: returns 0"""
        assert estimate_tokens("") == 0

    def test_four_chars_is_one_token(self):
        """Given: exactly 4 characters
        When: estimate_tokens is called
        Then: returns 1"""
        assert estimate_tokens("abcd") == 1

    def test_five_chars_is_two_tokens(self):
        """Given: 5 characters
        When: estimate_tokens is called
        Then: returns ceil(5/4) = 2"""
        assert estimate_tokens("hello") == 2

    def test_non_ascii_text(self):
        """Given: text with non-ASCII characters (CJK, emoji)
        When: estimate_tokens is called
        Then: still uses chars/4 heuristic"""
        text = "你好世界"  # 4 CJK chars
        assert estimate_tokens(text) == math.ceil(len(text) / 4)

    def test_emoji_text(self):
        """Given: text with emoji
        When: estimate_tokens is called
        Then: still uses chars/4 heuristic (Python len counts correctly)"""
        text = "hello 🌍 world 🚀"
        assert estimate_tokens(text) == math.ceil(len(text) / 4)

    def test_long_text(self):
        """Given: long text
        When: estimate_tokens is called
        Then: returns correct ceil(chars/4)"""
        text = "a" * 1000
        assert estimate_tokens(text) == 250  # 1000/4

    def test_odd_length_text(self):
        """Given: text with odd character count
        When: estimate_tokens is called
        Then: rounds up via ceil"""
        assert estimate_tokens("abc") == 1  # ceil(3/4)
        assert estimate_tokens("abcde") == 2  # ceil(5/4)

    def test_tiktoken_fallback(self, monkeypatch):
        """Given: tiktoken not installed
        When: estimate_tokens is called
        Then: falls back to chars/4 without error"""
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "tiktoken":
                raise ImportError("No module named 'tiktoken'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)
        # Force re-import to trigger the fallback path
        import importlib
        import tscg.core.utils as utils_mod
        importlib.reload(utils_mod)

        text = "the quick brown fox"
        expected = math.ceil(len(text) / 4)
        assert utils_mod.estimate_tokens(text) == expected


class TestEstimateDiff:
    """estimate_diff calculates percentage savings."""

    def test_positive_savings(self):
        """Given: before > after
        When: estimate_diff is called
        Then: returns positive savings percentage"""
        assert estimate_diff(100, 50) == pytest.approx(50.0)

    def test_no_change(self):
        """Given: before == after
        When: estimate_diff is called
        Then: returns 0.0"""
        assert estimate_diff(100, 100) == 0.0

    def test_string_inputs(self):
        """Given: string before/after values
        When: estimate_diff is called
        Then: converts via estimate_tokens and computes savings"""
        before = "a" * 100  # 25 tokens
        after = "b" * 40   # 10 tokens
        expected = (25 - 10) / 25 * 100  # 60%
        assert estimate_diff(before, after) == pytest.approx(expected)

    def test_negative_savings(self):
        """Given: after > before (expansion)
        When: estimate_diff is called
        Then: returns negative percentage"""
        assert estimate_diff(50, 100) == pytest.approx(-100.0)

    def test_zero_before(self):
        """Given: before is 0
        When: estimate_diff is called
        Then: returns 0.0 (avoids division by zero)"""
        assert estimate_diff(0, 100) == 0.0

    def test_mixed_int_str(self):
        """Given: int before, str after
        When: estimate_diff is called
        Then: converts str via estimate_tokens"""
        diff = estimate_diff(100, "abc")  # 100 tokens before, 1 token after
        expected = (100 - 1) / 100 * 100  # 99%
        assert diff == pytest.approx(expected)

    def test_full_savings(self):
        """Given: after is 0
        When: estimate_diff is called
        Then: returns 100% savings"""
        assert estimate_diff(100, 0) == 100.0
