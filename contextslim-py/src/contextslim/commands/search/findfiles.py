"""`contextslim search findfiles` — find files by glob, skip heavy dirs, cap results."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

from contextslim.analyzer.stack_detector import IGNORED_DIRS

if TYPE_CHECKING:
    from contextslim.config import Config

console = Console()


def findfiles_command(pattern: str, directory: str, config: "Config") -> None:
    """Find files matching *pattern* glob under *directory*.

    Skips ``IGNORED_DIRS`` and caps results at
    ``config.limits.findfiles_limit``.
    """
    root = Path(directory).resolve()
    if not root.is_dir():
        console.print(f"[red]Error:[/] '{directory}' is not a directory")
        return

    limit = config.limits.findfiles_limit
    found: list[Path] = []
    skipped = 0

    for file_path in root.rglob(pattern):
        # Skip ignored directories
        if any(part in IGNORED_DIRS for part in file_path.parts):
            continue
        if not file_path.is_file():
            continue
        skipped_in_walk = 0
        if any(part in IGNORED_DIRS for part in file_path.parts):
            continue
        if len(found) < limit:
            try:
                found.append(file_path.relative_to(root))
            except ValueError:
                found.append(file_path)
        else:
            skipped += 1

    # In a second pass, we need to know total. But for efficiency we just do rglob once.
    # The cap was already applied; we don't need an accurate skipped count from a single pass.
    # Just report what we found.

    if not found:
        console.print(f"[dim]No files matching '{pattern}' found[/]")
        return

    for rel in sorted(found):
        console.print(f"  {rel}")

    suffix = ""
    total = len(found)
    if total == limit and skipped > 0:
        suffix = f" (capped at {limit})"
    console.print(f"[dim]{total} file(s) matched '{pattern}'{suffix}[/]")
