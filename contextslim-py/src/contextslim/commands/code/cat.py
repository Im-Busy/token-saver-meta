"""cat — read file with blank stripping and truncation."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.text import Text

from contextslim.compressor.text import cap_line_width, strip_blanks
from contextslim.config import Config

console = Console(highlight=False)
TRUNC_MARKER = "\u2702\ufe0f  TRUNCATED ({skipped} lines)"


def cat_command(file: str, config: Config) -> None:
    """Read file with blank stripping and truncation.

    Shows head+tail if file exceeds ``config.limits.cat_lines``.
    Strips blank lines. Caps wide lines via ``cap_line_width``.
    Reports savings stats.
    """
    path = Path(file)
    raw = path.read_text(encoding="utf-8")
    original_lines = raw.splitlines()
    original_chars = sum(len(ln) for ln in original_lines)

    # Strip blanks
    filtered, blanks_removed = strip_blanks(original_lines)

    limit = config.limits.cat_lines
    max_width = config.limits.max_line_width

    if len(filtered) <= limit:
        shown = [cap_line_width(ln, max_width) for ln in filtered]
        truncated = 0
    else:
        half = limit // 2
        head = [cap_line_width(ln, max_width) for ln in filtered[:half]]
        tail = [cap_line_width(ln, max_width) for ln in filtered[-half:]]
        truncated = len(filtered) - 2 * half
        marker = TRUNC_MARKER.format(skipped=truncated)
        shown = head + [marker] + tail

    # Header
    header = Text()
    header.append(path.name, style="bold cyan")
    header.append("  ", style="")
    header.append(str(path), style="dim")
    console.print(header)
    console.print("─" * 60, style="dim")

    # Body with line numbers
    if limit < len(filtered):
        # Truncated: show head with real numbers, then tail with continuing numbers
        half = limit // 2
        for i, ln in enumerate(head, start=1):
            console.print(f"{i:>4} \u2502 {ln}")

        # Marker
        marker_text = Text(TRUNC_MARKER.format(skipped=truncated), style="dim")
        console.print(f"{'':>4} \u2502 ", marker_text)

        tail_start = half + truncated + 1
        for i, ln in enumerate(tail, start=tail_start):
            console.print(f"{i:>4} \u2502 {ln}")
    else:
        for i, ln in enumerate(shown, start=1):
            console.print(f"{i:>4} \u2502 {ln}")

    # Stats footer
    console.print("─" * 60, style="dim")

    shown_chars = sum(len(ln) for ln in shown)
    save_pct = 0.0
    if original_chars > 0:
        save_pct = (1 - shown_chars / original_chars) * 100

    console.print(
        f"Shown {len(shown)} lines. "
        f"Stripped {blanks_removed} blank lines. "
        f"Saved ~{save_pct:.0f}% tokens.",
        style="dim",
    )
