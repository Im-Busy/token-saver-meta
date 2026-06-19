"""Extract only import/require statements from a file."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.panel import Panel
from rich.text import Text

from contextslim.compressor.code import extract_imports

console = Console(highlight=False)


class _ImportHighlighter(RegexHighlighter):
    """Highlight import/require keywords."""
    base_style = "import."
    highlights = [
        r"\bimport\b",
        r"\brequire\b",
        r"\bfrom\b",
        r"\bexport\b",
        r"\btype\b",
        r"\bas\b",
    ]


def imports_command(file: str) -> None:
    """Read *file*, extract import/require lines, report savings."""
    path = Path(file).resolve()
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        console.print(f"[red]Cannot read: {file}[/]")
        return

    lines = raw.splitlines()
    imported = extract_imports(lines)

    if not imported:
        console.print(f"[dim]No imports found in {path.name}[/]")
        return

    # Build highlighted output via Rich Panel
    body = Text()
    for ln in imported:
        body.append(ln.rstrip())
        body.append("\n")

    highlighter = _ImportHighlighter()
    body = highlighter(body)

    orig_lines = len(lines)
    extracted_lines = len(imported)
    savings_pct = int((1 - extracted_lines / max(orig_lines, 1)) * 100) if orig_lines else 100

    body.append(f"\n{extracted_lines} lines ({savings_pct}% saved vs {orig_lines} total)", style="italic")

    console.print(Panel(body, title=f"Imports — {path.name}"))
