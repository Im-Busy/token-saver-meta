"""Tests for the 7-phase installer pipeline — per-tool isolation, idempotency, fallbacks."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.installer import main, run_phase


# ---------------------------------------------------------------------------
# run_phase unit tests
# ---------------------------------------------------------------------------

def test_run_phase_ok():
    """run_phase captures successful result."""
    result = run_phase("test", lambda: 42)
    assert result == {"test": {"status": "ok", "result": 42}}


def test_run_phase_error_isolation():
    """run_phase catches ALL exceptions — never crashes."""
    result = run_phase("test", lambda: 1 / 0)
    assert result["test"]["status"] == "error"
    assert "division by zero" in result["test"]["result"]


def test_run_phase_with_args():
    """run_phase passes args and kwargs through."""
    result = run_phase("test", lambda a, b=0: a + b, 3, b=7)
    assert result == {"test": {"status": "ok", "result": 10}}


# ---------------------------------------------------------------------------
# Platform detection in pipeline
# ---------------------------------------------------------------------------

@patch("src.config_gen.detect_platforms")
@patch("src.agents_injector.inject_agents_md_section")
@patch("src.prerequisites.check_prerequisites")
@patch("src.cgc_installer.install_cgc")
@patch("src.oneshot_installer.install_one_shot_tools")
@patch("src.rtk_installer.install_rtk")
def test_detect_platforms(
    mock_rtk: MagicMock,
    mock_oneshot: MagicMock,
    mock_cgc: MagicMock,
    mock_pre: MagicMock,
    mock_inject: MagicMock,
    mock_detect: MagicMock,
    tmp_path: Path,
):
    """Pipeline detects known platforms from project markers."""
    mock_detect.return_value = ["kilo", "claude-code"]
    mock_inject.return_value = {
        "kilo": {"status": "appended"},
        "claude-code": {"status": "appended"},
    }
    mock_pre.return_value = {
        "node": {"status": "ok", "version": "v22.0.0", "path": "/usr/bin/node"},
        "npm": {"status": "ok", "version": "10.0.0", "path": "/usr/bin/npm"},
        "npx": {"status": "ok"},
        "python": {"status": "ok", "version": "3.12", "path": "/usr/bin/python"},
        "uv": {"status": "ok", "version": "uv 0.6.0", "path": "/usr/bin/uv"},
        "internet": {"status": "ok"},
        "disk_free_mb": 5000.0,
        "can_write": True,
        "all_ok": True,
        "node_only_fallback": False,
        "issues": [],
    }
    mock_cgc.return_value = {"status": "ok", "platforms": {"kilo": {"status": "ok"}}, "message": "ok"}
    mock_oneshot.return_value = {
        "codesight": {"status": "skip", "message": "already exists"},
        "repomix": {"status": "skip", "message": "already exists"},
        "gitignore_updated": False,
    }
    mock_rtk.return_value = {
        "status": "ok",
        "version": "1.0.0",
        "install_method": "pre-installed",
        "hook_status": "ok",
        "message": "",
    }

    results = main(tmp_path)

    assert results["platforms"]["status"] == "ok"
    assert results["platforms"]["detected"] == ["kilo", "claude-code"]
    mock_detect.assert_called_once()


# ---------------------------------------------------------------------------
# Node-only fallback
# ---------------------------------------------------------------------------

@patch("src.config_gen.detect_platforms")
@patch("src.agents_injector.inject_agents_md_section")
@patch("src.prerequisites.check_prerequisites")
@patch("src.oneshot_installer.install_one_shot_tools")
@patch("src.rtk_installer.install_rtk")
def test_node_only_fallback(
    mock_rtk: MagicMock,
    mock_oneshot: MagicMock,
    mock_pre: MagicMock,
    mock_inject: MagicMock,
    mock_detect: MagicMock,
    tmp_path: Path,
):
    """When Python/uv are missing, pipeline records node_only_fallback."""
    mock_detect.return_value = ["kilo"]
    mock_inject.return_value = {"kilo": {"status": "appended"}}
    mock_pre.return_value = {
        "node": {"status": "ok", "version": "v22.0.0", "path": "/usr/bin/node"},
        "npm": {"status": "ok", "version": "10.0.0", "path": "/usr/bin/npm"},
        "npx": {"status": "ok"},
        "python": {"status": "missing", "version": None, "path": None},
        "uv": {"status": "missing", "version": None, "path": None},
        "internet": {"status": "ok"},
        "disk_free_mb": 5000.0,
        "can_write": True,
        "all_ok": True,
        "node_only_fallback": True,
        "issues": ["Python not found. Install from https://python.org"],
    }
    mock_oneshot.return_value = {
        "codesight": {"status": "skip", "message": "already exists"},
        "repomix": {"status": "skip", "message": "already exists"},
        "gitignore_updated": False,
    }
    mock_rtk.return_value = {
        "status": "skip",
        "version": None,
        "install_method": None,
        "hook_status": "skip",
        "message": "RTK not installable.",
    }

    results = main(tmp_path)

    assert results["node_only_fallback"] is True
    cgc_result = results.get("cgc", {})
    assert isinstance(cgc_result, dict)
    assert "status" in cgc_result


# ---------------------------------------------------------------------------
# Per-tool failure isolation
# ---------------------------------------------------------------------------

@patch("src.config_gen.detect_platforms")
@patch("src.agents_injector.inject_agents_md_section")
@patch("src.prerequisites.check_prerequisites")
@patch("src.cgc_installer.install_cgc")
@patch("src.oneshot_installer.install_one_shot_tools")
@patch("src.rtk_installer.install_rtk")
def test_per_tool_failure_isolation(
    mock_rtk: MagicMock,
    mock_oneshot: MagicMock,
    mock_cgc: MagicMock,
    mock_pre: MagicMock,
    mock_inject: MagicMock,
    mock_detect: MagicMock,
    tmp_path: Path,
):
    """CGC fails — but codesight, repomix, and RTK still install."""
    mock_detect.return_value = ["kilo"]
    mock_inject.return_value = {"kilo": {"status": "appended"}}
    mock_pre.return_value = {
        "node": {"status": "ok", "version": "v22.0.0", "path": "/usr/bin/node"},
        "npm": {"status": "ok", "version": "10.0.0", "path": "/usr/bin/npm"},
        "npx": {"status": "ok"},
        "python": {"status": "ok", "version": "3.12", "path": "/usr/bin/python"},
        "uv": {"status": "ok", "version": "uv 0.6.0", "path": "/usr/bin/uv"},
        "internet": {"status": "ok"},
        "disk_free_mb": 5000.0,
        "can_write": True,
        "all_ok": True,
        "node_only_fallback": False,
        "issues": [],
    }
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

    cgc = results.get("cgc", {})
    assert cgc.get("status") == "error"
    assert "CGC install failed" in cgc.get("result", "")

    mock_oneshot.assert_called_once()
    mock_rtk.assert_called_once()


# ---------------------------------------------------------------------------
# Idempotent second run
# ---------------------------------------------------------------------------

@patch("src.config_gen.detect_platforms")
@patch("src.agents_injector.inject_agents_md_section")
@patch("src.prerequisites.check_prerequisites")
@patch("src.cgc_installer.install_cgc")
@patch("src.oneshot_installer.install_one_shot_tools")
@patch("src.rtk_installer.install_rtk")
def test_idempotent_second_run(
    mock_rtk: MagicMock,
    mock_oneshot: MagicMock,
    mock_cgc: MagicMock,
    mock_pre: MagicMock,
    mock_inject: MagicMock,
    mock_detect: MagicMock,
    tmp_path: Path,
):
    """Running twice produces same result — tools report skip/unchanged on second run."""
    mock_detect.return_value = ["kilo"]
    mock_inject.return_value = {
        "kilo": {"status": "unchanged"},
    }
    mock_pre.return_value = {
        "node": {"status": "ok", "version": "v22.0.0", "path": "/usr/bin/node"},
        "npm": {"status": "ok", "version": "10.0.0", "path": "/usr/bin/npm"},
        "npx": {"status": "ok"},
        "python": {"status": "ok", "version": "3.12", "path": "/usr/bin/python"},
        "uv": {"status": "ok", "version": "uv 0.6.0", "path": "/usr/bin/uv"},
        "internet": {"status": "ok"},
        "disk_free_mb": 5000.0,
        "can_write": True,
        "all_ok": True,
        "node_only_fallback": False,
        "issues": [],
    }
    mock_cgc.return_value = {"status": "skip", "platforms": {}, "message": "All servers already configured"}
    mock_oneshot.return_value = {
        "codesight": {"status": "skip", "message": "CODESIGHT.md already exists"},
        "repomix": {"status": "skip", "message": "repomix output already exists: repomix-output.txt"},
        "gitignore_updated": False,
    }
    mock_rtk.return_value = {
        "status": "ok",
        "version": "1.0.0",
        "install_method": "pre-installed",
        "hook_status": "ok",
        "message": "",
    }

    results1 = main(tmp_path)
    results2 = main(tmp_path)

    assert results1.keys() == results2.keys()
    assert "base_layer" in results1
    assert "platforms" in results1

    assert mock_inject.call_count == 2
    assert mock_oneshot.call_count == 2
    assert mock_rtk.call_count == 2
