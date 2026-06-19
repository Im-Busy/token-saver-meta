"""`contextslim system disk` — filesystem overview + top directory sizes."""

from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()


def _fmt_bytes(n: int) -> str:
    """Format byte count to human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def _dir_size(path: Path) -> int:
    """Recursively compute directory size in bytes."""
    total = 0
    try:
        for entry in path.iterdir():
            if entry.is_file(follow_symlinks=False):
                try:
                    total += entry.stat().st_size
                except OSError:
                    pass
            elif entry.is_dir(follow_symlinks=False):
                total += _dir_size(entry)
    except PermissionError:
        pass
    return total


def disk_command(directory: str = ".") -> None:
    """Show filesystem overview for *directory* and top subdirectory sizes.

    Uses ``shutil.disk_usage()`` for the mount and scans immediate
    children for size breakdown.
    """
    root = Path(directory).resolve()
    if not root.is_dir():
        console.print(f"[red]Error:[/] '{directory}' is not a directory")
        return

    # Disk usage for the mounted filesystem
    try:
        usage = shutil.disk_usage(root)
    except OSError:
        console.print(f"[red]Error:[/] cannot access disk usage for '{directory}'")
        return

    console.print(f"\n[bold]Disk: {root}[/]")
    console.print(f"  Total : {_fmt_bytes(usage.total)}")
    console.print(f"  Used  : {_fmt_bytes(usage.used)} ({usage.used / max(usage.total, 1) * 100:.1f}%)")
    console.print(f"  Free  : {_fmt_bytes(usage.free)}")

    # Top subdirectory sizes
    entries: list[tuple[str, int]] = []
    try:
        for child in sorted(root.iterdir()):
            if child.is_dir(follow_symlinks=False):
                entries.append((child.name, _dir_size(child)))
            elif child.is_file(follow_symlinks=False):
                try:
                    entries.append((child.name, child.stat().st_size))
                except OSError:
                    pass
    except PermissionError:
        pass

    if not entries:
        console.print("\n[dim]No readable children[/]")
        return

    # Sort by size descending, top 20
    entries.sort(key=lambda x: x[1], reverse=True)
    entries = entries[:20]

    table = Table(title="Top Directories & Files", show_header=True, header_style="bold")
    table.add_column("Name", style="cyan", max_width=40)
    table.add_column("Size", style="yellow", justify="right")
    table.add_column("Share", style="green")

    for name, size in entries:
        pct = (size / max(usage.total, 1)) * 100
        table.add_row(name, _fmt_bytes(size), f"{pct:.2f}%")

    console.print(table)
