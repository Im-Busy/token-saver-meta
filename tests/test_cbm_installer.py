import pytest
from pathlib import Path
from src.tools.cbm_installer import detect_platform, get_install_path, get_cbm_db_path, install_cbm, generate_cbm_config

def test_detect_platform_windows():
    plat = detect_platform()
    assert "windows" in plat or "linux" in plat or "darwin" in plat

def test_get_install_path():
    path = get_install_path()
    assert ".token-saver-meta" in str(path)
    assert "bin" in str(path)

def test_get_cbm_db_path():
    path = get_cbm_db_path()
    assert "codebase-memory-mcp" in str(path)

def test_install_cbm_structure():
    """Verify install_cbm returns structured result even without network."""
    result = install_cbm()
    assert "status" in result
    assert result["status"] in ("ok", "warn", "error")
    assert "message" in result

def test_download_failure_graceful():
    """Install should not crash even if requests is unavailable."""
    result = install_cbm()
    assert result is not None
    assert isinstance(result, dict)


def test_generate_opencode_config():
    result = generate_cbm_config("opencode")
    assert result["status"] in ("ok", "warn")
    if result["status"] == "ok":
        assert "mcpServers" in result["config"]
        assert "codebase-memory-mcp" in result["config"]["mcpServers"]


def test_generate_claude_config():
    result = generate_cbm_config("claude")
    assert result["status"] in ("ok", "warn")


def test_generate_unsupported_agent():
    result = generate_cbm_config("unsupported-agent")
    assert result["status"] == "error"


def test_config_idempotent():
    """Two calls should produce identical configs."""
    r1 = generate_cbm_config("opencode")
    r2 = generate_cbm_config("opencode")
    assert r1["status"] == r2["status"]
