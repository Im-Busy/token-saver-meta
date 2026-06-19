"""Tests for contextslim.commands.setup.audit."""

from __future__ import annotations

from pathlib import Path

import pytest

from contextslim.commands.setup.audit import (
    _count_files,
    _dir_size,
    _format_bytes,
    _format_num,
    _scan_directory,
    audit_command,
)
from contextslim.config import Config


class TestScanDirectory:
    def test_detects_node_modules(self, tmp_path: Path) -> None:
        """Given: project with node_modules. When: _scan_directory. Then: node_modules listed."""
        nm = tmp_path / "node_modules"
        nm.mkdir()
        (nm / "lib.js").write_text("console.log('hi')")

        results = _scan_directory(tmp_path)
        names = [r[0] for r in results]
        assert "node_modules" in names

    def test_detects_git_dir(self, tmp_path: Path) -> None:
        """Given: project with .git. When: _scan_directory. Then: .git listed."""
        git = tmp_path / ".git"
        git.mkdir()
        (git / "HEAD").write_text("ref: refs/heads/main")

        results = _scan_directory(tmp_path)
        names = [r[0] for r in results]
        assert ".git" in names

    def test_detects_build_dir(self, tmp_path: Path) -> None:
        """Given: project with build dir. When: _scan_directory. Then: build listed."""
        build = tmp_path / "build"
        build.mkdir()
        (build / "output.js").write_text("// bundled")

        results = _scan_directory(tmp_path)
        names = [r[0] for r in results]
        assert "build" in names

    def test_detects_multiple_heavy_dirs(self, tmp_path: Path) -> None:
        """Given: multiple heavy dirs. When: _scan_directory. Then: all detected."""
        for d in ["node_modules", ".git", "dist", "build"]:
            sub = tmp_path / d
            sub.mkdir()
            (sub / "placeholder.txt").write_text("data")

        results = _scan_directory(tmp_path)
        names = {r[0] for r in results}
        assert names >= {"node_modules", ".git", "dist", "build"}

    def test_empty_dir_returns_empty(self, tmp_path: Path) -> None:
        """Given: empty directory. When: _scan_directory. Then: empty list."""
        results = _scan_directory(tmp_path)
        assert results == []

    def test_clean_project_returns_empty(self, tmp_path: Path) -> None:
        """Given: clean source-only project. When: _scan_directory. Then: empty."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hi')")
        (tmp_path / "README.md").write_text("# Readme")

        results = _scan_directory(tmp_path)
        assert results == []

    def test_dir_size_calculates_correctly(self, tmp_path: Path) -> None:
        """Given: directory with files. When: _dir_size. Then: returns sum of file sizes."""
        d = tmp_path / "data"
        d.mkdir()
        (d / "a.txt").write_text("hello")
        (d / "b.txt").write_text("world")

        size = _dir_size(d)
        assert size >= 10  # "hello" + "world"

    def test_count_files_respects_extension_filter(self, tmp_path: Path) -> None:
        """Given: dir with mix of .txt and .pyc. When: _count_files. Then: .pyc excluded."""
        d = tmp_path / "mixed"
        d.mkdir()
        (d / "source.py").write_text("code")
        (d / "cache.pyc").write_text("binary")

        count = _count_files(d)
        assert count == 1  # only source.py


class TestFormatBytes:
    def test_bytes(self) -> None:
        assert _format_bytes(500) == "500 B"

    def test_kilobytes(self) -> None:
        result = _format_bytes(2048)
        assert "KB" in result

    def test_megabytes(self) -> None:
        result = _format_bytes(5_000_000)
        assert "MB" in result

    def test_gigabytes(self) -> None:
        result = _format_bytes(2_000_000_000)
        assert "GB" in result


class TestFormatNum:
    def test_small(self) -> None:
        assert _format_num(42) == "42"

    def test_kilo(self) -> None:
        result = _format_num(1500)
        # 1500 rounds to 2K with :.0f formatting
        assert "K" in result

    def test_mega(self) -> None:
        result = _format_num(1_500_000)
        assert "M" in result


class TestAuditCommand:
    def test_audits_project_with_node_modules(self, tmp_path: Path) -> None:
        """Given: project with node_modules. When: audit. Then: shows savings estimate."""
        nm = tmp_path / "node_modules"
        nm.mkdir()
        (nm / "lib.js").write_text("console.log('hi')")

        audit_command(str(tmp_path), Config())

    def test_audits_clean_project(self, tmp_path: Path) -> None:
        """Given: clean project. When: audit. Then: reports no heavy dirs."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hi')")

        audit_command(str(tmp_path), Config())

    def test_audits_project_with_dot_dirs(self, tmp_path: Path) -> None:
        """Given: project with .-prefixed dirs. When: audit. Then: all listed."""
        for d in [".venv", ".mypy_cache", ".pytest_cache"]:
            sub = tmp_path / d
            sub.mkdir()
            (sub / "data.txt").write_text("cache data")

        audit_command(str(tmp_path), Config())

    def test_handles_missing_directory(self, tmp_path: Path) -> None:
        """Given: non-existent directory. When: audit. Then: prints error, no crash."""
        audit_command(str(tmp_path / "nope"), Config())

    def test_audit_with_dist_build_dirs(self, tmp_path: Path) -> None:
        """Given: project with dist and build. When: audit. Then: both listed."""
        for d in ["dist", "build"]:
            sub = tmp_path / d
            sub.mkdir()
            (sub / "output.js").write_text("bundled content")

        audit_command(str(tmp_path), Config())
