"""Tests for sysinfo_command — compact OS/hardware info."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from contextslim.commands.system.sysinfo import sysinfo_command


class TestSysinfoCommand:
    """Given mocked psutil, sysinfo_command prints a rich table with system info."""

    @pytest.fixture(autouse=True)
    def _mock_psutil(self, monkeypatch: pytest.MonkeyPatch) -> MagicMock:
        """Replace psutil with a mock that returns stable values."""
        mock = MagicMock()
        mock.cpu_count.side_effect = lambda logical=True: 8 if logical else 4
        mock.cpu_percent.return_value = 23.5
        mock.virtual_memory.return_value = MagicMock(
            total=16 * 1024**3,
            available=8 * 1024**3,
            used=8 * 1024**3,
            percent=50.0,
        )
        mock.swap_memory.return_value = MagicMock(
            total=4 * 1024**3,
            used=1 * 1024**3,
            percent=25.0,
        )
        mock.disk_usage.return_value = MagicMock(
            total=256 * 1024**3,
            used=128 * 1024**3,
            percent=50.0,
        )
        mock.boot_time.return_value = 1700000000.0
        # inject mock into sys.modules
        import sys
        sys.modules["psutil"] = mock
        return mock

    def test_shows_cpu_info(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Given mocked psutil. When sysinfo_command runs. Then CPU lines appear."""
        sysinfo_command()
        out = capsys.readouterr().out
        assert "8 logical" in out
        assert "physical" in out

    def test_shows_memory_info(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Given mocked psutil. When sysinfo_command runs. Then memory appears."""
        sysinfo_command()
        out = capsys.readouterr().out
        assert "Memory" in out
        assert "8.0 GB" in out
        assert "16.0 GB" in out

    def test_shows_disk_info(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Given mocked psutil. When sysinfo_command runs. Then disk appears."""
        sysinfo_command()
        out = capsys.readouterr().out
        assert "Disk" in out
        assert "128.0 GB" in out

    def test_shows_boot_uptime(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Given mocked psutil. When sysinfo_command runs. Then boot/uptime appears."""
        sysinfo_command()
        out = capsys.readouterr().out
        assert "Boot Time" in out
        assert "Uptime" in out

    def test_psutil_missing(self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
        """Given psutil not importable. When sysinfo_command runs. Then install hint shown."""
        import sys
        sys.modules.pop("psutil", None)
        # Make import fail
        import builtins
        orig_import = builtins.__import__
        def block_psutil(name, *args, **kwargs):  # noqa: ANN202
            if name == "psutil":
                raise ImportError("No module named 'psutil'")
            return orig_import(name, *args, **kwargs)
        monkeypatch.setattr(builtins, "__import__", block_psutil)

        sysinfo_command()
        out = capsys.readouterr().out
        assert "psutil not installed" in out
