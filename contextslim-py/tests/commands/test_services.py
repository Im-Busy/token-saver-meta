"""Tests for services_command — platform-aware service listing."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from contextslim.commands.system.services import services_command


class TestServicesCommand:
    """Given mocked subprocess/systemctl, services_command prints grouped services."""

    SAMPLE_SC_OUTPUT = """\
SERVICE_NAME: WSearch
        TYPE               : 10  WIN32_OWN_PROCESS
        STATE              : 4  RUNNING

SERVICE_NAME: Spooler
        TYPE               : 110  WIN32_OWN_PROCESS  (interactive)
        STATE              : 4  RUNNING

SERVICE_NAME: Themes
        TYPE               : 20  WIN32_SHARE_PROCESS
        STATE              : 1  STOPPED
"""

    SAMPLE_SYSTEMCTL_OUTPUT = """\
  ssh.service                        loaded active     running   OpenSSH server
  nginx.service                      loaded inactive   dead      nginx - high performance web server
  cron.service                       loaded active     running   Regular background program processing daemon
"""

    def test_windows_services(self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
        """Given Windows platform and sc query output. When services_command runs. Then services shown."""
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setattr("subprocess.check_output", lambda *a, **kw: self.SAMPLE_SC_OUTPUT)

        services_command(None, 30)

        out = capsys.readouterr().out
        assert "WSearch" in out
        assert "Spooler" in out
        assert "Themes" in out
        assert "Running: 2 shown" in out
        assert "Stopped: 1 shown" in out

    def test_unix_systemctl_services(self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
        """Given Unix platform and systemctl output. When services_command runs. Then services shown."""
        monkeypatch.setattr("sys.platform", "linux")
        monkeypatch.setattr("subprocess.check_output", lambda *a, **kw: self.SAMPLE_SYSTEMCTL_OUTPUT)

        services_command(None, 30)

        out = capsys.readouterr().out
        assert "ssh" in out
        assert "nginx" in out
        assert "cron" in out

    def test_filter_by_name(self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
        """Given Windows services. When filter='search'. Then only matching shown."""
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setattr("subprocess.check_output", lambda *a, **kw: self.SAMPLE_SC_OUTPUT)

        services_command("search", 30)

        out = capsys.readouterr().out
        assert "WSearch" in out
        assert "Spooler" not in out

    def test_caps_at_limit(self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
        """Given 3 running services at limit=1. Then only 1 running shown."""
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setattr("subprocess.check_output", lambda *a, **kw: self.SAMPLE_SC_OUTPUT)

        services_command(None, 1)

        out = capsys.readouterr().out
        assert "Running: 1 shown" in out

    def test_sc_query_missing(self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
        """Given Windows but sc query fails. When services_command runs. Then empty result."""
        monkeypatch.setattr("sys.platform", "win32")
        def _fail(*a, **kw):  # noqa: ANN202
            raise FileNotFoundError("sc not found")
        monkeypatch.setattr("subprocess.check_output", _fail)

        services_command(None, 30)

        out = capsys.readouterr().out
        assert "Running: 0 shown" in out
        assert "Stopped: 0 shown" in out
