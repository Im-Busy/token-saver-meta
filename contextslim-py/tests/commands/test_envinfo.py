"""Tests for envinfo_command — environment variables grouped, sensitive vars hidden."""

from __future__ import annotations

import os

import pytest

from contextslim.commands.system.envinfo import envinfo_command


class TestEnvinfoCommand:
    """Given controlled os.environ, envinfo_command prints grouped, redacted output."""

    @pytest.fixture(autouse=True)
    def _clear_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Set a controlled minimal environment."""
        monkeypatch.setattr(os, "environ", {})

    def test_groups_by_category(self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
        """Given vars spanning categories. When envinfo runs. Then grouped correctly."""
        env = {
            "PATH": "/usr/bin",
            "HOME": "/home/user",
            "USER": "dev",
            "PYTHONPATH": "/src",
            "NODE_ENV": "development",
            "DOCKER_HOST": "tcp://localhost",
            "AWS_REGION": "us-east-1",
            "GIT_AUTHOR_NAME": "Alice",
            "CI": "true",
            "OTHER_VAR": "other_value",
        }
        monkeypatch.setattr(os, "environ", env)

        envinfo_command(None)

        out = capsys.readouterr().out
        assert "PATH" in out
        assert "HOME" in out
        assert "USER" in out
        assert "PYTHONPATH" in out
        assert "NODE_ENV" in out
        assert "DOCKER_HOST" in out
        assert "AWS_REGION" in out
        assert "GIT_AUTHOR_NAME" in out
        assert "CI" in out
        assert "OTHER_VAR" in out

    def test_redacts_sensitive_vars(self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
        """Given vars with KEY/TOKEN/SECRET/PASSWORD. When envinfo runs. Then ***HIDDEN***."""
        env = {
            "API_KEY": "sk-12345",
            "SECRET_TOKEN": "mysecret",
            "DB_PASSWORD": "pass123",
            "AWS_ACCESS_KEY_ID": "AKIA123",
            "MY_SECRET": "hidden",
            "NORMAL_VAR": "visible",
        }
        monkeypatch.setattr(os, "environ", env)

        envinfo_command(None)

        out = capsys.readouterr().out
        assert "***HIDDEN***" in out
        assert "visible" in out
        assert "sk-12345" not in out
        assert "mysecret" not in out
        assert "pass123" not in out

    def test_filter_by_name(self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
        """Given filter='HOME'. When envinfo runs. Then only matching vars shown."""
        env = {
            "HOME": "/home/user",
            "USER": "dev",
            "SHELL": "/bin/bash",
        }
        monkeypatch.setattr(os, "environ", env)

        envinfo_command("HOME")

        out = capsys.readouterr().out
        assert "HOME" in out
        assert "USER" not in out
        assert "SHELL" not in out

    def test_empty_environment(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Given empty os.environ. When envinfo runs. Then no crash."""
        envinfo_command(None)
        out = capsys.readouterr().out
        assert "Environment Variables" in out

    def test_shows_values_for_normal_vars(self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
        """Given normal vars. When envinfo runs. Then actual values shown."""
        env = {"EDITOR": "vim", "LANG": "en_US.UTF-8"}
        monkeypatch.setattr(os, "environ", env)

        envinfo_command(None)

        out = capsys.readouterr().out
        assert "vim" in out
        assert "en_US.UTF-8" in out
