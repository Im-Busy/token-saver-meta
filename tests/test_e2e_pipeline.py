"""End-to-end integration tests for the Phase 07b installer pipeline.

Tests 1-3: Full pipeline with mocked sub-modules (dry run, node-only, failure isolation).
Test 4: Install/uninstall cycle using real agents_injector + uninstall functions.
Test 5: Summary report formatter with known results dict.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.installer import main
from src.summary import format_summary


# ============================================================================
# Helpers — prerequisite mock builders
# ============================================================================

def _all_ok_prereqs(*, node_only_fallback: bool = False) -> dict:
    """Mock prerequisites with all tools present or Python/uv missing."""
    py_status = {"status": "missing", "version": None, "path": None} if node_only_fallback else {"status": "ok", "version": "Python 3.12.0", "path": "/usr/bin/python"}
    uv_status = {"status": "missing", "version": None, "path": None} if node_only_fallback else {"status": "ok", "version": "uv 0.6.0", "path": "/usr/bin/uv"}
    issues = ["Python not found. Install from https://python.org", "uv not found. Install with: pip install uv"] if node_only_fallback else []
    return {
        "node": {"status": "ok", "version": "v22.0.0", "path": "/usr/bin/node"},
        "npm": {"status": "ok", "version": "10.0.0", "path": "/usr/bin/npm"},
        "npx": {"status": "ok"},
        "python": py_status,
        "uv": uv_status,
        "internet": {"status": "ok"},
        "disk_free_mb": 5000.0,
        "can_write": True,
        "all_ok": True,
        "node_only_fallback": node_only_fallback,
        "issues": issues,
    }


# ============================================================================
# Test 1: Full Pipeline Dry Run
# ============================================================================

@patch("src.config_gen.detect_platforms")
@patch("src.agents_injector.inject_agents_md_section")
@patch("src.prerequisites.check_prerequisites")
@patch("src.cgc_installer.install_cgc")
@patch("src.oneshot_installer.install_one_shot_tools")
@patch("src.rtk_installer.install_rtk")
def test_full_pipeline_dry_run(
    mock_rtk: MagicMock,
    mock_oneshot: MagicMock,
    mock_cgc: MagicMock,
    mock_pre: MagicMock,
    mock_inject: MagicMock,
    mock_detect: MagicMock,
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
):
    """Run full pipeline with all tools already installed — verify skip statuses and summary."""
    mock_detect.return_value = ["kilo", "claude-code"]
    mock_inject.return_value = {
        "kilo": {"status": "unchanged"},
        "claude-code": {"status": "unchanged"},
    }
    mock_pre.return_value = _all_ok_prereqs()
    mock_cgc.return_value = {
        "status": "skip",
        "platforms": {},
        "message": "All servers already configured",
    }
    mock_oneshot.return_value = {
        "codesight": {"status": "skip", "message": "CODESIGHT.md already exists"},
        "repomix": {"status": "skip", "message": "repomix output already exists: repomix-output.txt"},
        "gitignore_updated": False,
    }
    mock_rtk.return_value = {
        "status": "ok",
        "version": "1.2.3",
        "install_method": "pre-installed",
        "hook_status": "ok",
        "message": "",
    }

    results = main(tmp_path)

    # All 7 phases returned results
    assert "base_layer" in results
    assert "platforms" in results
    assert "prerequisites" in results
    assert "cgc" in results
    assert "oneshot" in results
    assert "rtk" in results

    # Base layer injected
    assert results["base_layer"]["status"] == "ok"
    assert results["platforms"]["detected"] == ["kilo", "claude-code"]

    # Intelligence layer: CGC skipped, oneshot skipped
    cgc = results.get("cgc", {})
    assert cgc.get("status") == "ok"
    cgc_result = cgc.get("result", {})
    assert cgc_result.get("status") == "skip"

    oneshot = results.get("oneshot", {})
    assert oneshot.get("status") == "ok"
    oneshot_result = oneshot.get("result", {})
    assert oneshot_result.get("codesight", {}).get("status") == "skip"
    assert oneshot_result.get("repomix", {}).get("status") == "skip"

    # Compression: RTK ok (pre-installed)
    rtk = results.get("rtk", {})
    assert rtk.get("status") == "ok"
    rtk_result = rtk.get("result", {})
    assert rtk_result.get("status") == "ok"
    assert rtk_result.get("version") == "1.2.3"

    # Summary printed to stdout
    captured = capsys.readouterr()
    assert "Token Saver Meta" in captured.out
    assert "tools active" in captured.out


# ============================================================================
# Test 2: Full Pipeline Node-Only Fallback
# ============================================================================

@patch("src.config_gen.detect_platforms")
@patch("src.agents_injector.inject_agents_md_section")
@patch("src.prerequisites.check_prerequisites")
@patch("src.oneshot_installer.install_one_shot_tools")
@patch("src.rtk_installer.install_rtk")
def test_full_pipeline_node_only(
    mock_rtk: MagicMock,
    mock_oneshot: MagicMock,
    mock_pre: MagicMock,
    mock_inject: MagicMock,
    mock_detect: MagicMock,
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
):
    """Node-only mode: Python/uv missing, Node tools still install. Summary shows fallback."""
    mock_detect.return_value = ["kilo"]
    mock_inject.return_value = {"kilo": {"status": "appended"}}
    mock_pre.return_value = _all_ok_prereqs(node_only_fallback=True)
    mock_oneshot.return_value = {
        "codesight": {"status": "ok", "message": "CODESIGHT.md generated"},
        "repomix": {"status": "ok", "message": "repomix output generated: repomix-output.txt"},
        "gitignore_updated": True,
    }
    mock_rtk.return_value = {
        "status": "ok",
        "version": "1.0.0",
        "install_method": "pre-installed",
        "hook_status": "ok",
        "message": "",
    }

    results = main(tmp_path)

    # Node-only fallback flag recorded
    assert results["node_only_fallback"] is True

    # CGC skipped (npx available in mock but prereqs controls it — npx is still ok in node_only mode)
    # Wait: prereqs has npx={"status":"ok"}, node_only_fallback checks npx status.
    # In node_only_fallback mode: node/npm/npx are ok, Python/uv are missing.
    # So npx IS ok — CGC should install.
    cgc = results.get("cgc", {})
    assert "status" in cgc  # CGC install attempted

    # One-shot tools installed
    mock_oneshot.assert_called_once()
    oneshot = results.get("oneshot", {})
    assert oneshot.get("result", {}).get("codesight", {}).get("status") == "ok"

    # RTK installed
    mock_rtk.assert_called_once()

    # Summary records fallback notice
    captured = capsys.readouterr()
    assert "Node-only mode" in captured.out


# ============================================================================
# Test 3: Full Pipeline with CGC Failure (Per-Tool Isolation)
# ============================================================================

@patch("src.config_gen.detect_platforms")
@patch("src.agents_injector.inject_agents_md_section")
@patch("src.prerequisites.check_prerequisites")
@patch("src.cgc_installer.install_cgc")
@patch("src.oneshot_installer.install_one_shot_tools")
@patch("src.rtk_installer.install_rtk")
def test_full_pipeline_with_cgc_failure(
    mock_rtk: MagicMock,
    mock_oneshot: MagicMock,
    mock_cgc: MagicMock,
    mock_pre: MagicMock,
    mock_inject: MagicMock,
    mock_detect: MagicMock,
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
):
    """CGC raises RuntimeError — codesight, Repomix, RTK still install. Summary shows CGC=error."""
    mock_detect.return_value = ["kilo", "claude-code"]
    mock_inject.return_value = {
        "kilo": {"status": "appended"},
        "claude-code": {"status": "appended"},
    }
    mock_pre.return_value = _all_ok_prereqs()
    mock_cgc.side_effect = RuntimeError("CGC install failed: network timeout")
    mock_oneshot.return_value = {
        "codesight": {"status": "ok", "message": "CODESIGHT.md generated"},
        "repomix": {"status": "ok", "message": "repomix output generated: repomix-output.txt"},
        "gitignore_updated": True,
    }
    mock_rtk.return_value = {
        "status": "ok",
        "version": "1.0.0",
        "install_method": "pre-installed",
        "hook_status": "ok",
        "message": "",
    }

    results = main(tmp_path)

    # CGC errored
    cgc = results.get("cgc", {})
    assert cgc.get("status") == "error"
    assert "CGC install failed" in cgc.get("result", "")

    # codesight and Repomix still installed (failure isolation)
    mock_oneshot.assert_called_once()
    oneshot = results.get("oneshot", {})
    oneshot_result = oneshot.get("result", {})
    assert oneshot_result.get("codesight", {}).get("status") == "ok"
    assert oneshot_result.get("repomix", {}).get("status") == "ok"

    # RTK still installed
    mock_rtk.assert_called_once()

    # Summary shows CGC as error
    captured = capsys.readouterr()
    assert "Token Saver Meta" in captured.out
    assert "❌" in captured.out or "error" in captured.out.lower()


# ============================================================================
# Test 4: Install / Uninstall Cycle
# ============================================================================

def test_install_uninstall_cycle(tmp_path: Path):
    """Inject token-saver protocol + MCP entries, then uninstall using individual functions. Verify clean removal."""
    from src.agents_injector import (
        START_MARKER,
        END_MARKER,
        inject_agents_md_section,
        remove_injected_section,
        is_injected,
    )
    from src.uninstall import uninstall_cgc_mcp
    from src.config_gen import detect_platforms

    # ---- Setup: create a project with kilo platform markers ----
    # Detection marker: .kilo/ directory
    kilo_dir = tmp_path / ".kilo"
    kilo_dir.mkdir()

    # AGENTS.md with pre-existing content
    agents_md = tmp_path / "AGENTS.md"
    preamble = "# My Project Rules\n\nThese rules are important.\n"
    postamble = "\n# Appendix\n\nAdditional notes here.\n"
    agents_md.write_text(preamble + postamble, encoding="utf-8")

    # Inject token-saver protocol into AGENTS.md
    platforms = detect_platforms(tmp_path)
    assert "kilo" in platforms, f"Expected kilo detected, got {platforms}"

    inject_results = inject_agents_md_section(tmp_path, platforms)
    assert "kilo" in inject_results
    assert is_injected(agents_md), "AGENTS.md should have token-saver markers after injection"

    injected_content = agents_md.read_text(encoding="utf-8")
    assert START_MARKER in injected_content
    assert END_MARKER in injected_content
    assert "Token Saving Protocol" in injected_content
    assert preamble.strip() in injected_content, "Pre-existing preamble preserved"

    # ---- Setup: create .kilo/kilo.json with CGC MCP entries ----
    kilo_json = tmp_path / ".kilo" / "kilo.json"
    mcp_config = {
        "mcp": {
            "codegraphcontext": {
                "type": "local",
                "command": ["npx", "-y", "codegraph", "mcp"],
                "workdir": str(tmp_path),
            },
            "user-server": {
                "type": "local",
                "command": ["echo", "hello"],
            },
        }
    }
    kilo_json.write_text(json.dumps(mcp_config, indent=2), encoding="utf-8")

    # ---- Act: uninstall AGENTS.md section ----
    remove_result = remove_injected_section(agents_md)
    assert remove_result["status"] == "removed"

    # ---- Verify: AGENTS.md section removed ----
    final_agents_md = agents_md.read_text(encoding="utf-8")
    assert START_MARKER not in final_agents_md, "Token-saver start marker should be removed"
    assert END_MARKER not in final_agents_md, "Token-saver end marker should be removed"
    assert "Token Saving Protocol" not in final_agents_md
    assert not is_injected(agents_md), "is_injected should return False after uninstall"

    # Pre-existing content preserved
    assert "My Project Rules" in final_agents_md
    assert "These rules are important" in final_agents_md
    assert "Appendix" in final_agents_md
    assert "Additional notes here" in final_agents_md

    # ---- Act: uninstall MCP entries ----
    cgc_result = uninstall_cgc_mcp(tmp_path, ["kilo"])
    assert cgc_result.get("kilo", {}).get("status") == "ok"

    # ---- Verify: MCP entries removed ----
    cleaned_config = json.loads(kilo_json.read_text(encoding="utf-8"))
    assert "mcp" in cleaned_config
    assert "codegraphcontext" not in cleaned_config["mcp"], "CGC MCP entry should be removed"
    assert "user-server" in cleaned_config["mcp"], "User's MCP server should be preserved"
    assert cleaned_config["mcp"]["user-server"]["command"] == ["echo", "hello"]


# ============================================================================
# Test 5: Summary Report Format
# ============================================================================

def test_summary_report_format():
    """Build a mock results dict, call format_summary, verify expected sections."""
    results = {
        "base_layer": {"status": "ok", "platforms": ["claude-code", "opencode"]},
        "intelligence": {
            "cgc": {"status": "ok", "platforms": 2},
            "codesight": {"status": "ok"},
            "repomix": {"status": "skip", "reason": "repomix output already exists: repomix-output.txt"},
        },
        "compression": {
            "rtk": {"status": "ok", "version": "1.2.3"},
        },
        "node_only_fallback": False,
    }

    out = format_summary(results)

    # Header
    assert "Token Saver Meta" in out
    assert "Installation Summary" in out

    # Section labels
    assert "Base Layer" in out
    assert "Intelligence" in out
    assert "Compression" in out

    # Active tool count
    assert "tools active" in out
    # Base layer (1 ok) + cgc (1 ok) + codesight (1 ok) + repomix (1 skip) + rtk (1 ok) = 4 active out of 5
    assert "4/5" in out

    # Status icons
    assert "✅" in out  # ok tools
    assert "⚠️" in out  # skip/warn tools

    # Specific tool labels
    assert "cgc" in out.lower() or "CGC" in out
    assert "repomix" in out.lower() or "Repomix" in out
    assert "rtk" in out.lower() or "RTK" in out
