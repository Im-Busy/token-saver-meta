"""head — show first N lines with blank stripping."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.text import Text

from contextslim.compressor.text import cap_line_width, strip_blanks
from contextslim.config import Config

console = Console(highlight=False)


def head_command(file: str, lines: int, config: Config) -> None:
    """Show first N lines with blank stripping.

    Strips blank lines before counting. Caps wide lines.
    Reports savings stats.
    """
    path = Path(file)
    raw = path.read_text(encoding="utf-8")
    original_lines = raw.splitlines()
    original_chars = sum(len(ln) for ln in original_lines)

    # Strip blanks first, then take first N non-blank lines
    filtered, blanks_removed = strip_blanks(original_lines)
    max_width = config.limits.max_line_width

    shown = [cap_line_width(ln, max_width) for ln in filtered[:lines]]

    # Header
    header = Text()
    header.append(path.name, style="bold cyan")
    header.append("  ", style="")
    header.append(f"first {len(shown)} lines", style="dim")
    console.print(header)
    console.print("─" * 60, style="dim")

    # Body with line numbers
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
