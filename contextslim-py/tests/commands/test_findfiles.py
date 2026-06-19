"""Tests for contextslim.commands.search.findfiles."""

from __future__ import annotations

from pathlib import Path

import pytest

from contextslim.commands.search.findfiles import findfiles_command
from contextslim.config import Config, Limits


@pytest.fixture
def cfg() -> Config:
    return Config()


@pytest.fixture
def strict_cfg() -> Config:
    """Config with low findfiles limit."""
    return Config(limits=Limits(findfiles_limit=3))


class TestFindfilesCommand:
    """Find files by glob with filtering and capping."""

    def test_finds_matching_files(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: .py files. When: findfiles '*.py'. Then: all .py files shown."""
        (tmp_path / "main.py").write_text("pass")
        (tmp_path / "utils.py").write_text("pass")
        (tmp_path / "README.md").write_text("# README")
        findfiles_command("*.py", str(tmp_path), cfg)
        out = capsys.readouterr().out
        assert "main.py" in out
        assert "utils.py" in out
        assert "README.md" not in out

    def test_reports_count(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: 2 matching files. When: findfiles. Then: '2 file(s)'."""
        (tmp_path / "a.py").write_text("pass")
        (tmp_path / "b.py").write_text("pass")
        findfiles_command("*.py", str(tmp_path), cfg)
        out = capsys.readouterr().out
        assert "2 file(s) matched" in out

    def test_no_matches(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: no .rs files. When: findfiles '*.rs'. Then: 'No files'."""
        (tmp_path / "main.py").write_text("pass")
        findfiles_command("*.rs", str(tmp_path), cfg)
        out = capsys.readouterr().out
        assert "No files" in out

    def test_not_a_directory(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: non-existent path. When: findfiles. Then: error."""
        bad = tmp_path / "nope_xyz"
        findfiles_command("*.py", str(bad), cfg)
        out = capsys.readouterr().out
        assert "Error" in out

    def test_caps_results(self, tmp_path: Path, strict_cfg: Config, capsys) -> None:
        """Given: 5 .py files, limit=3. When: findfiles. Then: capped at 3."""
        for i in range(5):
            (tmp_path / f"file{i}.py").write_text("pass")
        findfiles_command("*.py", str(tmp_path), strict_cfg)
        out = capsys.readouterr().out
        assert "capped" in out

    def test_skips_ignored_dirs(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: .py in node_modules. When: findfiles. Then: skipped."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "app.py").write_text("pass")
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "lib.py").write_text("pass")
        findfiles_command("*.py", str(tmp_path), cfg)
        out = capsys.readouterr().out
        assert "app.py" in out
        assert "lib.py" not in out

    def test_nested_pattern(self, tmp_path: Path, cfg: Config, capsys) -> None:
        """Given: files in subdirectories. When: findfiles '**/*.txt'. Then: all found."""
        (tmp_path / "sub").mkdir()
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "sub" / "b.txt").write_text("b")
        findfiles_command("**/*.txt", str(tmp_path), cfg)
        out = capsys.readouterr().out
        assert "a.txt" in out
        assert "b.txt" in out
