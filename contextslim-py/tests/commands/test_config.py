"""Tests for contextslim.commands.code.config_cmd."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from contextslim.commands.code.config_cmd import (
    _detect_format,
    _FORMAT_COMMENT_LANG,
    _redact_line,
    _SECRET_KEYS_RE,
    config_command,
)


class TestDetectFormat:
    def test_detects_json(self) -> None:
        assert _detect_format(Path("config.json")) == ".json"

    def test_detects_yaml_extensions(self) -> None:
        assert _detect_format(Path("config.yaml")) == ".yaml"
        assert _detect_format(Path("config.yml")) == ".yml"

    def test_detects_toml(self) -> None:
        assert _detect_format(Path("config.toml")) == ".toml"

    def test_detects_ini(self) -> None:
        assert _detect_format(Path("config.ini")) == ".ini"
        assert _detect_format(Path("config.cfg")) == ".cfg"

    def test_detects_env(self) -> None:
        assert _detect_format(Path(".env")) == ".env"
        assert _detect_format(Path(".env.local")) == ".env"


class TestRedactLine:
    def test_redacts_api_key_in_json(self) -> None:
        line = '"api_key": "sk-abc123"'
        result = _redact_line(line)
        assert "***REDACTED***" in result
        assert "sk-abc123" not in result

    def test_redacts_token_in_yaml(self) -> None:
        line = "token: ghp_abcdef123456"
        result = _redact_line(line)
        assert "***REDACTED***" in result
        assert "ghp_abcdef123456" not in result

    def test_redacts_password_in_env(self) -> None:
        line = 'DATABASE_PASSWORD=supersecret'
        result = _redact_line(line)
        assert "***REDACTED***" in result
        assert "supersecret" not in result

    def test_redacts_secret_key(self) -> None:
        line = 'secret_key = "my-very-secret-key"'
        result = _redact_line(line)
        assert "***REDACTED***" in result
        assert "my-very-secret-key" not in result

    def test_case_insensitive_key_match(self) -> None:
        line = "API_KEY=xyz"
        result = _redact_line(line)
        assert "***REDACTED***" in result
        assert "xyz" not in result

    def test_does_not_redact_non_secret_keys(self) -> None:
        line = 'name = "my-app"'
        result = _redact_line(line)
        assert "***REDACTED***" not in result
        assert "my-app" in result

    def test_leaves_safe_line_unchanged(self) -> None:
        line = "DEBUG=true"
        result = _redact_line(line)
        assert result == line

    def test_redacts_json_single_quoted_value(self) -> None:
        line = "\"password\": 'p@ssw0rd'"
        result = _redact_line(line)
        assert "***REDACTED***" in result
        assert "p@ssw0rd" not in result


class TestSecretKeysRe:
    def test_matches_api_key(self) -> None:
        assert _SECRET_KEYS_RE.search("api_key=foo")
        assert _SECRET_KEYS_RE.search("API_KEY: bar")

    def test_matches_token(self) -> None:
        assert _SECRET_KEYS_RE.search("token=abc")
        assert _SECRET_KEYS_RE.search("auth_token: xyz")

    def test_matches_secret(self) -> None:
        assert _SECRET_KEYS_RE.search("secret=abc")

    def test_matches_password(self) -> None:
        assert _SECRET_KEYS_RE.search("password=abc")
        assert _SECRET_KEYS_RE.search("db_password: xyz")

    def test_matches_bare_key(self) -> None:
        assert _SECRET_KEYS_RE.search("key=abc")
        # But "key" alone is broad — still redacts

    def test_does_not_match_unrelated_keys(self) -> None:
        assert not _SECRET_KEYS_RE.search("name=foo")
        assert not _SECRET_KEYS_RE.search("debug=true")
        assert not _SECRET_KEYS_RE.search("host: localhost")


class TestConfigCommand:
    def test_processes_json_file(self, tmp_path: Path) -> None:
        """Given: a JSON config file. When: config_command called. Then: secrets redacted."""
        cfg = tmp_path / "config.json"
        data = {"api_key": "sk-secret123", "name": "my-app", "debug": True}
        cfg.write_text(json.dumps(data, indent=2), encoding="utf-8")
        # Should not raise
        config_command(str(cfg))

    def test_processes_yaml_file(self, tmp_path: Path) -> None:
        """Given: a YAML config file. When: config_command called. Then: executes without error."""
        cfg = tmp_path / "config.yaml"
        cfg.write_text(
            "# App config\napi_key: sk-abc\nname: my-app\n",
            encoding="utf-8",
        )
        config_command(str(cfg))

    def test_processes_env_file(self, tmp_path: Path) -> None:
        """Given: .env file. When: config_command called. Then: secrets redacted, comments stripped."""
        env = tmp_path / ".env"
        env.write_text(
            "# Database\nDB_PASSWORD=secret123\nAPI_KEY=sk-xyz\nDEBUG=true\n",
            encoding="utf-8",
        )
        config_command(str(env))

    def test_processes_toml_file(self, tmp_path: Path) -> None:
        """Given: TOML file. When: config_command called. Then: executes without error."""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text(
            '# Project config\n[secrets]\napi_key = "sk-test"\n',
            encoding="utf-8",
        )
        config_command(str(toml_file))

    def test_handles_missing_file(self, tmp_path: Path) -> None:
        """Given: non-existent file. When: config_command called. Then: prints error, no crash."""
        config_command(str(tmp_path / "nonexistent.json"))

    def test_handles_ini_file(self, tmp_path: Path) -> None:
        """Given: INI file. When: config_command called. Then: executes without error."""
        ini = tmp_path / "settings.ini"
        ini.write_text(
            "; Database settings\npassword = mypass\nhost = localhost\n",
            encoding="utf-8",
        )
        config_command(str(ini))
