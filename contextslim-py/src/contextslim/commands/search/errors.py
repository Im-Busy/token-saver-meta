"""Extract only error/warning lines from log files.

Captures Python tracebacks (multi-line) and strips timestamps.
"""

from __future__ import annotations

import re
from pathlib import Path

from contextslim.compressor.text import strip_blanks, strip_timestamps

# Matching lines (case-insensitive).
_ERROR_PATTERN = re.compile(
    r"(ERROR|WARN|FATAL|CRITICAL|FAIL|EXCEPTION|Traceback)",
    re.IGNORECASE,
)

# Start of a Python traceback: "Traceback (most recent call last):"
_TRACEBACK_START = re.compile(r"Traceback\s*\(most recent call last\)", re.IGNORECASE)
# Lines after Traceback are indented or start with File "...".
_TRACEBACK_CONT = re.compile(
    r"^\s+(File\s+\".*\",\s+line\s+\d+|[\w\.]+(?:Error|Exception|Warning)(?:\:|$))"
)


def _read_log(file: str) -> list[str]:
    """Read log file, return lines."""
    try:
        return Path(file).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def _extract_errors(lines: list[str], max_lines: int) -> str:
    """Filter *lines* to error/warning lines and tracebacks.

    Python tracebacks: when we hit ``Traceback (most recent call last):``,
    we capture it and subsequent indented/File lines until the next blank
    or non-traceback line.
    """
    result: list[str] = []
    in_traceback = False

    for line in lines:
        # Check traceback continuation first
        if in_traceback:
            # Continue capturing traceback frames
            if _TRACEBACK_CONT.match(line) or _TRACEBACK_START.match(line):
                result.append(line)
                continue
            elif line.strip() == "":
                in_traceback = False
                continue
            else:
                # Traceback content line (e.g. the exception message itself)
                result.append(line)
                in_traceback = False
                continue

        # Start of a traceback
        if _TRACEBACK_START.match(line):
            in_traceback = True
            result.append(line)
            continue

        # Single-line error/warn
        if _ERROR_PATTERN.search(line):
            result.append(line)

    if len(result) > max_lines > 0:
        head = max_lines // 2
        tail = max_lines - head - 1
        result = (
            result[:head]
            + [f"… [truncated {len(result) - head - tail} lines] …"]
            + result[-tail:]
        )

    # Strip timestamps from each line, then strip blanks
    stripped = [strip_timestamps(line) for line in result]
    final, _ = strip_blanks(stripped)
    return "\n".join(final)


def errors_command(file: str, max_lines: int = 50) -> None:
    """Extract only error/warning/traceback lines from log file.

    Args:
        file: Path to log file.
        max_lines: Maximum lines to output (default 50).
    """
    lines = _read_log(file)
    if not lines:
        print("  [file not found or empty]")
        return

    output = _extract_errors(lines, max_lines)
    if not output:
        print("  [dim]No errors/warnings found.[/dim]")
    else:
        print(output)
