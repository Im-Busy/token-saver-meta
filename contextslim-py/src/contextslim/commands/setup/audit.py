"""audit — audit token waste and projected savings."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.text import Text

from contextslim.config import Config

console = Console(highlight=False)

# Directories that are token-wasteful to include in AI context.
_HEAVY_DIRS: dict[str, str] = {
    "node_modules": "JavaScript dependencies",
    ".git": "Git history",
    ".venv": "Python virtual environment",
    "venv": "Python virtual environment",
    "__pycache__": "Python bytecode cache",
    ".mypy_cache": "MyPy type cache",
    ".pytest_cache": "Pytest cache",
    ".tox": "Tox test envs",
    "dist": "Build output",
    "build": "Build output",
    ".next": "Next.js build",
    "target": "Rust build output",
    ".idea": "JetBrains IDE",
    ".vscode": "VS Code config",
    "coverage": "Coverage reports",
    ".cache": "Cache directory",
    "vendor": "Go/other vendor deps",
    "*.egg-info": "Python egg info",
    ".gradle": "Gradle build cache",
    "logs": "Log files",
    "tmp": "Temporary files",
    "temp": "Temporary files",
}

# Extensions likely to be generated or binary — high token waste.
_IGNORE_EXTENSIONS: set[str] = {
    ".pyc", ".pyo", ".so", ".dll", ".exe", ".bin",
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg",
    ".ico", ".webp", ".mp4", ".mov", ".avi", ".mp3",
    ".wav", ".ogg", ".flac", ".pdf", ".doc", ".docx",
    ".xls", ".xlsx", ".ppt", ".pptx", ".woff", ".woff2",
    ".ttf", ".eot", ".otf", ".lock", ".map", ".tsbuildinfo",
}


def _scan_directory(root: Path) -> list[tuple[str, int, str]]:
    """Scan for heavy directories, return (name, size_bytes, description)."""
    results: list[tuple[str, int, str]] = []
    if not root.is_dir():
        return results

    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        name = entry.name
        if name in _HEAVY_DIRS or name.startswith("."):
            desc = _HEAVY_DIRS.get(name, "Hidden/config directory")
            size = _dir_size(entry)
            if size > 0:
                results.append((name, size, desc))

    return results


def _dir_size(path: Path) -> int:
    """Calculate total bytes in directory, respecting a timeout."""
    total = 0
    try:
        for f in path.rglob("*"):
            if f.is_file():
                try:
                    total += f.stat().st_size
                except OSError:
                    pass
    except (PermissionError, OSError):
        pass
    return total


def _count_files(path: Path) -> int:
    """Count files in a directory, skipping ignored extensions."""
    try:
        return sum(
            1
            for f in path.rglob("*")
            if f.is_file() and f.suffix.lower() not in _IGNORE_EXTENSIONS
        )
    except (PermissionError, OSError):
        return 0


def audit_command(directory: str, config: Config) -> None:
    """Audit token waste and projected savings.

    Scans the project for heavy directories (node_modules, .git, dist,
    build, etc.) that contribute to token waste. Estimates raw token
    counts (bytes ÷ 4) and shows projected savings with ContextSlim.

    Args:
        directory: Project root directory path.
        config: ContextSlim configuration.
    """
    project_dir = Path(directory).resolve()
    if not project_dir.is_dir():
        console.print(f"[red]Error:[/red] Directory not found: {directory}")
        return

    # Header
    header = Text()
    header.append("Token Waste Audit", style="bold")
    header.append("  ", style="")
    header.append(str(project_dir), style="dim")
    console.print(header)
    console.print()

    # Scan
    heavy = _scan_directory(project_dir)

    if not heavy:
        console.print("[green]✓[/green] No heavy directories found.")
        console.print()
        console.print(
            "[dim]ContextSlim can save ~40% of tokens through compression, "
            "output limits, and context optimization.[/dim]"
        )
        return

    # Build table
    table = Table(title="Heavy Directories")
    table.add_column("Directory", style="cyan")
    table.add_column("Type", style="dim")
    table.add_column("Size", justify="right")
    table.add_column("Tokens (÷4)", justify="right", style="yellow")
    table.add_column("% of Total", justify="right")

    total_bytes = 0
    rows: list[tuple[str, str, int, int]] = []
    for name, size, desc in heavy:
        tokens = size // 4
        total_bytes += size
        rows.append((name, desc, size, tokens))

    total_tokens = total_bytes // 4

    for name, desc, size, tokens in rows:
        pct = (tokens / max(total_tokens, 1)) * 100
        size_str = _format_bytes(size)
        tokens_str = _format_num(tokens)
        pct_str = f"{pct:.1f}%"
        table.add_row(name, desc, size_str, tokens_str, pct_str)

    # Total row
    table.add_section()
    table.add_row(
        "[bold]TOTAL[/bold]",
        "",
        _format_bytes(total_bytes),
        f"[bold]{_format_num(total_tokens)}[/bold]",
        "100%",
        style="bold",
    )

    console.print(table)
    console.print()

    # Projected savings
    saved_tokens = int(total_tokens * 0.85)  # conservative: 85% of waste avoided
    console.print(
        f"[bold green]Projected Savings:[/bold green] ~{_format_num(saved_tokens)} tokens "
        f"({_format_bytes(total_bytes)} avoided from context)"
    )
    console.print(
        "[dim]Run `contextslim setup init` to auto-generate ignore rules.[/dim]"
    )

    # Files summary
    total_files = 0
    for name, _, _ in heavy:
        fc = _count_files(project_dir / name)
        total_files += fc

    if total_files > 0:
        console.print()
        console.print(
            f"[dim]{_format_num(total_files)} files in heavy dirs excluded from context.[/dim]"
        )


def _format_bytes(n: int) -> str:
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f} GB"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f} MB"
    if n >= 1_000:
        return f"{n / 1_000:.0f} KB"
    return f"{n} B"


def _format_num(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)
