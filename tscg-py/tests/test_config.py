"""Tests for tscg.proxy.config — ENV parsing, defaults, validation."""

import os
import pytest
from tscg.proxy.config import ProxyConfig, get_config


class TestDefaults:
    """Given: no ENV vars set. When: get_config() called. Then: return defaults."""

    def test_default_model(self, monkeypatch):
        monkeypatch.delenv("TSCG_MODEL", raising=False)
        cfg = get_config()
        assert cfg.model == "auto"

    def test_default_profile(self, monkeypatch):
        monkeypatch.delenv("TSCG_PROFILE", raising=False)
        cfg = get_config()
        assert cfg.profile is None

    def test_default_downstream_url(self, monkeypatch):
        monkeypatch.delenv("TSCG_DOWNSTREAM_URL", raising=False)
        cfg = get_config()
        assert cfg.downstream_url is None

    def test_default_max_tools(self, monkeypatch):
        monkeypatch.delenv("TSCG_MAX_TOOLS", raising=False)
        cfg = get_config()
        assert cfg.max_tools == 200


class TestEnvParsing:
    """Given: ENV vars set. When: get_config() called. Then: parse correctly."""

    def test_model_from_env(self, monkeypatch):
        monkeypatch.setenv("TSCG_MODEL", "claude-sonnet-4")
        cfg = get_config()
        assert cfg.model == "claude-sonnet-4"

    def test_profile_from_env(self, monkeypatch):
        monkeypatch.setenv("TSCG_PROFILE", "aggressive")
        cfg = get_config()
        assert cfg.profile == "aggressive"

    def test_downstream_url_from_env(self, monkeypatch):
        monkeypatch.setenv("TSCG_DOWNSTREAM_URL", "http://localhost:8080/mcp")
        cfg = get_config()
        assert cfg.downstream_url == "http://localhost:8080/mcp"

    def test_max_tools_from_env(self, monkeypatch):
        monkeypatch.setenv("TSCG_MAX_TOOLS", "50")
        cfg = get_config()
        assert cfg.max_tools == 50

    def test_max_tools_non_numeric_defaults(self, monkeypatch):
        monkeypatch.setenv("TSCG_MAX_TOOLS", "not-a-number")
        cfg = get_config()
        assert cfg.max_tools == 200

    def test_all_env_vars(self, monkeypatch):
        monkeypatch.setenv("TSCG_MODEL", "gpt-5.2")
        monkeypatch.setenv("TSCG_PROFILE", "balanced")
        monkeypatch.setenv("TSCG_DOWNSTREAM_URL", "https://mcp.example.com")
        monkeypatch.setenv("TSCG_MAX_TOOLS", "300")
        cfg = get_config()
        assert cfg.model == "gpt-5.2"
        assert cfg.profile == "balanced"
        assert cfg.downstream_url == "https://mcp.example.com"
        assert cfg.max_tools == 300


class TestValidation:
    """Given: invalid values. When: get_config() called. Then: raise ValueError."""

    def test_invalid_profile_raises(self, monkeypatch):
        monkeypatch.setenv("TSCG_PROFILE", "extreme")
        with pytest.raises(ValueError, match="Invalid TSCG_PROFILE"):
            get_config()

    def test_whitespace_model_is_ok(self, monkeypatch):
        """Model names can be anything — no strict validation beyond non-empty."""
        monkeypatch.setenv("TSCG_MODEL", "  ")
        cfg = get_config()
        assert cfg.model == "  "

    def test_empty_model_is_ok(self, monkeypatch):
        monkeypatch.setenv("TSCG_MODEL", "")
        cfg = get_config()
        assert cfg.model == ""


class TestProxyConfigDataclass:
    """Given: ProxyConfig instance. When: accessing fields. Then: correct types."""

    def test_is_frozen(self):
        cfg = ProxyConfig()
        with pytest.raises(Exception):
            cfg.model = "changed"  # frozen dataclass

    def test_repr(self):
        cfg = ProxyConfig(model="claude", profile="conservative", downstream_url="http://x", max_tools=50)
        r = repr(cfg)
        assert "claude" in r
        assert "conservative" in r
        assert "50" in r
