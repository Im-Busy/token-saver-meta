"""Text compression utilities — compact output for token efficiency."""

from __future__ import annotations

import re
from typing import Sequence

# ---------------------------------------------------------------------------
# Truncation
# ---------------------------------------------------------------------------

TRUNC_MARKER = "… [truncated {skipped} lines] …"


def truncate_middle(lines: list[str], max_lines: int) -> list[str]:
    """Keep *head* and *tail* of *lines*, inserting a truncation marker
    when the input exceeds *max_lines*.

    Strategy
    --------
    * ``max_lines <= 0`` → empty list (degenerate).
    * ``len(lines) <= max_lines`` → *lines* unchanged.
    * ``max_lines < 3`` → just the first *max_lines* lines (no tail).
    * Otherwise split: ``head = max_lines // 2``, ``tail = max_lines - head - 1``
      (the ``-1`` reserves a slot for the marker).
    """
    n = len(lines)
    if max_lines <= 0:
        return []
    if n <= max_lines:
        return list(lines)

    # Too few lines to give meaningful head + tail + marker.
    if max_lines < 3:
        return lines[:max_lines]

    head = max_lines // 2
    tail = max_lines - head - 1  # one slot for the marker
    skipped = n - head - tail
    marker = TRUNC_MARKER.format(skipped=skipped)
    return lines[:head] + [marker] + lines[-tail:]


# ---------------------------------------------------------------------------
# Blank removal
# ---------------------------------------------------------------------------

def strip_blanks(lines: Sequence[str]) -> tuple[list[str], int]:
    """Remove empty or whitespace-only lines.

    Returns ``(filtered_lines, count_removed)``.
    """
    filtered: list[str] = []
    removed = 0
    for line in lines:
        if line.strip():
            filtered.append(line)
        else:
            removed += 1
    return filtered, removed


# ---------------------------------------------------------------------------
# Timestamp stripping
# ---------------------------------------------------------------------------

# ISO-8601 date[ T time[Z|±hh[:mm]]]  e.g.  "2024-01-15T10:30:45.123Z"
# Anchored at BOL — mid-line dates are NOT timestamps.
_ISO_TS = re.compile(
    r"^\d{4}-\d{2}-\d{2}"               # date (BOL-anchored)
    r"(?:[T ]\d{2}:\d{2}:\d{2}"         # time
    r"(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?"  # fractional / tz
    r")?"
)

# Unix-style numeric timestamp (10+ digits) anchored at BOL.
_UNIX_TS = re.compile(r"^\d{10,}(?:\.\d+)?\s")


def strip_timestamps(line: str) -> str:
    """Remove leading ISO-8601 date/time and Unix-epoch timestamps
    from *line*.  Returns the stripped string.
    """
    s = _ISO_TS.sub("", line, count=1).lstrip()
    s = _UNIX_TS.sub("", s, count=1)
    return s


# ---------------------------------------------------------------------------
# Line-width capping
# ---------------------------------------------------------------------------

ELLIPSIS = "…"


def cap_line_width(line: str, width: int) -> str:
    """Truncate *line* longer than *width* chars, appending ``…``."""
    if width <= 0:
        return ""
    if len(line) <= width:
        return line
    # Reserve one character for the ellipsis.
    return line[: width - 1] + ELLIPSIS
