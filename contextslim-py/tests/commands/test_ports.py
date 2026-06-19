"""Tests for contextslim.commands.system.ports."""

from __future__ import annotations

from unittest.mock import patch

import psutil
import pytest

from contextslim.commands.system.ports import ports_command


def _make_conn(ip: str, port: int, status: str = "LISTEN", pid: int = 1) -> object:
    """Construct a mock psutil connection."""
    from psutil._ntuples import addr, sconn  # type: ignore[import-not-found]

    return sconn(
        fd=-1,
        family=2,  # AF_INET
        type=1,    # SOCK_STREAM
        laddr=addr(ip=ip, port=port),
        raddr=(),
        status=status,
        pid=pid,
    )


class TestPortsCommand:
    """Open ports listing via psutil."""

    def test_no_connections(self, capsys) -> None:
        """Given: no open connections. When: ports. Then: no ports message."""
        with patch("psutil.net_connections", return_value=[]):
            ports_command()
        out = capsys.readouterr().out
        assert "No open ports" in out

    def test_shows_listening_port(self, capsys) -> None:
        """Given: one listening connection. When: ports. Then: shown."""
        conn = _make_conn("127.0.0.1", 8080)
        with patch("psutil.net_connections", return_value=[conn]), \
             patch("psutil.Process") as mock_proc:
            mock_proc.return_value.name.return_value = "python"
            ports_command()
        out = capsys.readouterr().out
        assert "python" in out
        assert "8080" in out

    def test_filters_by_name(self, capsys) -> None:
        """Given: multiple processes. When: ports --filter nginx. Then: only nginx."""
        conn1 = _make_conn("0.0.0.0", 80, pid=100)
        conn2 = _make_conn("0.0.0.0", 443, pid=200)
        with patch("psutil.net_connections", return_value=[conn1, conn2]), \
             patch("psutil.Process") as mock_proc:
            mock_proc.return_value.name.return_value = "nginx"
            ports_command(name_filter="nginx")
        out = capsys.readouterr().out
        assert "nginx" in out

    def test_filter_no_match(self, capsys) -> None:
        """Given: connections. When: filter 'zzz'. Then: no ports."""
        conn = _make_conn("127.0.0.1", 3000)
        with patch("psutil.net_connections", return_value=[conn]), \
             patch("psutil.Process") as mock_proc:
            mock_proc.return_value.name.return_value = "node"
            ports_command(name_filter="zzz")
        out = capsys.readouterr().out
        assert "No open ports" in out

    def test_permission_error(self, capsys) -> None:
        """Given: PermissionError from psutil. When: ports. Then: graceful."""
        with patch("psutil.net_connections", side_effect=PermissionError):
            ports_command()
        out = capsys.readouterr().out
        assert "elevated permissions" in out

    def test_filter_by_port_number(self, capsys) -> None:
        """Given: port 5432. When: filter '5432'. Then: matched."""
        conn = _make_conn("127.0.0.1", 5432, pid=42)
        with patch("psutil.net_connections", return_value=[conn]), \
             patch("psutil.Process") as mock_proc:
            mock_proc.return_value.name.return_value = "postgres"
            ports_command(name_filter="5432")
        out = capsys.readouterr().out
        assert "postgres" in out
