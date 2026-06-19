"""Tests for oneshot_installer.py."""

from unittest.mock import patch

import pytest

from src.oneshot_installer import install_one_shot_tools


def test_codesight_idempotent(tmp_path):
    """CODESIGHT.md already exists -> status=skip with message."""
    (tmp_path / "CODESIGHT.md").write_text("existing")
    with patch("shutil.which", return_value="/usr/bin/npx"):
        result = install_one_shot_tools(tmp_path)
    assert result["codesight"]["status"] == "skip"
    assert "already exists" in result["codesight"]["message"]


def test_repomix_idempotent(tmp_path):
    """repomix-output.txt already exists -> status=skip with message."""
    (tmp_path / "repomix-output.txt").write_text("existing")
    with patch("shutil.which", return_value="/usr/bin/npx"):
        result = install_one_shot_tools(tmp_path)
    assert result["repomix"]["status"] == "skip"
    assert "already exists" in result["repomix"]["message"]


def test_npx_unavailable(tmp_path):
    """npx not found -> status=warn for both tools with message."""
    with patch("shutil.which", return_value=None):
        result = install_one_shot_tools(tmp_path)
    assert result["codesight"]["status"] == "warn"
    assert "npx not found" in result["codesight"]["message"]
    assert result["repomix"]["status"] == "warn"
    assert "npx not found" in result["repomix"]["message"]


def test_gitignore_updated(tmp_path):
    """Verify CODESIGHT.md and repomix-output.* added to .gitignore."""
    (tmp_path / ".gitignore").write_text("existing_entry\n")
    (tmp_path / "CODESIGHT.md").write_text("")          # triggers idempotent skip
    (tmp_path / "repomix-output.txt").write_text("")    # triggers idempotent skip
    with patch("shutil.which", return_value="/usr/bin/npx"):
        result = install_one_shot_tools(tmp_path)
    content = (tmp_path / ".gitignore").read_text()
    assert "CODESIGHT.md" in content
    assert "repomix-output.*" in content
    assert result["gitignore_updated"] is True
