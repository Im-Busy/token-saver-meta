"""Tests for contextslim.commands.code.cat."""

from __future__ import annotations

from pathlib import Path

import pytest

from contextslim.commands.code.cat import cat_command
from contextslim.config import Config, Limits


def _make_config(cat_lines: int = 150, max_line_width: int = 120) -> Config:
    """Build a Config with specific limits for testing."""
    return Config(limits=Limits(cat_lines=cat_lines, max_line_width=max_line_width))


class TestCatShortFile:
    """Short files (within cat_lines) are displayed in full."""

    def test_short_file_shows_all_lines(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given a file with fewer lines than cat_lines, all lines are shown."""
        f = tmp_path / "short.py"
        f.write_text("line1\nline2\nline3\n")

        cat_command(str(f), _make_config(cat_lines=10))

        captured = capsys.readouterr()
        assert "line1" in captured.out
        assert "line2" in captured.out
        assert "line3" in captured.out

    def test_short_file_reports_no_truncation(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given a short file, the truncation marker is absent."""
        f = tmp_path / "data.txt"
        f.write_text("a\nb\nc\n")

        cat_command(str(f), _make_config(cat_lines=10))

        captured = capsys.readouterr()
        assert "TRUNCATED" not in captured.out

    def test_short_file_reports_savings(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given any file, savings stats are reported."""
        f = tmp_path / "x.txt"
        f.write_text("hello\n")

        cat_command(str(f), _make_config())

        captured = capsys.readouterr()
        assert "Saved" in captured.out


class TestCatLongFile:
    """Files exceeding cat_lines are truncated."""

    def test_long_file_shows_head_and_tail(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given a file with > cat_lines non-blank lines, head and tail are shown."""
        lines = [f"line_{i}" for i in range(200)]
        f = tmp_path / "big.txt"
        f.write_text("\n".join(lines))

        cat_command(str(f), _make_config(cat_lines=20))

        captured = capsys.readouterr()
        assert "line_0" in captured.out
        assert "line_9" in captured.out  # last of head (20//2=10)
        assert "TRUNCATED" in captured.out
        assert "line_190" in captured.out  # first of tail
        assert "line_199" in captured.out  # last line

    def test_long_file_skips_middle(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given truncation, middle lines are NOT shown."""
        lines = [f"line_{i}" for i in range(100)]
        f = tmp_path / "mid.txt"
        f.write_text("\n".join(lines))

        cat_command(str(f), _make_config(cat_lines=20))

        captured = capsys.readouterr()
        # line_50 should be in the skipped middle
        assert "line_50" not in captured.out


class TestCatBlankStripping:
    """Blank lines are stripped and counted."""

    def test_blank_lines_are_counted(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given a file with blank lines, stripped count appears in stats."""
        f = tmp_path / "with_blanks.py"
        f.write_text("a\n\n\nb\n\nc\n")

        cat_command(str(f), _make_config(cat_lines=10))

        captured = capsys.readouterr()
        assert "Stripped 3 blank lines" in captured.out

    def test_blank_lines_do_not_appear_in_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given blank lines, they are excluded from displayed content."""
        f = tmp_path / "gaps.txt"
        f.write_text("hello\n\nworld\n")

        cat_command(str(f), _make_config(cat_lines=10))

        captured = capsys.readouterr()
        # Two non-blank lines should appear with line numbers
        assert "1 " in captured.out  # The first line has line number prefix
        assert "2 " in captured.out  # The second adjacent non-blank keeps sequential numbering
        assert "hello" in captured.out
        assert "world" in captured.out


class TestCatNotFound:
    """Error handling for missing files."""

    def test_missing_file_raises(
        self, tmp_path: Path
    ) -> None:
        """Given a nonexistent file path, FileNotFoundError is raised."""
        missing = tmp_path / "nope.txt"

        with pytest.raises(FileNotFoundError):
            cat_command(str(missing), _make_config())


class TestCatWideLineCapping:
    """Wide lines are capped to max_line_width."""

    def test_wide_line_is_capped(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given a line exceeding max_line_width, it is truncated with ellipsis."""
        long_line = "x" * 200
        f = tmp_path / "wide.txt"
        f.write_text(long_line)

        cat_command(str(f), _make_config(max_line_width=10))

        captured = capsys.readouterr()
        assert "…" in captured.out
        # The shown text should be ≤ 10 chars (minus line number prefix)
        for ln in captured.out.splitlines():
            if "x" in ln and "│" in ln:
                content = ln.split("│", 1)[1].strip()
                assert len(content) <= 10

    def test_short_line_is_not_capped(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given a line shorter than max_line_width, it is unchanged."""
        f = tmp_path / "narrow.txt"
        f.write_text("short")

        cat_command(str(f), _make_config(max_line_width=80))

        captured = capsys.readouterr()
        assert "short" in captured.out
