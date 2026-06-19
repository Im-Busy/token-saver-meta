"""Tests for src/uninstall.py — marker removal, MCP cleanup, user config preservation."""
import json
from pathlib import Path
from unittest.mock import patch

from src.uninstall import uninstall_all


def test_uninstall_removes_agents_md_section(tmp_path: Path):
    """Create temp AGENTS.md with TOKEN_SAVER markers, run uninstall, verify markers gone."""
    agents_md = tmp_path / "AGENTS.md"
    agents_md.write_text(
        "# Project Docs\n\nSome content.\n\n<!-- TOKEN_SAVER_START -->\n"
        "token-saver content here\n<!-- TOKEN_SAVER_END -->\n\nMore content.\n"
    )
    # Create a platform detection marker so detect_platforms finds something
    (tmp_path / ".kilo").mkdir()
    (tmp_path / "kilo.json").write_text("{}")

    with patch("builtins.input", return_value="y"):
        result = uninstall_all(tmp_path, force=False)

    # Force path is also accepted
    assert result.get("status") == "ok"
    updated = agents_md.read_text()
    assert "<!-- TOKEN_SAVER_START -->" not in updated
    assert "<!-- TOKEN_SAVER_END -->" not in updated
    assert "# Project Docs" in updated
    assert "More content" in updated


def test_uninstall_removes_mcp_entries(tmp_path: Path):
    """Create temp MCP config with CGC entries, run uninstall, verify CGC entries gone."""
    # Detection markers for "kilo" platform
    (tmp_path / ".kilo").mkdir()
    kilo_cfg_dir = tmp_path / ".kilo"
    kilo_cfg_dir.mkdir(parents=True, exist_ok=True)
    kilo_json = kilo_cfg_dir / "kilo.json"
    kilo_json_content = {
        "mcp": {
            "codegraphcontext": {
                "type": "local",
                "command": ["npx", "-y", "@codegraphcontext/mcp"],
            },
            # Should be removed — another token-saver prefix
            "gitnexus": {
                "type": "local",
                "command": ["npx", "-y", "gitnexus"],
            },
        }
    }
    kilo_json.write_text(json.dumps(kilo_json_content))
    # Also put a kilo.json marker at root for detection
    (tmp_path / "kilo.json").write_text("{}")

    with patch("builtins.input", return_value="y"):
        result = uninstall_all(tmp_path, force=False)

    assert result.get("status") == "ok"
    cleaned = json.loads(kilo_json.read_text())
    assert "codegraphcontext" not in cleaned.get("mcp", {})
    assert "gitnexus" not in cleaned.get("mcp", {})


def test_uninstall_preserves_user_config(tmp_path: Path):
    """User MCP entry alongside token-saver entries — uninstall preserves user entry."""
    (tmp_path / ".kilo").mkdir()
    kilo_cfg_dir = tmp_path / ".kilo"
    kilo_cfg_dir.mkdir(parents=True, exist_ok=True)
    kilo_json = kilo_cfg_dir / "kilo.json"
    kilo_json_content = {
        "mcp": {
            "codegraphcontext": {
                "type": "local",
                "command": ["npx", "-y", "@codegraphcontext/mcp"],
            },
            "user-server": {
                "type": "local",
                "command": ["my-custom-tool"],
            },
        }
    }
    kilo_json.write_text(json.dumps(kilo_json_content))
    (tmp_path / "kilo.json").write_text("{}")

    with patch("builtins.input", return_value="y"):
        result = uninstall_all(tmp_path, force=False)

    assert result.get("status") == "ok"
    cleaned = json.loads(kilo_json.read_text())
    assert "codegraphcontext" not in cleaned.get("mcp", {})
    assert "user-server" in cleaned.get("mcp", {})
    assert cleaned["mcp"]["user-server"]["command"] == ["my-custom-tool"]
