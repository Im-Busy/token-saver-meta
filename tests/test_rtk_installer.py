"""Tests for src/rtk_installer.py — install_rtk and init_rtk_hook."""

from pathlib import Path
from unittest.mock import patch, MagicMock

from src.rtk_installer import install_rtk, init_rtk_hook


# ---- helpers ----

def _mock_run_side_effect(args, **__):
    """Simulate subprocess.run for different rtk commands."""
    cmd = " ".join(args)
    if "--version" in cmd:
        result = MagicMock()
        result.stdout = "rtk 1.2.3\n"
        result.stderr = ""
        result.returncode = 0
        return result
    if "init" in cmd and "-g" in cmd:
        result = MagicMock()
        result.stdout = "Hook injected\n"
        result.stderr = ""
        result.returncode = 0
        return result
    raise RuntimeError(f"Unexpected subprocess.run call: {cmd}")


# ---- tests ----

def test_rtk_already_installed():
    """Mock shutil.which + subprocess.run → pre-installed path with version and hook."""
    dummy_project = Path("/fake/project")

    with (
        patch("src.rtk_installer.shutil.which", lambda _: "/usr/local/bin/rtk"),
        patch("src.rtk_installer.subprocess.run", side_effect=_mock_run_side_effect),
    ):
        result = install_rtk(dummy_project)

    assert result["status"] == "ok"
    assert result["version"] == "1.2.3"
    assert result["install_method"] == "pre-installed"
    assert result["hook_status"] == "ok"
    assert result["message"] == ""


def test_rtk_not_installable():
    """All install paths (brew, curl, cargo) unavailable → skip with helpful message."""
    dummy_project = Path("/fake/project")

    def _which_nothing(_: str) -> str | None:
        return None  # No rtk, no brew, no cargo

    with (
        patch("src.rtk_installer.shutil.which", _which_nothing),
        patch("src.rtk_installer.platform.system", return_value="Windows"),
    ):
        result = install_rtk(dummy_project)

    assert result["status"] == "skip"
    assert result["version"] is None
    assert result["install_method"] is None
    assert result["hook_status"] == "skip"
    assert "github.com/rtk-ai/rtk/releases" in result["message"].lower()
    assert "rustup.rs" in result["message"]


def test_rtk_install_returns_structured():
    """Verify output dict has all five required keys regardless of path."""
    dummy_project = Path("/fake/project")

    with (
        patch("src.rtk_installer.shutil.which", lambda _: "/usr/local/bin/rtk"),
        patch("src.rtk_installer.subprocess.run", side_effect=_mock_run_side_effect),
    ):
        result = install_rtk(dummy_project)

    required_keys = {"status", "version", "install_method", "hook_status", "message"}
    assert required_keys == set(result.keys())
    assert result["status"] in ("ok", "warn", "skip", "error")
    assert result["hook_status"] in ("ok", "skip", "warn")
    assert isinstance(result["message"], str)
