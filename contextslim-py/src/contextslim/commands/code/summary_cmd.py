"""summary — structured file stats (lines, imports, functions, classes, savings)."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.text import Text

from contextslim.compressor.code import extract_imports, extract_signatures

console = Console(highlight=False)


def _count_blank_lines(lines: list[str]) -> int:
    return sum(1 for ln in lines if not ln.strip())


def _count_comment_lines(lines: list[str]) -> int:
    """Count lines that are pure comments (# or //)."""
    count = 0
    for ln in lines:
        stripped = ln.strip()
        if stripped.startswith("#") or stripped.startswith("//"):
            count += 1
        elif stripped.startswith("/*") or stripped.startswith("*"):
            count += 1
    return count


def _estimate_tokens(lines: list[str]) -> int:
    """Crude token estimate: bytes / 4."""
    return sum(len(ln.encode("utf-8")) for ln in lines) // 4


def _format_num(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def summary_command(file: str) -> None:
    """Structured file stats (lines, imports, functions, etc).

    Counts total lines, blank lines, comment lines, imports,
    function/class signatures. Displays a Rich table with stats
    and estimated token savings.
    """
    path = Path(file)
    if not path.is_file():
        console.print(f"[red]Error:[/red] File not found: {file}")
        return

    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = raw.splitlines()
    total_lines = len(lines)
    blank_lines = _count_blank_lines(lines)
    comment_lines = _count_comment_lines(lines)
    code_lines = total_lines - blank_lines - comment_lines

    # Extract structural info
    imports = extract_imports(lines)
    signatures = extract_signatures(lines)

    # Separate functions (starting with "def" or "fn" or "func") from classes
    func_count = 0
    class_count = 0
    const_count = 0
    for sig in signatures:
        stripped = sig.strip()
        if "class " in stripped.split("=")[0]:
            class_count += 1
        elif any(
            kw in stripped for kw in ("def ", "fn ", "func ", "function ", "async def ", "async fn ")
        ):
            func_count += 1
        elif any(
            kw in stripped
            for kw in ("interface ", "type ", "enum ", "const ", "let ", "var ")
        ):
            const_count += 1
        else:
            # Heuristic: everything else is likely an exported const/var
            const_count += 1

    byte_size = len(raw.encode("utf-8"))
    raw_tokens = byte_size // 4
    code_bytes = sum(len(ln.encode("utf-8")) for ln in lines if ln.strip())
    code_tokens = code_bytes // 4

    # Header
    header = Text()
    header.append(path.name, style="bold cyan")
    header.append("  ", style="")
    header.append(f"({total_lines} lines, {byte_size:,} bytes)", style="dim")
    console.print(header)
    console.print()

    # Table 1: Composition
    comp = Table(title="File Composition", show_header=False, box=None)
    comp.add_column("Metric", style="dim")
    comp.add_column("Value", justify="right")
    comp.add_column("Pct", justify="right", style="dim")

    comp.add_row("Total lines", str(total_lines), "100%")
    comp.add_row("  Code lines", str(code_lines), f"{code_lines / max(total_lines, 1) * 100:.0f}%")
    comp.add_row("  Blank lines", str(blank_lines), f"{blank_lines / max(total_lines, 1) * 100:.0f}%")
    comp.add_row(
        "  Comment lines", str(comment_lines), f"{comment_lines / max(total_lines, 1) * 100:.0f}%"
    )
    console.print(comp)
    console.print()

    # Table 2: Structure
    struct = Table(title="Structure", show_header=False, box=None)
    struct.add_column("Metric", style="dim")
    struct.add_column("Value", justify="right")

    struct.add_row("Imports/requires", str(len(imports)))
    struct.add_row("Functions/methods", str(func_count))
    struct.add_row("Classes", str(class_count))
    if const_count:
        struct.add_row("Types/consts/exports", str(const_count))
    struct.add_row("Total signatures", str(len(signatures)))
    console.print(struct)
    console.print()

    # Table 3: Token estimate
    token_table = Table(title="Token Estimate", show_header=False, box=None)
    token_table.add_column("Metric", style="dim")
    token_table.add_column("Value", justify="right")

    token_table.add_row("File size", f"{byte_size:,} bytes")
    token_table.add_row("Raw token estimate (÷4)", _format_num(raw_tokens))
    token_table.add_row("Code-only tokens", _format_num(code_tokens))
    if raw_tokens > 0:
        savings_pct = (1 - code_tokens / max(raw_tokens, 1)) * 100
        token_table.add_row("Potential savings", f"~{savings_pct:.0f}% (blank+comment)")
    console.print(token_table)
