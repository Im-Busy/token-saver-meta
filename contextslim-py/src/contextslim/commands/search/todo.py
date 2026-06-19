"""Find TODO/FIXME/HACK/BUG/XXX/OPTIMIZE/NOTE/REFACTOR/TEMP comments.

Walks project files, skips ignored directories and binary files,
groups results by file with line numbers.
"""

from __future__ import annotations

import re
from pathlib import Path

from rich.console import Console
from rich.table import Table

from contextslim.config import Config, DEFAULT_CONFIG

# Directories never scanned.
_IGNORED_DIRS: set[str] = {
    ".git", "node_modules", "dist", "build", ".next",
    "__pycache__", ".mypy_cache", ".pytest_cache", ".venv", "venv",
    "target", "vendor", ".tox", ".eggs", "coverage",
}

# Binary extensions (by common extension).
_BINARY_EXTS: set[str] = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
    ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z",
    ".exe", ".dll", ".so", ".dylib",
    ".pyc", ".pyo", ".class", ".o", ".obj",
    ".db", ".sqlite", ".sqlite3",
    ".lock",  # lock files omitted
}

_TODO_PATTERN = re.compile(
    r"(TODO|FIXME|HACK|BUG|XXX|OPTIMIZE|NOTE|REFACTOR|TEMP)[s:]*\s*(.+)", re.IGNORECASE
)


def _is_binary(path: Path) -> bool:
    """Heuristic: skip known binary extensions and files with null bytes."""
    ext = path.suffix.lower()
    if ext in _BINARY_EXTS:
        return True
    # Quick null-byte check for files without known binary extensions.
    try:
        with path.open("rb") as f:
            chunk = f.read(512)
            return b"\x00" in chunk
    except OSError:
        return True


def _walk_todos(directory: str) -> dict[str, list[tuple[int, str, str]]]:
    """Walk *directory*, find TODO-like comments.

    Returns ``{rel_path: [(line_no, tag, message), ...]}``.
    """
    root = Path(directory)
    results: dict[str, list[tuple[int, str, str]]] = {}

    for file_path in root.rglob("*"):
        # Skip ignored directories
        if any(part in _IGNORED_DIRS for part in file_path.parts):
            continue
        if not file_path.is_file():
            continue
        if _is_binary(file_path):
            continue

        try:
            lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        file_matches: list[tuple[int, str, str]] = []
        for lineno, line in enumerate(lines, start=1):
            m = _TODO_PATTERN.search(line)
            if m:
                tag = m.group(1).upper()
                message = m.group(2).strip()
                file_matches.append((lineno, tag, message))

        if file_matches:
            rel = str(file_path.relative_to(root))
            results[rel] = file_matches

    return results


def todo_command(directory: str, config: Config | None = None) -> None:
    """Find TODO/FIXME/HACK/BUG/XXX/OPTIMIZE/NOTE/REFACTOR/TEMP comments.

    Args:
        directory: Project root to scan.
        config: Config with limits.todo_max_total cap (default 50).
    """
    cfg = config if config is not None else DEFAULT_CONFIG
    max_total = cfg.limits.todo_max_total
    console = Console()
    found = _walk_todos(directory)

    if not found:
        console.print("[dim]No TODO/FIXME/BUG/etc comments found.[/dim]")
        return

    table = Table(title="Code Annotations", show_header=True, header_style="bold")
    table.add_column("File", style="cyan", max_width=60, overflow="fold")
    table.add_column("Line", style="yellow", justify="right")
    table.add_column("Tag", style="red")
    table.add_column("Message", style="white")

    count = 0
    for file_path, matches in sorted(found.items()):
        for lineno, tag, message in matches:
            count += 1
            if count > max_total:
                continue
            table.add_row(file_path, str(lineno), tag, message)

    console.print(table)
    if count > max_total:
        console.print(f"\n[dim yellow]… capped at {max_total} (total: {count})[/dim yellow]")
