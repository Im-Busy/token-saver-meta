"""Tests for contextslim.commands.git.diff."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from contextslim.commands.git.diff import _cap_output, _file_diff


# ============================================================================
# _cap_output
# ============================================================================


class TestCapOutput:
    def test_under_limit_unchanged(self) -> None:
        text = "a\nb\nc"
        assert _cap_output(text, 5) == text

    def test_exact_limit_unchanged(self) -> None:
        text = "a\nb\nc"
        assert _cap_output(text, 3) == text

    def test_over_limit_truncated(self) -> None:
        lines = "\n".join(str(i) for i in range(30))
        result = _cap_output(lines, 10)
        assert "truncated" in result
        result_lines = result.splitlines()
        assert len(result_lines) == 10

    def test_very_small_limit(self) -> None:
        lines = "\n".join(str(i) for i in range(20))
        result = _cap_output(lines, 3)
        result_lines = result.splitlines()
        assert len(result_lines) == 3


# ============================================================================
# _file_diff
# ============================================================================


class TestFileDiff:
    def test_different_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            f1 = root / "a.txt"
            f2 = root / "b.txt"
            f1.write_text("line 1\nline 2\nline 3\n", encoding="utf-8")
            f2.write_text("line 1\nline X\nline 3\n", encoding="utf-8")
            result = _file_diff(str(f1), str(f2))
            assert "line 2" in result
            assert "line X" in result
            assert "@@" in result  # unified diff hunk header

    def test_same_files_no_diff(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            f1 = root / "a.txt"
            f2 = root / "b.txt"
            content = "identical\ncontent\n"
            f1.write_text(content, encoding="utf-8")
            f2.write_text(content, encoding="utf-8")
            result = _file_diff(str(f1), str(f2))
            assert result == ""

    def test_file_not_found(self) -> None:
        result = _file_diff("/nonexistent/a.txt", "/nonexistent/b.txt")
        assert "Error" in result or result == ""

    def test_one_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            f1 = root / "a.txt"
            f1.write_text("hello\n", encoding="utf-8")
            result = _file_diff(str(f1), str(root / "missing.txt"))
            assert "Error" in result or result == ""
