"""Sorted process list command using psutil."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table


def procs_command(name_filter: str | None, limit: int) -> None:
    """Print processes sorted by memory usage.

    Args:
        name_filter: Optional substring to filter process names (case-insensitive).
        limit: Maximum number of processes to display.
    """
    try:
        import psutil
    except ImportError:
        print("psutil not installed. pip install psutil")
        return

    procs = []
    for p in psutil.process_iter(["pid", "name", "memory_percent", "cpu_percent", "status"]):
        try:
            info = p.info
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        name = info.get("name", "") or ""
        if name_filter and name_filter.lower() not in name.lower():
            continue
        procs.append(info)

    procs.sort(key=lambda x: x.get("memory_percent", 0) or 0, reverse=True)
    procs = procs[:limit]

    console = Console()
    table = Table(title=f"Processes (top {len(procs)} by memory)", padding=(0, 1))
    table.add_column("PID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Mem%", justify="right")
    table.add_column("CPU%", justify="right")
    table.add_column("Status", style="yellow")

    for p in procs:
        table.add_row(
            str(p.get("pid", "")),
            (p.get("name") or "")[:40],
            f"{p.get('memory_percent') or 0:.1f}",
            f"{p.get('cpu_percent') or 0:.1f}",
            p.get("status", ""),
        )

    console.print(table)
    console.print(f"[dim]{len(procs)} process(es) shown. Sorted by memory (desc).[/dim]")
