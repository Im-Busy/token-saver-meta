"""Tests for contextslim.commands.code.tree_cmd."""

from __future__ import annotations

from pathlib import Path

import pytest

from contextslim.commands.code.tree_cmd import tree_command
from contextslim.config import Config


@pytest.fixture
def cfg() -> Config:
    return Config()


class TestTreeCommand:
    """Directory tree rendering."""

    def test_shows_directory_tree(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: nested dirs with files. When: tree. Then: rendered correctly."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("pass")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_app.py").write_text("def test(): pass")
        (tmp_path / "README.md").write_text("# Project")

        tree_command(str(tmp_path), max_depth=3, config=cfg)

        out = capsys.readouterr().out
        assert "src" in out
        assert "tests" in out
        assert "main.py" in out
        assert "test_app.py" in out
        assert "README.md" in out

    def test_respects_max_depth(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: deeply nested dirs. When: tree depth=1. Then: only shallow."""
        (tmp_path / "a").mkdir()
        (tmp_path / "a" / "b").mkdir()
        (tmp_path / "a" / "b" / "c").mkdir()

        tree_command(str(tmp_path), max_depth=1, config=cfg)

        out = capsys.readouterr().out
        assert "a" in out
        # b should not appear beyond depth 0 root + depth 1 = a only
        # Actually generate_mini_tree with max_depth=2 shows depth 0 (root) + 1 level
        # Let me check: generate_mini_tree(root, max_depth=2) - root is depth 0, children depth 1
        # So max_depth=2 shows root + 1 level of children
        # CLI default depth=3 means root + 2 levels

    def test_reports_hidden_dirs(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: IGNORED_DIRS present. When: tree. Then: hidden count reported."""
        (tmp_path / "src").mkdir()
        (tmp_path / "node_modules").mkdir()
        (tmp_path / ".git").mkdir()
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "dist").mkdir()

        tree_command(str(tmp_path), max_depth=2, config=cfg)

        out = capsys.readouterr().out
        assert "src" in out
        assert "node_modules" not in out
        assert "4 heavy dirs hidden" in out

    def test_tree_skips_ignored_dirs(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: node_modules subdir. When: tree. Then: skipped from tree."""
        (tmp_path / "src").mkdir()
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "lodash").mkdir()

        tree_command(str(tmp_path), max_depth=3, config=cfg)

        out = capsys.readouterr().out
        assert "src" in out
        assert "node_modules" not in out

    def test_not_a_directory(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: non-existent path. When: tree. Then: error printed."""
        bad = tmp_path / "nonexistent_dir_xyz"
        tree_command(str(bad), max_depth=2, config=cfg)
        out = capsys.readouterr().out
        assert "Error" in out
