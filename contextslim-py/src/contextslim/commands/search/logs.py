"""Last N lines of log, timestamps stripped, blanks removed."""

from __future__ import annotations

from pathlib import Path

from contextslim.compressor.text import strip_blanks, strip_timestamps


def logs_command(file: str, lines: int = 100) -> None:
    """Last *lines* lines of log file, timestamps stripped, blanks removed.

    Args:
        file: Path to log file.
        lines: Number of lines to tail (default 100).
    """
    try:
        text = Path(file).read_text(encoding="utf-8", errors="replace")
    except OSError:
        print("  [file not found or empty]")
        return

    all_lines = text.splitlines()
    tail = all_lines[-lines:] if len(all_lines) > lines else all_lines

    stripped = [strip_timestamps(line) for line in tail]
    filtered, _ = strip_blanks(stripped)

    if not filtered:
        print("  [dim]No content.[/dim]")
        return

    for line in filtered:
        print(line)
