"""Tests for contextslim.commands.setup.init_cmd."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from contextslim.commands.setup.init_cmd import _canonical_stack_name, init_command


class TestCanonicalStackName:
    def test_nodejs(self) -> None:
        assert _canonical_stack_name("Node.js") == "node"

    def test_python(self) -> None:
        assert _canonical_stack_name("Python") == "python"

    def test_rust(self) -> None:
        assert _canonical_stack_name("Rust") == "rust"

    def test_go(self) -> None:
        assert _canonical_stack_name("Go") == "go"

    def test_unknown_falls_back_to_lower(self) -> None:
        assert _canonical_stack_name("CUSTOM") == "custom"


class TestInitCommand:
    def test_initializes_python_project(self, tmp_path: Path) -> None:
        """Given: Python project. When: init with cursor IDE. Then: creates config + ignore + rules."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")
        (tmp_path / "requirements.txt").write_text("fastapi\n")

        init_command(str(tmp_path), ["cursor"], force=False)

        assert (tmp_path / ".contextslim.toml").exists()
        assert (tmp_path / ".gitignore").exists()
        assert (tmp_path / ".cursorrules").exists()

    def test_initializes_nodejs_project(self, tmp_path: Path) -> None:
        """Given: Node.js project with package.json. When: init with claude. Then: creates CLAUDE.md."""
        (tmp_path / "package.json").write_text(json.dumps({"name": "test-app"}))

        init_command(str(tmp_path), ["claude"], force=False)

        assert (tmp_path / ".contextslim.toml").exists()
        assert (tmp_path / "CLAUDE.md").exists()

    def test_initializes_with_multiple_ides(self, tmp_path: Path) -> None:
        """Given: project. When: init with cursor+claude+copilot. Then: all IDE files created."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")

        init_command(str(tmp_path), ["cursor", "claude", "copilot"], force=False)

        assert (tmp_path / ".cursorrules").exists()
        assert (tmp_path / "CLAUDE.md").exists()
        assert (tmp_path / ".github" / "copilot-instructions.md").exists()

    def test_force_overwrites_config(self, tmp_path: Path) -> None:
        """Given: existing .contextslim.toml. When: init with force=True. Then: overwrites."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")
        config = tmp_path / ".contextslim.toml"
        config.write_text("# Old config\n", encoding="utf-8")

        init_command(str(tmp_path), ["cursor"], force=True)

        content = config.read_text()
        assert "ContextSlim configuration" in content
        assert "Old config" not in content

    def test_skips_config_when_exists_without_force(self, tmp_path: Path) -> None:
        """Given: existing .contextslim.toml. When: init without force. Then: config preserved."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")
        config = tmp_path / ".contextslim.toml"
        config.write_text("# My custom config\n", encoding="utf-8")

        init_command(str(tmp_path), ["cursor"], force=False)

        content = config.read_text()
        assert "# My custom config" in content
        assert "ContextSlim configuration" not in content

    def test_handles_unknown_ides(self, tmp_path: Path) -> None:
        """Given: unknown IDE in list. When: init. Then: filtered quietly, valid ones processed."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")

        init_command(str(tmp_path), ["cursor", "gemini", "chatgpt"], force=False)

        # cursor should still be created
        assert (tmp_path / ".cursorrules").exists()

    def test_handles_empty_ides_list(self, tmp_path: Path) -> None:
        """Given: empty IDE list. When: init. Then: reports error, no crash."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")
        init_command(str(tmp_path), [], force=False)

    def test_handles_no_stack_detected(self, tmp_path: Path) -> None:
        """Given: empty directory. When: init. Then: works with generic defaults."""
        (tmp_path / "README.md").write_text("# Test\n")
        init_command(str(tmp_path), ["cursor"], force=False)

        assert (tmp_path / ".contextslim.toml").exists()
        assert (tmp_path / ".gitignore").exists()
        assert (tmp_path / ".cursorrules").exists()

    def test_handles_missing_directory(self, tmp_path: Path) -> None:
        """Given: non-existent directory. When: init. Then: prints error, no crash."""
        init_command(str(tmp_path / "nope"), ["cursor"], force=False)

    def test_idempotent_ignore_merging(self, tmp_path: Path) -> None:
        """Given: second init. When: same stack. Then: no duplicate patterns."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")

        init_command(str(tmp_path), ["cursor"], force=False)
        first_content = (tmp_path / ".gitignore").read_text()

        init_command(str(tmp_path), ["cursor"], force=False)
        second_content = (tmp_path / ".gitignore").read_text()

        assert first_content == second_content

    def test_writes_windsurf_rules(self, tmp_path: Path) -> None:
        """Given: project. When: init with windsurf. Then: .windsurfrules created."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")
        init_command(str(tmp_path), ["windsurf"], force=False)
        assert (tmp_path / ".windsurfrules").exists()
