"""Compact OS/hardware info command using psutil."""

from __future__ import annotations

import datetime

from rich.console import Console
from rich.table import Table


def sysinfo_command() -> None:
    """Print compact OS/hardware info (~20 lines) using psutil.

    Reports: CPU cores, CPU usage, memory, disk, boot time.
    If psutil is missing, prints install instruction and exits.
    """
    try:
        import psutil  # noqa: F811
    except ImportError:
        print("psutil not installed. pip install psutil")
        return

    console = Console()

    # CPU
    cpu_count = psutil.cpu_count(logical=True)
    cpu_physical = psutil.cpu_count(logical=False)
    cpu_percent = psutil.cpu_percent(interval=0.1)

    # Memory
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    # Disk
    disk = psutil.disk_usage("/")

    # Boot
    boot = datetime.datetime.fromtimestamp(psutil.boot_time())

    table = Table(title="System Info", show_header=False, padding=(0, 1))
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("CPU Cores", f"{cpu_count} logical / {cpu_physical} physical")
    table.add_row("CPU Usage", f"{cpu_percent:.1f}%")
    table.add_row("Memory", _fmt_bytes(mem.used) + " / " + _fmt_bytes(mem.total) + f" ({mem.percent:.1f}%)")
    table.add_row("Swap", _fmt_bytes(swap.used) + " / " + _fmt_bytes(swap.total) + f" ({swap.percent:.1f}%)")
    table.add_row("Disk /", _fmt_bytes(disk.used) + " / " + _fmt_bytes(disk.total) + f" ({disk.percent:.1f}%)")
    table.add_row("Boot Time", str(boot))
    table.add_row("Uptime", _fmt_uptime(psutil.boot_time()))

    console.print(table)


def _fmt_bytes(b: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(b) < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def _fmt_uptime(boot_ts: float) -> str:
    """Format uptime from boot timestamp."""
    now = datetime.datetime.now()
    delta = now - datetime.datetime.fromtimestamp(boot_ts)
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    mins = rem // 60
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{mins}m")
    return " ".join(parts)
