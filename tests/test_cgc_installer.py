"""Tests for src/cgc_installer.py — install_cgc with per-platform isolation."""
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.cgc_installer import install_cgc


def _mock_npx_run(args, **__):
    """Simulate subprocess.run for npx -y codegraph --version."""
    result = MagicMock()
    result.returncode = 0
    result.stdout = "1.0.0\n"
    result.stderr = ""
    return result


def test_cgc_config_generated():
    """npx available + CGC reachable → config written → status='ok'."""
    dummy = Path("/fake/project")

    with (
        patch("src.cgc_installer.shutil.which", return_value="/usr/local/bin/npx"),
        patch("src.cgc_installer.subprocess.run", side_effect=_mock_npx_run),
        patch(
            "src.cgc_installer.config_gen.write_mcp_config",
            return_value=("created", "Created config"),
        ),
    ):
        result = install_cgc(dummy, ["claude-code"])

    assert result["status"] == "ok"
    assert "claude-code" in result["platforms"]
    assert result["platforms"]["claude-code"]["status"] == "ok"
    assert "1/1" in result["message"]


def test_cgc_npx_unavailable():
    """subprocess.run raises FileNotFoundError → status='warn'."""
    dummy = Path("/fake/project")

    with (
        patch("src.cgc_installer.shutil.which", return_value="/usr/local/bin/npx"),
        patch(
            "src.cgc_installer.subprocess.run",
            side_effect=FileNotFoundError("npx not found"),
        ),
    ):
        result = install_cgc(dummy, ["claude-code"])

    assert result["status"] == "warn"
    assert result["platforms"] == {}
    assert "npx not found" in result["message"]


def test_cgc_idempotent():
    """All platforms already configured → write_mcp_config returns 'skipped' → status='skip'."""
    dummy = Path("/fake/project")

    with (
        patch("src.cgc_installer.shutil.which", return_value="/usr/local/bin/npx"),
        patch("src.cgc_installer.subprocess.run", side_effect=_mock_npx_run),
        patch(
            "src.cgc_installer.config_gen.write_mcp_config",
            return_value=("skipped", "All servers already configured"),
        ),
    ):
        result = install_cgc(dummy, ["claude-code"])

    assert result["status"] == "skip"
    assert result["platforms"]["claude-code"]["status"] == "skipped"
