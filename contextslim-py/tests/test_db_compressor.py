"""Tests for database output compression utilities."""

from __future__ import annotations

import pytest
from contextslim.compressor.db import truncate_columns, limit_rows, format_table


# ---------------------------------------------------------------------------
# truncate_columns
# ---------------------------------------------------------------------------

class TestTruncateColumns:
    def test_truncates_long_cells(self) -> None:
        rows = [["short", "a" * 50, "ok"]]
        result = truncate_columns(rows, max_width=10)
        assert result == [["short", "a" * 7 + "...", "ok"]]

    def test_leaves_short_cells_unchanged(self) -> None:
        rows = [["a", "bb", "ccc"]]
        result = truncate_columns(rows, max_width=10)
        assert result == [["a", "bb", "ccc"]]

    def test_exact_boundary(self) -> None:
        rows = [["1234567890"]]  # 10 chars, max_width=10
        result = truncate_columns(rows, max_width=10)
        assert result == [["1234567890"]]  # not truncated

    def test_one_over_boundary(self) -> None:
        rows = [["12345678901"]]  # 11 chars, max_width=10
        result = truncate_columns(rows, max_width=10)
        assert result == [["1234567..."]]  # 10 - 3 = 7 showable

    def test_non_string_cells_converted(self) -> None:
        rows = [[1, 2.5, None]]
        result = truncate_columns(rows, max_width=10)
        assert result == [["1", "2.5", "None"]]

    def test_multiple_rows(self) -> None:
        rows = [
            ["short", "long_long_long_value", "x"],
            ["a", "b", "c"],
        ]
        result = truncate_columns(rows, max_width=8)
        # "long_long_long_value" (21 chars) → 5 showable + "..." = "long_..."
        assert result == [
            ["short", "long_...", "x"],
            ["a", "b", "c"],
        ]

    def test_default_max_width(self) -> None:
        rows = [["a" * 100]]
        result = truncate_columns(rows)
        assert result == [["a" * 27 + "..."]]

    def test_empty_rows(self) -> None:
        assert truncate_columns([], max_width=10) == []


# ---------------------------------------------------------------------------
# limit_rows
# ---------------------------------------------------------------------------

class TestLimitRows:
    def test_no_limit_when_under_max(self) -> None:
        rows = [["a"], ["b"], ["c"]]
        result = limit_rows(rows, max_rows=5)
        assert result == [["a"], ["b"], ["c"]]

    def test_limits_and_adds_summary(self) -> None:
        rows = [["r1"], ["r2"], ["r3"], ["r4"], ["r5"]]
        result = limit_rows(rows, max_rows=3)
        assert result == [["r1"], ["r2"], ["r3"], ["... and 2 more rows"]]

    def test_returns_copy_not_reference(self) -> None:
        rows = [["a"]]
        result = limit_rows(rows, max_rows=10)
        assert result == [["a"]]
        result[0][0] = "modified"
        assert rows[0][0] == "a"  # original unchanged

    def test_empty_input(self) -> None:
        assert limit_rows([], max_rows=10) == []


# ---------------------------------------------------------------------------
# format_table
# ---------------------------------------------------------------------------

class TestFormatTable:
    def test_basic_table(self) -> None:
        headers = ["Name", "Age"]
        rows = [["Alice", "30"], ["Bob", "25"]]
        result = format_table(headers, rows)
        assert "Name" in result
        assert "Age" in result
        assert "Alice" in result
        assert "30" in result
        assert "Bob" in result
        assert "25" in result

    def test_alignment(self) -> None:
        headers = ["N", "LongHeader"]
        rows = [["a", "short"], ["longer", "b"]]
        result = format_table(headers, rows)
        lines = result.split("\n")
        # 2 cols, max_cols defaults to 20 → no "..." column added.
        # Widest in col 0 = "longer" (6), col 1 = "LongHeader" (10).
        assert lines[0] == "N       LongHeader"
        # "a" padded to 6, "short" padded to 10
        assert lines[1] == "a       short     "
        assert lines[2] == "longer  b         "

    def test_row_limiting(self) -> None:
        headers = ["Col"]
        rows = [[str(i)] for i in range(20)]
        result = format_table(headers, rows, max_rows=5)
        lines = result.split("\n")
        assert len(lines) == 7  # header + 5 data + 1 summary

    def test_column_limiting(self) -> None:
        headers = ["A", "B", "C", "D", "E"]
        rows = [["1", "2", "3", "4", "5"]]
        result = format_table(headers, rows, max_cols=3)
        lines = result.split("\n")
        # 5 cols → limited to 3 + "..." marker
        assert lines[0] == "A  B  C  ..."
        assert lines[1] == "1  2  3  ..."

    def test_empty_data(self) -> None:
        headers = ["X", "Y"]
        result = format_table(headers, [], max_rows=5)
        assert "X" in result
        assert "Y" in result

    def test_single_column(self) -> None:
        headers = ["ID"]
        rows = [["1"], ["2"]]
        result = format_table(headers, rows)
        assert "ID" in result
        assert "1" in result
        assert "2" in result

    def test_truncated_in_format(self) -> None:
        """format_table does NOT auto-truncate columns — that's truncate_columns' job."""
        headers = ["Key", "Value"]
        rows = [["k", "v" * 50]]
        result = format_table(headers, rows)
        assert "v" * 50 in result
