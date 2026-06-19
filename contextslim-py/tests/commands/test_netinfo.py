"""Tests for netinfo_command — network interfaces info."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from contextslim.commands.system.netinfo import netinfo_command


def _make_snicaddr(family_str: str, address: str, netmask: str = "", broadcast: str = "") -> MagicMock:
    """Create a mock snicaddr with a str-family for display."""
    addr = MagicMock()
    addr.family = family_str
    addr.address = address
    addr.netmask = netmask
    addr.broadcast = broadcast
    return addr


def _make_ifstats(isup: bool = True, speed: int = 1000) -> MagicMock:
    """Create a mock ifstats."""
    stats = MagicMock()
    stats.isup = isup
    stats.speed = speed
    return stats


class TestNetinfoCommand:
    """Given mocked psutil, netinfo_command prints network interfaces."""

    @pytest.fixture(autouse=True)
    def _mock_psutil(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Replace psutil with a mock."""
        import sys
        sys.modules["psutil"] = MagicMock()

    def test_shows_interfaces(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Given 2 interfaces. When netinfo_command runs. Then both shown."""
        import psutil
        psutil.net_if_addrs.return_value = {
            "eth0": [
                _make_snicaddr("AddressFamily.AF_INET", "192.168.1.10"),
                _make_snicaddr("AddressFamily.AF_INET6", "fe80::1"),
                _make_snicaddr("AddressFamily.AF_LINK", "00:11:22:33:44:55"),
            ],
            "lo": [
                _make_snicaddr("AddressFamily.AF_INET", "127.0.0.1"),
            ],
        }
        psutil.net_if_stats.return_value = {
            "eth0": _make_ifstats(isup=True, speed=1000),
            "lo": _make_ifstats(isup=True, speed=0),
        }

        netinfo_command()

        out = capsys.readouterr().out
        assert "eth0" in out
        assert "lo" in out
        assert "192.168.1.10" in out
        assert "fe80::1" in out
        assert "00:11:22:33:44:55" in out

    def test_shows_status(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Given an interface that is down. When netinfo_command runs. Then status='down'."""
        import psutil
        psutil.net_if_addrs.return_value = {
            "eth0": [_make_snicaddr("AddressFamily.AF_INET", "10.0.0.1")],
        }
        psutil.net_if_stats.return_value = {
            "eth0": _make_ifstats(isup=False, speed=0),
        }

        netinfo_command()

        out = capsys.readouterr().out
        assert "down" in out
        assert "up" not in out

    def test_shows_speed(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Given an interface with speed. When netinfo_command runs. Then speed shown."""
        import psutil
        psutil.net_if_addrs.return_value = {
            "wlan0": [_make_snicaddr("AddressFamily.AF_INET", "10.0.0.2")],
        }
        psutil.net_if_stats.return_value = {
            "wlan0": _make_ifstats(isup=True, speed=866),
        }

        netinfo_command()

        out = capsys.readouterr().out
        assert "866 Mbps" in out

    def test_empty_interface_list(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Given no interfaces. When netinfo_command runs. Then table still renders."""
        import psutil
        psutil.net_if_addrs.return_value = {}
        psutil.net_if_stats.return_value = {}

        netinfo_command()

        out = capsys.readouterr().out
        assert "Network Interfaces" in out

    def test_psutil_missing(self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
        """Given psutil not importable. When netinfo_command runs. Then install hint shown."""
        import sys
        sys.modules.pop("psutil", None)
        import builtins
        orig_import = builtins.__import__
        def block_psutil(name, *args, **kwargs):  # noqa: ANN202
            if name == "psutil":
                raise ImportError("No module named 'psutil'")
            return orig_import(name, *args, **kwargs)
        monkeypatch.setattr(builtins, "__import__", block_psutil)

        netinfo_command()
        out = capsys.readouterr().out
        assert "psutil not installed" in out
