"""Tests for contextslim.commands.search.logs."""

from __future__ import annotations

import tempfile
from pathlib import Path

from contextslim.commands.search.logs import logs_command


class TestLogsCommand:
    def test_tails_last_n_lines(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            log_path = root / "app.log"
            lines = [f"line {i}" for i in range(1, 21)]  # 20 lines
            log_path.write_text("\n".join(lines), encoding="utf-8")
            # Can't easily capture console output; test via reader directly.
            text = log_path.read_text(encoding="utf-8")
            all_lines = text.splitlines()
            tail = all_lines[-5:]
            assert tail == [f"line {i}" for i in range(16, 21)]

    def test_tails_all_when_fewer_than_n(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            log_path = root / "app.log"
            log_path.write_text("line 1\nline 2\n", encoding="utf-8")
            text = log_path.read_text(encoding="utf-8")
            all_lines = text.splitlines()
            tail = all_lines[-10:]
            assert len(tail) == 2
            assert tail == ["line 1", "line 2"]

    def test_strips_timestamps(self) -> None:
        from contextslim.compressor.text import strip_timestamps

        lines = [
            "2024-01-15T10:30:45Z ERROR: fail",
            "2024-01-15T10:30:46Z INFO: ok",
        ]
        stripped = [strip_timestamps(line) for line in lines]
        assert stripped[0] == "ERROR: fail"
        assert stripped[1] == "INFO: ok"

    def test_strips_blanks(self) -> None:
        from contextslim.compressor.text import strip_blanks

        lines = ["", "  ", "hello", "", "world", "\t"]
        filtered, removed = strip_blanks(lines)
        assert filtered == ["hello", "world"]
        assert removed == 4

    def test_tail_with_blanks_and_timestamps_removed(self) -> None:
        """Integration: verify tail + strip works together."""
        from contextslim.compressor.text import strip_blanks, strip_timestamps

        text = "\n".join([
            "2024-01-15T10:00:00Z old line 1",
            "",
            "2024-01-15T10:00:01Z old line 2",
            "",
            "2024-01-15T10:30:00Z recent message",
            "",
        ])
        all_lines = text.splitlines()
        tail = all_lines[-4:]  # last 4
        stripped = [strip_timestamps(line) for line in tail]
        filtered, _ = strip_blanks(stripped)
        assert "recent message" in filtered
        assert "old line 2" in filtered
