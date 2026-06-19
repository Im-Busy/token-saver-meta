"""`contextslim system ports` — open ports list using psutil.net_connections()."""

from __future__ import annotations

from collections import defaultdict

from rich.console import Console
from rich.table import Table

console = Console()


def ports_command(name_filter: str | None = None) -> None:
    """List open network connections, grouped by process.

    Uses ``psutil.net_connections()``.  Filters by *name_filter*
    (matched case-insensitively against process name or local port).
    """
    try:
        import psutil  # type: ignore[import-not-found]
    except ImportError:
        console.print("[red]Error:[/] psutil not installed")
        return

    try:
        conns = psutil.net_connections(kind="inet")
    except PermissionError:
        console.print("[yellow]Limited:[/] elevated permissions needed for full port listing")
        return

    # Group by PID
    by_pid: dict[int, dict] = defaultdict(
        lambda: {"name": "?", "listening": [], "established": []}
    )

    for conn in conns:
        if conn.status == "NONE":
            continue
        pid = conn.pid or 0
        entry = by_pid[pid]
        if conn.pid and not entry["name"] or entry["name"] == "?":
            try:
                proc = psutil.Process(conn.pid)
                entry["name"] = proc.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        local = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "?"
        remote = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "-"

        if conn.status == "LISTEN":
            entry["listening"].append(local)
        else:
            entry["established"].append(f"{local} -> {remote}")

    # Filter
    if name_filter:
        nf = name_filter.lower()
        filtered: dict[int, dict] = {}
        for pid, info in by_pid.items():
            name_lower = info["name"].lower()
            if nf in name_lower or any(nf in addr.lower() for addr in info["listening"] + info["established"]):
                filtered[pid] = info
        by_pid = filtered

    if not by_pid:
        console.print("[dim]No open ports found[/]")
        return

    table = Table(title="Open Ports", show_header=True, header_style="bold")
    table.add_column("Process", style="cyan", max_width=30)
    table.add_column("PID", style="yellow", justify="right")
    table.add_column("Listening", style="green")
    table.add_column("Connected", style="white")

    for pid, info in sorted(by_pid.items()):
        name = info["name"]
        listening = "\n".join(info["listening"][:5]) or "-"
        if len(info["listening"]) > 5:
            listening += f"\n... +{len(info['listening']) - 5} more"
        established = "\n".join(info["established"][:3]) or "-"
        if len(info["established"]) > 3:
            established += f"\n... +{len(info['established']) - 3} more"
        table.add_row(name, str(pid), listening, established)

    console.print(table)
    console.print(f"[dim]{len(by_pid)} processes shown[/]")
