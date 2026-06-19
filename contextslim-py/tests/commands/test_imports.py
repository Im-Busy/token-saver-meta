"""Tests for imports_command — extract-only imports from a file."""

from __future__ import annotations

from pathlib import Path

import pytest

from contextslim.commands.code.imports_cmd import imports_command


class TestImportsCommand:
    """Given a source file, imports_command extracts only import/require lines."""

    def test_extracts_es6_imports(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """ES6 import statements are extracted and displayed."""
        f = tmp_path / "app.ts"
        f.write_text(
            "import React from 'react';\n"
            "import { useState } from 'react';\n"
            "import * as lib from './lib';\n"
            "\n"
            "function App() {\n"
            "  return <div>hi</div>;\n"
            "}\n"
        )

        imports_command(str(f))

        captured = capsys.readouterr().out
        assert "import React from" in captured
        assert "import { useState }" in captured
        assert "import * as lib" in captured

    def test_extracts_require_statements(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """CJS require() calls are extracted."""
        f = tmp_path / "server.js"
        f.write_text(
            "const fs = require('fs');\n"
            "const path = require('path');\n"
            "\n"
            "fs.readFileSync('data.txt');\n"
        )

        imports_command(str(f))

        captured = capsys.readouterr().out
        assert "const fs = require" in captured
        assert "const path = require" in captured

    def test_reports_savings(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Output includes savings percentage line."""
        f = tmp_path / "mod.ts"
        f.write_text(
            "import a from 'a';\n\n\n\n\nfunction big() {\n  return 1;\n}\n"
        )

        imports_command(str(f))

        captured = capsys.readouterr().out
        assert "% saved" in captured

    def test_no_imports_found(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """When no imports exist, message is shown."""
        f = tmp_path / "plain.txt"
        f.write_text("hello world")

        imports_command(str(f))

        captured = capsys.readouterr().out
        assert "No imports found" in captured

    def test_handles_nonexistent_file(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Missing file reports error without crashing."""
        imports_command(str(tmp_path / "nope.ts"))

        captured = capsys.readouterr().out
        assert "Cannot read" in captured

    def test_omits_non_import_lines(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Function bodies, comments, blank lines are excluded."""
        f = tmp_path / "file.ts"
        f.write_text(
            "import x from 'x';\n"
            "// comment\n"
            "const y = 1;\n"
            "function f() {\n"
            "  return x(y);\n"
            "}\n"
        )

        imports_command(str(f))

        captured = capsys.readouterr().out
        assert "import x from" in captured
        assert "function f()" not in captured
        assert "return" not in captured
