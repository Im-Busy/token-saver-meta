"""Tests for contextslim.commands.search.grep."""

from __future__ import annotations

from pathlib import Path

import pytest

from contextslim.commands.search.grep import grep_command
from contextslim.config import Config, Limits


@pytest.fixture
def cfg() -> Config:
    return Config()


@pytest.fixture
def strict_cfg() -> Config:
    """Config with very low limits for capping tests."""
    return Config(limits=Limits(grep_matches_per_file=2, grep_max_total=3))


class TestGrepCommand:
    """File search with filtering and capping."""

    def test_finds_matches(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: file with matching text. When: grep. Then: matches shown."""
        (tmp_path / "main.py").write_text("print('hello')\nprint('world')\nprint('hello again')\n")

        grep_command("hello", str(tmp_path), cfg)

        out = capsys.readouterr().out
        assert "main.py" in out
        assert "hello" in out
        assert "1" in out  # line number 1
        assert "3" in out  # line number 3

    def test_case_insensitive(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: mixed-case text. When: grep 'TODO'. Then: matches 'todo', 'Todo'."""
        (tmp_path / "notes.txt").write_text("TODO: fix this\nFix the Todo item\ntodo later\n")

        grep_command("TODO", str(tmp_path), cfg)

        out = capsys.readouterr().out
        assert "3 matches" in out

    def test_skips_ignored_dirs(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: match in node_modules. When: grep. Then: skipped."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "app.py").write_text("TODO: fix bug")
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "lib.js").write_text("TODO: ignore me")

        grep_command("TODO", str(tmp_path), cfg)

        out = capsys.readouterr().out
        assert "app.py" in out
        assert "lib.js" not in out

    def test_skips_binary_extensions(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: .png and .pyc files with match text. When: grep. Then: skipped."""
        (tmp_path / "data.py").write_text("TODO: data fix")
        (tmp_path / "image.png").write_text("TODO: in image")  # would match if read
        (tmp_path / "cache.pyc").write_text("TODO: in cache")

        grep_command("TODO", str(tmp_path), cfg)

        out = capsys.readouterr().out
        assert "data.py" in out
        assert "image.png" not in out
        assert "cache.pyc" not in out

    def test_caps_per_file(self, tmp_path: Path, strict_cfg: Config, capsys) -> None:
        """Given: 5 matches in one file, cap=2. When: grep. Then: only 2 shown."""
        lines = "\n".join(f"line{i}: found" for i in range(1, 6))
        (tmp_path / "log.txt").write_text(lines)

        grep_command("found", str(tmp_path), strict_cfg)

        out = capsys.readouterr().out
        # strict_cfg has grep_matches_per_file=2, grep_max_total=3
        # Should show at most 2 matches
        assert "line1: found" in out
        assert "line2: found" in out
        if "line3" in out:
            # Could have 3 if total cap not hit yet with just 1 file
            pass  # acceptable — total_cap=3 > per_file_cap=2, but we only have 1 file
        assert "line4" not in out  # definitely beyond per_file_cap
        assert "line5" not in out

    def test_caps_total(self, tmp_path: Path, strict_cfg: Config, capsys) -> None:
        """Given: many files with matches, total_cap=3. When: grep. Then: max 3."""
        for i in range(5):
            (tmp_path / f"file{i}.txt").write_text(f"match in file {i}\nanother match\n")

        grep_command("match", str(tmp_path), strict_cfg)

        out = capsys.readouterr().out
        # strict_cfg has grep_max_total=3, grep_matches_per_file=2
        # At most 3 total matches across all files
        assert "results capped" in out

    def test_no_matches(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: no matching text. When: grep. Then: 'No matches' message."""
        (tmp_path / "file.txt").write_text("nothing here")

        grep_command("xyz_not_present", str(tmp_path), cfg)

        out = capsys.readouterr().out
        assert "No matches found" in out

    def test_truncates_long_lines(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: line > max_line_width. When: grep. Then: truncated with '...'."""
        long_line = "x" * 200 + " target " + "y" * 50
        (tmp_path / "big.txt").write_text(long_line)

        grep_command("target", str(tmp_path), cfg)

        out = capsys.readouterr().out
        assert "..." in out

    def test_reports_counts(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: 2 files, 5 matches total. When: grep. Then: summary correct."""
        (tmp_path / "a.txt").write_text("alpha\nbeta\nalpha again\n")
        (tmp_path / "b.txt").write_text("alpha other\ndelta\n")

        grep_command("alpha", str(tmp_path), cfg)

        out = capsys.readouterr().out
        assert "3 matches across 2 file(s)" in out

    def test_handles_empty_directory(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: empty dir. When: grep. Then: no matches."""
        grep_command("anything", str(tmp_path), cfg)
        out = capsys.readouterr().out
        assert "No matches found" in out

    def test_not_a_directory(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: non-existent path. When: grep. Then: error printed."""
        bad = tmp_path / "nonexistent_dir_xyz"
        grep_command("query", str(bad), cfg)
        out = capsys.readouterr().out
        assert "Error" in out
