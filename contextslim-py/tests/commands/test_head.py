"""Tests for contextslim.commands.code.head."""

from __future__ import annotations

from pathlib import Path

import pytest

from contextslim.commands.code.head import head_command
from contextslim.config import Config, Limits


def _make_config(max_line_width: int = 120) -> Config:
    """Build a Config with specific limits for testing."""
    return Config(limits=Limits(max_line_width=max_line_width))


class TestHeadDefault:
    """Default behaviour: shows first 30 non-blank lines."""

    def test_shows_at_most_30(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given a file with >30 non-blank lines, only 30 are shown."""
        lines = [f"line_{i}" for i in range(50)]
        f = tmp_path / "many.txt"
        f.write_text("\n".join(lines))

        head_command(str(f), lines=30, config=_make_config())

        captured = capsys.readouterr()
        assert "Shown 30 lines" in captured.out
        assert "line_29" in captured.out
        assert "line_30" not in captured.out

    def test_shows_fewer_when_file_is_smaller(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given a file with <30 non-blank lines, all are shown."""
        f = tmp_path / "few.txt"
        f.write_text("a\nb\nc\n")

        head_command(str(f), lines=30, config=_make_config())

        captured = capsys.readouterr()
        assert "Shown 3 lines" in captured.out
        assert "a" in captured.out
        assert "b" in captured.out
        assert "c" in captured.out


class TestHeadCustomN:
    """Custom line count via --lines / -n."""

    def test_shows_exactly_n(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given N=5, only 5 lines are shown."""
        lines = [f"line_{i}" for i in range(20)]
        f = tmp_path / "data.txt"
        f.write_text("\n".join(lines))

        head_command(str(f), lines=5, config=_make_config())

        captured = capsys.readouterr()
        assert "Shown 5 lines" in captured.out
        assert "line_4" in captured.out
        assert "line_5" not in captured.out

    def test_n_zero_shows_nothing(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given N=0, no content lines are shown."""
        f = tmp_path / "empty.txt"
        f.write_text("a\nb\n")

        head_command(str(f), lines=0, config=_make_config())

        captured = capsys.readouterr()
        assert "Shown 0 lines" in captured.out


class TestHeadBlankStripping:
    """Blank lines are skipped before counting toward N."""

    def test_blanks_do_not_count_toward_n(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given a file with blank lines interspersed, only non-blank lines appear."""
        f = tmp_path / "gapped.txt"
        f.write_text("a\n\nb\n\nc\n\nd\n")

        head_command(str(f), lines=2, config=_make_config())

        captured = capsys.readouterr()
        assert "Shown 2 lines" in captured.out
        assert "a" in captured.out
        assert "b" in captured.out
        assert "c" not in captured.out  # Should not appear (only 2 non-blank requested)

    def test_blanks_are_reported(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given blank lines, the stripped count appears in stats."""
        f = tmp_path / "whitespace.txt"
        f.write_text("x\n\n\ny\n")

        head_command(str(f), lines=10, config=_make_config())

        captured = capsys.readouterr()
        assert "Stripped 2 blank lines" in captured.out

    def test_all_blanks_shows_nothing(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given a file of only blank lines, no content is shown."""
        f = tmp_path / "blanks.txt"
        f.write_text("\n\n\n\n")

        head_command(str(f), lines=10, config=_make_config())

        captured = capsys.readouterr()
        assert "Shown 0 lines" in captured.out
        assert "Stripped 4 blank lines" in captured.out


class TestHeadSavings:
    """Token savings are reported."""

    def test_savings_are_reported(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given any file, savings stats appear in output."""
        f = tmp_path / "s.txt"
        f.write_text("hello world\nfoo bar\n")

        head_command(str(f), lines=10, config=_make_config())

        captured = capsys.readouterr()
        assert "Saved" in captured.out


class TestHeadNotFound:
    """Error handling for missing files."""

    def test_missing_file_raises(
        self, tmp_path: Path
    ) -> None:
        """Given a nonexistent file path, FileNotFoundError is raised."""
        missing = tmp_path / "nope.txt"

        with pytest.raises(FileNotFoundError):
            head_command(str(missing), lines=10, config=_make_config())


class TestHeadWideLineCapping:
    """Wide lines are capped to config.limits.max_line_width."""

    def test_wide_line_is_capped(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given lines exceeding max_line_width, they are truncated with ellipsis."""
        long_line = "x" * 200
        f = tmp_path / "wide.txt"
        f.write_text(long_line)

        head_command(str(f), lines=10, config=_make_config(max_line_width=10))

        captured = capsys.readouterr()
        assert "…" in captured.out
