"""Tests for brief_command — project-level context summary."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from contextslim.commands.code.brief import brief_command


class TestBriefCommand:
    """Given a project directory, brief_command outputs a compact summary."""

    def test_detects_nodejs_stack(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """When Node.js project exists, brief shows stack name and TypeScript status."""
        (tmp_path / "package.json").write_text('{"dependencies":{"react":"^18"}}')
        (tmp_path / "tsconfig.json").write_text("{}")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "index.ts").write_text("export {}")

        brief_command(str(tmp_path))

        captured = capsys.readouterr().out
        assert "Node.js" in captured
        assert "TypeScript" in captured
        assert "React" in captured

    def test_detects_python_stack(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """When Python project exists, brief shows Python stack."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\ndependencies=['fastapi']")
        (tmp_path / "main.py").write_text("print('hi')")

        brief_command(str(tmp_path))

        captured = capsys.readouterr().out
        assert "Python" in captured
        assert "main.py" in captured

    def test_detects_rust_stack(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """When Rust project exists, brief shows Rust stack and src/main.rs."""
        (tmp_path / "Cargo.toml").write_text("[package]\nname='test'")
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.rs").write_text("fn main() {}")

        brief_command(str(tmp_path))

        captured = capsys.readouterr().out
        assert "Rust" in captured
        assert "src/main.rs" in captured

    def test_detects_go_stack(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """When Go project exists, brief shows Go stack and main.go entry."""
        (tmp_path / "go.mod").write_text("module test")
        (tmp_path / "main.go").write_text("package main")

        brief_command(str(tmp_path))

        captured = capsys.readouterr().out
        assert "Go" in captured
        assert "main.go" in captured

    def test_no_stack_detected(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """When no known project files exist, brief reports no stack."""
        (tmp_path / "README.md").write_text("# Hello")

        brief_command(str(tmp_path))

        captured = capsys.readouterr().out
        assert "No project stack detected" in captured

    def test_reports_token_estimate(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Output includes a token estimate line."""
        (tmp_path / "package.json").write_text("{}")
        (tmp_path / "index.js").write_text("console.log(1)")

        brief_command(str(tmp_path))

        captured = capsys.readouterr().out
        assert re.search(r"~\d+\s+tokens", captured) is not None

    def test_shows_frameworks(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Detected frameworks appear in output."""
        (tmp_path / "package.json").write_text('{"dependencies":{"react":"^18","express":"^4"}}')
        (tmp_path / "index.js").write_text("// entry")

        brief_command(str(tmp_path))

        captured = capsys.readouterr().out
        assert "React" in captured
        assert "Express" in captured

    def test_shows_mini_tree(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Output includes a directory tree."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "app.py").write_text("# app")

        brief_command(str(tmp_path))

        captured = capsys.readouterr().out
        assert "src" in captured
        assert "app.py" in captured
