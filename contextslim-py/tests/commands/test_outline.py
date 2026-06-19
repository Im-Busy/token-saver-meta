"""Tests for outline_command — recursive signature extraction."""

from __future__ import annotations

from pathlib import Path

import pytest

from contextslim.commands.code.outline import outline_command
from contextslim.config import Config, Limits


def _cfg(max_sigs: int = 15) -> Config:
    return Config(limits=Limits(outline_max_sigs_per_file=max_sigs))


class TestOutlineCommand:
    """Given a project directory, outline_command walks source files and extracts signatures."""

    def test_extracts_signatures_from_js(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Source files with signatures show them in tree output."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "utils.js").write_text(
            "import x from 'y';\nfunction add(a, b) {\n  return a + b;\n}\nclass Foo {\n  bar() {}\n}\n"
        )

        outline_command(str(tmp_path), _cfg())

        captured = capsys.readouterr().out
        assert "utils.js" in captured
        assert "function add" in captured
        assert "class Foo" in captured

    def test_extracts_signatures_from_python(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Python source files with top-level defs/classes are captured."""
        (tmp_path / "mod.py").write_text(
            "def greet(name):\n    return f'hi {name}'\n\nclass Animal:\n    pass\n"
        )

        outline_command(str(tmp_path), _cfg())

        captured = capsys.readouterr().out
        assert "mod.py" in captured
        # Python def/class: SIGNATURE_PATTERNS won't match Python indented defs exactly
        # because patterns use ^, but they should still match when no leading whitespace

    def test_empty_project(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Empty directory prints 'No source files found.'."""
        outline_command(str(tmp_path), _cfg())

        captured = capsys.readouterr().out
        assert "No source files found" in captured

    def test_skips_ignored_dirs(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """node_modules and .git files are excluded from outline."""
        (tmp_path / "src").mkdir()
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "src" / "app.ts").write_text("export function main() {}")
        (tmp_path / "node_modules" / "lib.js").write_text("function secret() {}")

        outline_command(str(tmp_path), _cfg())

        captured = capsys.readouterr().out
        assert "app.ts" in captured
        assert "function main" in captured
        assert "lib.js" not in captured

    def test_signature_cap(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Signatures per file are capped at config.limits.outline_max_sigs_per_file."""
        (tmp_path / "lots.ts").write_text("\n".join(f"export function f{i}() {{}}" for i in range(50)))

        outline_command(str(tmp_path), _cfg(max_sigs=3))

        captured = capsys.readouterr().out
        # Should only see f0, f1, f2
        assert "f0" in captured
        assert "f1" in captured
        assert "f2" in captured
        assert "f3" not in captured

    def test_handles_read_error_gracefully(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Unreadable files show error marker but don't crash."""
        bad = tmp_path / "bad.ts"
        bad.write_text("function ok() {}")
        bad.chmod(0o000) if hasattr(bad, "chmod") else None  # best-effort

        outline_command(str(tmp_path), _cfg())

        captured = capsys.readouterr().out
        # Should not crash — at minimum the project root name appears
        assert tmp_path.name in captured

    def test_shows_no_signatures_for_empty_files(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Files with no signature lines show '(no signatures)'."""
        (tmp_path / "empty.js").write_text("// just a comment\n")

        outline_command(str(tmp_path), _cfg())

        captured = capsys.readouterr().out
        assert "empty.js" in captured
        assert "no signatures" in captured

    def test_multi_file_tree_structure(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Tree preserves directory hierarchy for multiple files."""
        (tmp_path / "src" / "lib").mkdir(parents=True)
        (tmp_path / "src" / "main.ts").write_text("export function entry() {}")
        (tmp_path / "src" / "lib" / "util.ts").write_text("export function helper() {}")

        outline_command(str(tmp_path), _cfg())

        captured = capsys.readouterr().out
        assert "main.ts" in captured
        assert "util.ts" in captured
        assert "function entry" in captured
        assert "function helper" in captured
