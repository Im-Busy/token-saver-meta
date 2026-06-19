"""Tests for contextslim.commands.code.ls_cmd."""

from __future__ import annotations

from pathlib import Path

import pytest

from contextslim.commands.code.ls_cmd import ls_command
from contextslim.config import Config


@pytest.fixture
def cfg() -> Config:
    return Config()


class TestLsCommand:
    """List directory contents with filtering."""

    def test_lists_dirs_and_files(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: a dir with files and subdirs. When: ls. Then: both shown."""
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "README.md").write_text("# Project")
        (tmp_path / "pyproject.toml").write_text("[project]")

        ls_command(str(tmp_path), cfg)

        out = capsys.readouterr().out
        assert "src/" in out
        assert "tests/" in out
        assert "README.md" in out
        assert "pyproject.toml" in out

    def test_skips_ignored_dirs(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: IGNORED_DIRS present. When: ls. Then: skipped in listing."""
        (tmp_path / "src").mkdir()
        (tmp_path / "node_modules").mkdir()
        (tmp_path / ".git").mkdir()
        (tmp_path / "__pycache__").mkdir()

        ls_command(str(tmp_path), cfg)

        out = capsys.readouterr().out
        assert "src/" in out
        assert "node_modules" not in out
        assert ".git" not in out
        assert "__pycache__" not in out

    def test_reports_hidden_count(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: 3 IGNORED_DIRS. When: ls. Then: summary shows hidden count."""
        (tmp_path / "src").mkdir()
        (tmp_path / "node_modules").mkdir()
        (tmp_path / ".git").mkdir()
        (tmp_path / "dist").mkdir()

        ls_command(str(tmp_path), cfg)

        out = capsys.readouterr().out
        assert "3 heavy dirs hidden" in out
        assert "1 dirs" in out
        assert "0 files" in out

    def test_reports_counts(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: 2 dirs, 3 files. When: ls. Then: summary correct."""
        (tmp_path / "a").mkdir()
        (tmp_path / "b").mkdir()
        (tmp_path / "x.txt").write_text("x")
        (tmp_path / "y.txt").write_text("y")
        (tmp_path / "z.py").write_text("pass")

        ls_command(str(tmp_path), cfg)

        out = capsys.readouterr().out
        assert "2 dirs, 3 files" in out

    def test_empty_directory(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: empty dir. When: ls. Then: summary shows 0 counts."""
        ls_command(str(tmp_path), cfg)

        out = capsys.readouterr().out
        assert "0 dirs, 0 files" in out

    def test_not_a_directory(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: non-existent path. When: ls. Then: error printed."""
        bad = tmp_path / "nonexistent_dir_xyz"
        ls_command(str(bad), cfg)
        out = capsys.readouterr().out
        assert "Error" in out
