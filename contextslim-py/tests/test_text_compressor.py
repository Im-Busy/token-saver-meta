"""Tests for contextslim.compressor.text."""

from __future__ import annotations

import pytest

from contextslim.compressor.text import (
    cap_line_width,
    strip_blanks,
    strip_timestamps,
    truncate_middle,
)

# ============================================================================
# truncate_middle
# ============================================================================


class TestTruncateMiddle:
    def test_shorter_than_max_returns_all(self) -> None:
        lines = ["a", "b", "c"]
        assert truncate_middle(lines, 5) == lines

    def test_exact_fit_returns_all(self) -> None:
        lines = ["x", "y", "z"]
        assert truncate_middle(lines, 3) == lines

    def test_oversized_splits_head_tail(self) -> None:
        lines = [str(i) for i in range(20)]
        result = truncate_middle(lines, 7)
        # head=3, tail=3, marker=1 → total 7
        assert len(result) == 7
        assert result[0] == "0"
        assert result[1] == "1"
        assert result[2] == "2"
        assert "truncated" in result[3]
        assert result[4] == "17"
        assert result[5] == "18"
        assert result[6] == "19"

    def test_max_lines_one(self) -> None:
        lines = ["a", "b", "c"]
        result = truncate_middle(lines, 1)
        assert result == ["a"]

    def test_max_lines_zero(self) -> None:
        lines = ["a", "b"]
        assert truncate_middle(lines, 0) == []

    def test_max_lines_negative(self) -> None:
        lines = ["a", "b"]
        assert truncate_middle(lines, -5) == []

    def test_max_lines_two(self) -> None:
        """With max_lines=2 (<3), just return first 2 lines (no tail)."""
        lines = [str(i) for i in range(10)]
        result = truncate_middle(lines, 2)
        assert result == ["0", "1"]

    def test_marker_contains_skipped_count(self) -> None:
        lines = [str(i) for i in range(50)]
        result = truncate_middle(lines, 5)
        marker = result[2]
        # head=2, tail=2, skipped=50-2-2=46
        assert "46" in marker

    def test_empty_input(self) -> None:
        assert truncate_middle([], 5) == []
        assert truncate_middle([], 0) == []


# ============================================================================
# strip_blanks
# ============================================================================


class TestStripBlanks:
    def test_all_non_blank(self) -> None:
        lines = ["hello", "world"]
        filtered, removed = strip_blanks(lines)
        assert filtered == ["hello", "world"]
        assert removed == 0

    def test_mixed_blanks(self) -> None:
        lines = ["a", "", "  ", "\t", "b", ""]
        filtered, removed = strip_blanks(lines)
        assert filtered == ["a", "b"]
        assert removed == 4

    def test_all_blanks(self) -> None:
        lines = ["", "   ", "\n"]
        filtered, removed = strip_blanks(lines)
        assert filtered == []
        assert removed == 3

    def test_empty_input(self) -> None:
        filtered, removed = strip_blanks([])
        assert filtered == []
        assert removed == 0

    def test_whitespace_only_lines_removed(self) -> None:
        lines = ["\t\t", "ok", "   "]
        filtered, removed = strip_blanks(lines)
        assert filtered == ["ok"]
        assert removed == 2


# ============================================================================
# strip_timestamps
# ============================================================================


class TestStripTimestamps:
    def test_iso_datetime(self) -> None:
        assert strip_timestamps("2024-01-15T10:30:45Z hello") == "hello"

    def test_iso_date_only(self) -> None:
        assert strip_timestamps("2024-01-15 hello") == "hello"

    def test_iso_with_milliseconds(self) -> None:
        assert strip_timestamps("2024-01-15T10:30:45.123Z data") == "data"

    def test_iso_with_space_separator(self) -> None:
        assert strip_timestamps("2024-01-15 10:30:45 event") == "event"

    def test_iso_with_timezone_offset(self) -> None:
        assert strip_timestamps("2024-01-15T10:30:45+08:00 log") == "log"

    def test_unix_timestamp(self) -> None:
        assert strip_timestamps("1705312245 message") == "message"

    def test_unix_timestamp_with_fractional(self) -> None:
        assert strip_timestamps("1705312245.789123 data") == "data"

    def test_no_timestamp(self) -> None:
        assert strip_timestamps("plain text here") == "plain text here"

    def test_mid_line_date_untouched(self) -> None:
        """Dates embedded mid-line are kept."""
        assert strip_timestamps("prefix 2024-01-15 suffix") == "prefix 2024-01-15 suffix"

    def test_unix_mid_line_untouched(self) -> None:
        """Unix timestamps mid-line are kept (anchor ^ only)."""
        assert strip_timestamps("prefix 1705312245 suffix") == "prefix 1705312245 suffix"

    def test_empty_string(self) -> None:
        assert strip_timestamps("") == ""


# ============================================================================
# cap_line_width
# ============================================================================


class TestCapLineWidth:
    def test_short_line_unchanged(self) -> None:
        assert cap_line_width("hello", 10) == "hello"

    def test_exact_fit_unchanged(self) -> None:
        s = "12345"
        assert cap_line_width(s, 5) == s

    def test_long_line_truncated(self) -> None:
        s = "abcdefghij"
        result = cap_line_width(s, 5)
        assert len(result) == 5
        assert result.endswith("…")

    def test_width_zero(self) -> None:
        assert cap_line_width("abc", 0) == ""

    def test_width_negative(self) -> None:
        assert cap_line_width("abc", -1) == ""

    def test_width_one(self) -> None:
        assert cap_line_width("abc", 1) == "…"

    def test_empty_string(self) -> None:
        assert cap_line_width("", 5) == ""
