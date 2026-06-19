"""Tests for contextslim.commands.system.disk."""

from __future__ import annotations

from pathlib import Path

import pytest

from contextslim.commands.system.disk import disk_command, _fmt_bytes


class TestFmtBytes:
    """Human-readable byte formatting."""

    def test_bytes(self) -> None:
        assert _fmt_bytes(0) == "0.0 B"
        assert _fmt_bytes(500) == "500.0 B"

    def test_kb(self) -> None:
        assert _fmt_bytes(1024) == "1.0 KB"
        assert _fmt_bytes(1536) == "1.5 KB"

    def test_mb(self) -> None:
        assert _fmt_bytes(1024 * 1024) == "1.0 MB"

    def test_gb(self) -> None:
        assert _fmt_bytes(1024 ** 3) == "1.0 GB"


class TestDiskCommand:
    """Filesystem overview with directory sizes."""

    def test_shows_disk_usage(self, tmp_path: Path, capsys) -> None:
        """Given: a directory. When: disk. Then: usage stats shown."""
        (tmp_path / "file1.txt").write_text("hello")
        disk_command(str(tmp_path))
        out = capsys.readouterr().out
        assert "Total" in out
        assert "Used" in out
        assert "Free" in out

    def test_shows_directory_sizes(self, tmp_path: Path, capsys) -> None:
        """Given: subdirectories with files. When: disk. Then: sizes listed."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hello world')")
        (tmp_path / "empty").mkdir()
        disk_command(str(tmp_path))
        out = capsys.readouterr().out
        assert "src" in out
        assert "empty" in out

    def test_not_a_directory(self, tmp_path: Path, capsys) -> None:
        """Given: non-directory path. When: disk. Then: error."""
        bad = tmp_path / "noexist_xyz"
        disk_command(str(bad))
        out = capsys.readouterr().out
        assert "Error" in out

    def test_formats_sizes_readably(self, tmp_path: Path, capsys) -> None:
        """Given: files. When: disk. Then: sizes are human-readable."""
        (tmp_path / "data.bin").write_bytes(b"\x00" * 2048)
        disk_command(str(tmp_path))
        out = capsys.readouterr().out
        assert "KB" in out or "B" in out
