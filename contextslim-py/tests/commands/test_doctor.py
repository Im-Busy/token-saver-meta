"""Tests for contextslim.commands.setup.doctor."""

from __future__ import annotations

from pathlib import Path

import pytest

from contextslim.commands.setup.doctor import (
    _check_config,
    _check_config_valid,
    _check_git,
    _check_ide_rules,
    _check_ignore,
    _check_stack,
    Check,
    doctor_command,
)


class TestCheckConfig:
    def test_found(self, tmp_path: Path) -> None:
        """Given: .contextslim.toml exists. When: _check_config. Then: PASS."""
        (tmp_path / ".contextslim.toml").write_text("# config", encoding="utf-8")
        check = _check_config(tmp_path)
        assert check.status == "PASS"

    def test_not_found(self, tmp_path: Path) -> None:
        """Given: no config. When: _check_config. Then: FAIL."""
        check = _check_config(tmp_path)
        assert check.status == "FAIL"
        assert "not found" in check.detail.lower()


class TestCheckStack:
    def test_detects_python_stack(self, tmp_path: Path) -> None:
        """Given: Python project. When: _check_stack. Then: PASS with detection."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")
        check = _check_stack(tmp_path)
        assert check.status == "PASS"
        assert "Python" in check.detail

    def test_no_stack_warns(self, tmp_path: Path) -> None:
        """Given: empty directory. When: _check_stack. Then: WARN."""
        check = _check_stack(tmp_path)
        assert check.status == "WARN"


class TestCheckIgnore:
    def test_found_with_contextslim_patterns(self, tmp_path: Path) -> None:
        """Given: .gitignore with ContextSlim patterns. When: _check_ignore. Then: PASS."""
        (tmp_path / ".gitignore").write_text(
            "# ContextSlim patterns\nnode_modules/\n__pycache__/\n.git/\n",
            encoding="utf-8",
        )
        check = _check_ignore(tmp_path)
        assert check.status == "PASS"

    def test_found_without_contextslim(self, tmp_path: Path) -> None:
        """Given: .gitignore without ContextSlim. When: _check_ignore. Then: WARN."""
        (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")
        check = _check_ignore(tmp_path)
        assert check.status == "WARN"

    def test_not_found(self, tmp_path: Path) -> None:
        """Given: no .gitignore. When: _check_ignore. Then: FAIL."""
        check = _check_ignore(tmp_path)
        assert check.status == "FAIL"


class TestCheckIdeRules:
    def test_found_cursor_rules(self, tmp_path: Path) -> None:
        """Given: .cursorrules exists. When: _check_ide_rules. Then: PASS."""
        (tmp_path / ".cursorrules").write_text("# rules", encoding="utf-8")
        check = _check_ide_rules(tmp_path)
        assert check.status == "PASS"
        assert "cursor" in check.detail

    def test_found_multiple_ides(self, tmp_path: Path) -> None:
        """Given: multiple IDE files. When: _check_ide_rules. Then: all listed."""
        (tmp_path / ".cursorrules").write_text("# cursor")
        (tmp_path / "CLAUDE.md").write_text("# claude")
        check = _check_ide_rules(tmp_path)
        assert "cursor" in check.detail
        assert "claude" in check.detail

    def test_none_found(self, tmp_path: Path) -> None:
        """Given: no IDE files. When: _check_ide_rules. Then: WARN."""
        check = _check_ide_rules(tmp_path)
        assert check.status == "WARN"

    def test_copilot_nested_path(self, tmp_path: Path) -> None:
        """Given: .github/copilot-instructions.md exists. When: _check_ide_rules. Then: copilot detected."""
        github = tmp_path / ".github"
        github.mkdir()
        (github / "copilot-instructions.md").write_text("# copilot")
        check = _check_ide_rules(tmp_path)
        assert check.status == "PASS"
        assert "copilot" in check.detail


class TestCheckGit:
    def test_detects_git_dir(self, tmp_path: Path) -> None:
        """Given: .git directory. When: _check_git. Then: PASS."""
        (tmp_path / ".git").mkdir()
        check = _check_git(tmp_path)
        assert check.status == "PASS"

    def test_no_git_warns(self, tmp_path: Path) -> None:
        """Given: non-git directory. When: _check_git. Then: WARN."""
        check = _check_git(tmp_path)
        assert check.status == "WARN"


class TestCheckConfigValid:
    def test_valid_config(self, tmp_path: Path) -> None:
        """Given: valid .contextslim.toml. When: _check_config_valid. Then: PASS."""
        (tmp_path / ".contextslim.toml").write_text(
            "[limits]\ncat_lines = 42\n", encoding="utf-8"
        )
        check = _check_config_valid(tmp_path)
        assert check.status == "PASS"

    def test_missing_config(self, tmp_path: Path) -> None:
        """Given: no config. When: _check_config_valid. Then: WARN."""
        check = _check_config_valid(tmp_path)
        assert check.status == "WARN"

    def test_invalid_toml(self, tmp_path: Path) -> None:
        """Given: malformed TOML. When: _check_config_valid. Then: FAIL."""
        (tmp_path / ".contextslim.toml").write_text(
            "[limits\ncat_lines = abc\n", encoding="utf-8"
        )
        check = _check_config_valid(tmp_path)
        assert check.status == "FAIL"


class TestDoctorCommand:
    def test_runs_on_project(self, tmp_path: Path) -> None:
        """Given: typical project. When: doctor_command. Then: executes without error."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")
        (tmp_path / ".git").mkdir()
        doctor_command(str(tmp_path))

    def test_runs_on_already_configured_project(self, tmp_path: Path) -> None:
        """Given: fully configured project. When: doctor_command. Then: all PASS."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")
        (tmp_path / ".git").mkdir()
        (tmp_path / ".contextslim.toml").write_text(
            "[limits]\ncat_lines = 42\n", encoding="utf-8"
        )
        (tmp_path / ".gitignore").write_text(
            "# ContextSlim patterns\nnode_modules/\n", encoding="utf-8"
        )
        (tmp_path / ".cursorrules").write_text("# rules")
        doctor_command(str(tmp_path))

    def test_runs_on_empty_directory(self, tmp_path: Path) -> None:
        """Given: empty directory. When: doctor_command. Then: reports issues but no crash."""
        doctor_command(str(tmp_path))

    def test_handles_missing_directory(self, tmp_path: Path) -> None:
        """Given: non-existent directory. When: doctor_command. Then: prints error, no crash."""
        doctor_command(str(tmp_path / "nope"))
