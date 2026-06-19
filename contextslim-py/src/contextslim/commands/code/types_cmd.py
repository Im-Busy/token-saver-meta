"""Extract only TypeScript interface/type/enum declarations from a file."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.panel import Panel
from rich.text import Text

from contextslim.compressor.code import extract_types

console = Console(highlight=False)


class _TypeHighlighter(RegexHighlighter):
    """Highlight TS type keywords."""
    base_style = "type."
    highlights = [
        r"\binterface\b",
        r"\btype\b",
        r"\benum\b",
        r"\bexport\b",
        r"\bextends\b",
        r"\bimplements\b",
    ]


def types_command(file: str) -> None:
    """Read *file*, extract TS type declarations, report savings."""
    path = Path(file).resolve()
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        console.print(f"[red]Cannot read: {file}[/]")
        return

    lines = raw.splitlines()
    typed = extract_types(lines)

    if not typed:
        console.print("[dim]No types found.[/]")
        return

    body = Text()
    for ln in typed:
        body.append(ln.rstrip())
        body.append("\n")

    highlighter = _TypeHighlighter()
    body = highlighter(body)

    orig_lines = len(lines)
    extracted_lines = len(typed)
    savings_pct = int((1 - extracted_lines / max(orig_lines, 1)) * 100) if orig_lines else 100

    body.append(f"\n{extracted_lines} lines ({savings_pct}% saved vs {orig_lines} total)", style="italic")

    console.print(Panel(body, title=f"Types — {path.name}"))
