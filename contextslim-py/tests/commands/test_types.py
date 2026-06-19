"""Tests for types_command — extract-only TS type declarations."""

from __future__ import annotations

from pathlib import Path

import pytest

from contextslim.commands.code.types_cmd import types_command


class TestTypesCommand:
    """Given a source file, types_command extracts only interface/type/enum lines."""

    def test_extracts_interface_type_enum(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """TS type declarations are extracted."""
        f = tmp_path / "types.ts"
        f.write_text(
            "interface User {\n  id: number;\n}\n"
            "type ID = string;\n"
            "enum Color { Red, Green }\n"
            "export interface Org {\n  slug: string;\n}\n"
        )

        types_command(str(f))

        captured = capsys.readouterr().out
        assert "interface User" in captured
        assert "type ID" in captured
        assert "enum Color" in captured
        assert "export interface Org" in captured

    def test_omits_functions_and_classes(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Functions, classes, and const assignments are excluded from types output."""
        f = tmp_path / "mixed.ts"
        f.write_text(
            "function f() {}\n"
            "class C {}\n"
            "const x = 1;\n"
            "interface I {}\n"
            "type T = string;\n"
        )

        types_command(str(f))

        captured = capsys.readouterr().out
        assert "interface I" in captured
        assert "type T" in captured
        assert "function f" not in captured
        assert "class C" not in captured
        assert "const x" not in captured

    def test_no_types_found(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """When no type declarations exist, 'No types found.' is printed."""
        f = tmp_path / "plain.js"
        f.write_text("console.log(1);\nfunction add() {}\n")

        types_command(str(f))

        captured = capsys.readouterr().out
        assert "No types found" in captured

    def test_reports_savings(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Output includes savings percentage."""
        f = tmp_path / "data.ts"
        f.write_text(
            "type ID = string;\n"
            "function big() {\n  // lots of code\n  return 1;\n}\n"
        )

        types_command(str(f))

        captured = capsys.readouterr().out
        assert "% saved" in captured

    def test_handles_nonexistent_file(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Missing file reports error without crashing."""
        types_command(str(tmp_path / "ghost.ts"))

        captured = capsys.readouterr().out
        assert "Cannot read" in captured

    def test_handles_export_types(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """export type/interface/enum declarations are extracted."""
        f = tmp_path / "exports.ts"
        f.write_text(
            "export type Status = 'ok' | 'err';\n"
            "export interface Config { debug: boolean; }\n"
            "export enum Level { Low, High }\n"
        )

        types_command(str(f))

        captured = capsys.readouterr().out
        assert "export type Status" in captured
        assert "export interface Config" in captured
        assert "export enum Level" in captured
