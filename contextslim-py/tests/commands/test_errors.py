"""Tests for contextslim.commands.search.errors."""

from __future__ import annotations

import tempfile
from pathlib import Path

from contextslim.commands.search.errors import _extract_errors, _read_log


class TestReadLog:
    def test_reads_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            log = root / "test.log"
            log.write_text("line 1\nline 2\n", encoding="utf-8")
            lines = _read_log(str(log))
            assert lines == ["line 1", "line 2"]

    def test_missing_file(self) -> None:
        lines = _read_log("/nonexistent/log.log")
        assert lines == []


class TestExtractErrors:
    def test_filters_error_lines(self) -> None:
        lines = [
            "2024-01-15 INFO: Starting app",
            "2024-01-15 ERROR: Connection failed",
            "2024-01-15 DEBUG: Processing...",
            "2024-01-15 WARN: Disk space low",
            "2024-01-15 FATAL: Out of memory",
            "2024-01-15 CRITICAL: Shutting down",
            "2024-01-15 INFO: Retrying...",
        ]
        result = _extract_errors(lines, 50)
        assert "ERROR" in result
        assert "WARN" in result
        assert "FATAL" in result
        assert "CRITICAL" in result
        assert "INFO" not in result
        assert "DEBUG" not in result
        assert "Retrying" not in result

    def test_case_insensitive(self) -> None:
        lines = [
            "2024-01-15 error: something broke",
            "2024-01-15 Error: another thing broke",
        ]
        result = _extract_errors(lines, 50)
        assert "error:" in result.lower()
        assert "Error:" in result

    def test_captures_traceback(self) -> None:
        lines = [
            "2024-01-15 INFO: Starting request",
            "Traceback (most recent call last):",
            '  File "main.py", line 42, in <module>',
            "    do_thing()",
            '  File "main.py", line 10, in do_thing',
            "    raise ValueError('bad value')",
            "ValueError: bad value",
            "2024-01-15 INFO: Request completed",
        ]
        result = _extract_errors(lines, 50)
        assert "Traceback" in result
        assert "main.py" in result
        assert "ValueError" in result
        assert "INFO: Starting request" not in result
        assert "INFO: Request completed" not in result

    def test_strips_timestamps(self) -> None:
        lines = [
            "2024-01-15T10:30:45Z ERROR: Request timeout",
            "2024-01-15T10:30:46Z INFO: Retrying",
        ]
        result = _extract_errors(lines, 50)
        assert "2024-01-15" not in result
        assert "ERROR: Request timeout" in result
        assert "INFO" not in result

    def test_caps_at_max_lines(self) -> None:
        lines = [f"ERROR: error number {i}" for i in range(100)]
        result = _extract_errors(lines, 10)
        assert "truncated" in result
        result_lines = result.splitlines()
        assert len(result_lines) == 10

    def test_no_errors(self) -> None:
        lines = [
            "2024-01-15 INFO: All good",
            "2024-01-15 DEBUG: Processing done",
        ]
        result = _extract_errors(lines, 50)
        assert result == ""

    def test_exception_keyword_matched(self) -> None:
        lines = [
            "2024-01-15 INFO: EXCEPTION occurred in handler",
        ]
        result = _extract_errors(lines, 50)
        assert "EXCEPTION" in result.upper()

    def test_fail_keyword_matched(self) -> None:
        lines = [
            "2024-01-15 FAIL: test_foo failed",
        ]
        result = _extract_errors(lines, 50)
        assert "FAIL" in result

    def test_empty_input(self) -> None:
        result = _extract_errors([], 50)
        assert result == ""
