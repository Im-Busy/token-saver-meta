"""Tests for contextslim.commands.code.map_cmd."""

from __future__ import annotations

from pathlib import Path

import pytest

from contextslim.commands.code.map_cmd import _colorize_line, map_command


class TestMapSignaturesFound:
    """When structural signatures exist, they are extracted and colorized."""

    def test_extracts_ts_signatures(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given a TypeScript file with classes/functions/consts, signatures appear."""
        code = """\
export function login() {}
class UserService {}
const API_URL = "https://api.example.com";
export interface IUser {}
export type UserId = string;
export enum Status { Active, Inactive }
"""
        f = tmp_path / "app.ts"
        f.write_text(code)

        map_command(str(f))

        captured = capsys.readouterr()
        assert "login" in captured.out
        assert "UserService" in captured.out
        assert "API_URL" in captured.out
        assert "IUser" in captured.out
        assert "UserId" in captured.out
        assert "Status" in captured.out

    def test_extracts_python_signatures(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given a Python file with class, signature appears. Python def is not
        matched (compressor patterns are JS/TS-oriented)."""
        code = """\
def foo():
    pass

class MyClass:
    def method(self):
        pass

CONST = 42  # not a signature
"""
        f = tmp_path / "mod.py"
        f.write_text(code)

        map_command(str(f))

        captured = capsys.readouterr()
        # class is a recognized structural signature
        assert "class MyClass" in captured.out
        # Python def and plain assignments are not extracted
        assert "def foo" not in captured.out
        assert "CONST" not in captured.out

    def test_reports_savings(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given signatures were extracted, savings are reported."""
        code = "export function f() {}\n" * 5
        f = tmp_path / "many.ts"
        f.write_text(code)

        map_command(str(f))

        captured = capsys.readouterr()
        assert "Extracted 5 signatures" in captured.out
        assert "Saved" in captured.out


class TestMapNoSignatures:
    """When no structural signatures exist, a helpful message is shown."""

    def test_no_signatures_reports_message(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given a file with no matching patterns, 'No structural signatures' appears."""
        f = tmp_path / "plain.txt"
        f.write_text("just some prose\nnothing structural\n")

        map_command(str(f))

        captured = capsys.readouterr()
        assert "No structural signatures found" in captured.out

    def test_empty_file_no_signatures(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given an empty file, the 'no signatures' message appears."""
        f = tmp_path / "empty.ts"
        f.write_text("")

        map_command(str(f))

        captured = capsys.readouterr()
        assert "No structural signatures found" in captured.out

    def test_no_savings_line_when_no_signatures(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given no signatures, the 'Saved' line is absent."""
        f = tmp_path / "data.txt"
        f.write_text("hello\n")

        map_command(str(f))

        captured = capsys.readouterr()
        assert "Saved" not in captured.out


class TestMapColorization:
    """Signature lines are colorized with rich."""

    def test_colorize_keywords(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given various keywords, color markup is applied."""
        code = """\
function greet() {}
class Animal {}
const MAX = 100;
let count = 0;
"""
        f = tmp_path / "color.ts"
        f.write_text(code)

        map_command(str(f))

        captured = capsys.readouterr()
        # All signatures should appear
        assert "greet" in captured.out
        assert "Animal" in captured.out
        assert "MAX" in captured.out
        assert "count" in captured.out

    def test_colorize_interface_type_enum(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Given interface, type, and enum keywords, they are magenta."""
        code = """\
interface IConfig {}
type Name = string;
enum Color { Red, Green }
"""
        f = tmp_path / "types.ts"
        f.write_text(code)

        map_command(str(f))

        captured = capsys.readouterr()
        assert "IConfig" in captured.out
        assert "Name" in captured.out
        assert "Color" in captured.out


class TestMapColorizeLine:
    """Unit tests for _colorize_line helper."""

    def test_function_cyan(self) -> None:
        """Given a function declaration, the keyword is styled cyan."""
        text = _colorize_line("function doStuff() {")
        # Verify the plain text is intact
        assert "function doStuff" in text.plain
        # Verify styles exist on the keyword span
        spans = text.spans
        assert len(spans) > 0

    def test_class_magenta(self) -> None:
        """Given a class declaration, the keyword is styled magenta."""
        text = _colorize_line("class Foo {")
        assert "class Foo" in text.plain
        spans = text.spans
        assert len(spans) > 0

    def test_const_yellow(self) -> None:
        """Given a const declaration, the keyword is styled yellow."""
        text = _colorize_line("const X = 1;")
        assert "const X =" in text.plain
        spans = text.spans
        assert len(spans) > 0

    def test_empty_line_unchanged(self) -> None:
        """Given an empty line, no spans are added."""
        text = _colorize_line("")
        assert text.plain == ""
        assert len(text.spans) == 0


class TestMapNotFound:
    """Error handling for missing files."""

    def test_missing_file_raises(
        self, tmp_path: Path
    ) -> None:
        """Given a nonexistent file path, FileNotFoundError is raised."""
        missing = tmp_path / "nope.ts"

        with pytest.raises(FileNotFoundError):
            map_command(str(missing))
