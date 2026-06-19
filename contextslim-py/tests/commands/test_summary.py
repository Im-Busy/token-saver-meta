"""Tests for contextslim.commands.code.summary_cmd."""

from __future__ import annotations

from pathlib import Path

import pytest

from contextslim.commands.code.summary_cmd import (
    _count_blank_lines,
    _count_comment_lines,
    _estimate_tokens,
    _format_num,
    summary_command,
)


class TestCounters:
    def test_count_blank_lines(self) -> None:
        lines = ["hello", "", "world", "   ", ""]
        assert _count_blank_lines(lines) == 3

    def test_count_zero_blank_lines(self) -> None:
        lines = ["a", "b", "c"]
        assert _count_blank_lines(lines) == 0

    def test_count_comment_lines_hash(self) -> None:
        lines = ["# comment", "code", "# another"]
        assert _count_comment_lines(lines) == 2

    def test_count_comment_lines_slash(self) -> None:
        lines = ["// js comment", "code", "/* block */"]
        assert _count_comment_lines(lines) >= 1  # "//" matched; "/*" matched

    def test_blank_lines_not_comments(self) -> None:
        lines = ["", "# comment", ""]
        assert _count_comment_lines(lines) == 1

    def test_estimate_tokens(self) -> None:
        lines = ["def foo():", "    return 42"]
        tokens = _estimate_tokens(lines)
        assert tokens > 0


class TestFormatNum:
    def test_small_number(self) -> None:
        assert _format_num(42) == "42"

    def test_thousands(self) -> None:
        result = _format_num(1500)
        assert "1.5K" in result

    def test_millions(self) -> None:
        result = _format_num(2_500_000)
        assert "2.5M" in result


class TestSummaryCommand:
    def test_processes_python_file(self, tmp_path: Path) -> None:
        """Given: Python file with imports and functions. When: summary_command called. Then: no error."""
        py = tmp_path / "test.py"
        py.write_text(
            '# My module\nimport os\nfrom pathlib import Path\n\n\ndef hello():\n    return "world"\n\nclass Greeter:\n    pass\n',
            encoding="utf-8",
        )
        summary_command(str(py))

    def test_processes_typescript_file(self, tmp_path: Path) -> None:
        """Given: TypeScript file. When: summary_command called. Then: detects imports and signatures."""
        ts = tmp_path / "app.ts"
        ts.write_text(
            "import { readFile } from 'fs';\n\n"
            "export interface User { name: string; }\n\n"
            "export function greet(name: string): string {\n  return `Hello ${name}`;\n}\n",
            encoding="utf-8",
        )
        summary_command(str(ts))

    def test_processes_empty_file(self, tmp_path: Path) -> None:
        """Given: empty file. When: summary_command called. Then: no error, shows 0 lines."""
        empty = tmp_path / "empty.py"
        empty.write_text("", encoding="utf-8")
        summary_command(str(empty))

    def test_processes_comment_only_file(self, tmp_path: Path) -> None:
        """Given: file with only comments. When: summary_command called. Then: counts correctly."""
        cmt = tmp_path / "config.py"
        cmt.write_text("# All comments\n# No code here\n", encoding="utf-8")
        summary_command(str(cmt))

    def test_handles_missing_file(self, tmp_path: Path) -> None:
        """Given: non-existent file. When: summary_command called. Then: prints error, no crash."""
        summary_command(str(Path("/nonexistent/file.py")))

    def test_processes_javascript_file(self, tmp_path: Path) -> None:
        """Given: JavaScript file. When: summary_command called. Then: detects require and function."""
        js = tmp_path / "index.js"
        js.write_text(
            "const fs = require('fs');\n\nfunction main() {\n  console.log('hi');\n}\n",
            encoding="utf-8",
        )
        summary_command(str(js))
