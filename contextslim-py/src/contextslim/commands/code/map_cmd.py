"""map — extract structural signatures only."""

from __future__ import annotations

import re
from pathlib import Path

from rich.console import Console
from rich.text import Text

from contextslim.compressor.code import extract_signatures

console = Console(highlight=False)

# Color mapping: keyword group → rich style
_KEYWORD_COLORS: list[tuple[str, str]] = [
    (r"\bfunction\b", "cyan"),
    (r"\bdef\b", "cyan"),
    (r"\bclass\b", "magenta"),
    (r"\binterface\b", "magenta"),
    (r"\btype\b", "magenta"),
    (r"\benum\b", "magenta"),
    (r"\bconst\b", "yellow"),
    (r"\blet\b", "yellow"),
    (r"\bvar\b", "yellow"),
]


def _colorize_line(line: str) -> Text:
    """Apply rich colors to keywords in a signature line."""
    text = Text(line.rstrip("\n"))
    for pattern, style in _KEYWORD_COLORS:
        for m in re.finditer(pattern, text.plain):
            start, end = m.span()
            text.stylize(style, start, end)
    return text


def map_command(file: str) -> None:
    """Extract structural signatures only (functions, classes, exports).

    Reads file, calls ``extract_signatures``, outputs with colorized
    keywords. Reports token savings.
    """
    path = Path(file)
    raw = path.read_text(encoding="utf-8")
    original_lines = raw.splitlines()
    original_chars = sum(len(ln) for ln in original_lines)

    sigs = extract_signatures(original_lines)

    # Header
    header = Text()
    header.append(path.name, style="bold cyan")
    header.append("  ", style="")
    header.append("signatures", style="dim")
    console.print(header)
    console.print("─" * 60, style="dim")

    if not sigs:
        console.print("No structural signatures found.", style="yellow")
        return

    # Body: colorized signature lines
    for ln in sigs:
        console.print(_colorize_line(ln))

    # Stats footer
    console.print("─" * 60, style="dim")

    sig_chars = sum(len(ln.rstrip("\n")) for ln in sigs)
    save_pct = 0.0
    if original_chars > 0:
        save_pct = (1 - sig_chars / original_chars) * 100

    console.print(
        f"Extracted {len(sigs)} signatures. "
        f"Saved ~{save_pct:.0f}% tokens.",
        style="dim",
    )
