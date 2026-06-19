"""Network interfaces info command using psutil."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table


def netinfo_command() -> None:
    """Print network interfaces with addresses and status.

    Uses psutil.net_if_addrs() and psutil.net_if_stats().
    If psutil is missing, prints install instruction and exits.
    """
    try:
        import psutil
    except ImportError:
        print("psutil not installed. pip install psutil")
        return

    console = Console()
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()

    table = Table(title="Network Interfaces", padding=(0, 1))
    table.add_column("Interface", style="cyan")
    table.add_column("Addresses", style="white")
    table.add_column("Status", style="yellow")
    table.add_column("Speed", style="dim")

    for iface_name in sorted(addrs.keys()):
        iface_addrs = addrs.get(iface_name, [])
        iface_stats = stats.get(iface_name)

        addr_lines: list[str] = []
        for addr in iface_addrs:
            family = str(addr.family)
            address = addr.address or ""
            netmask = addr.netmask or ""
            bc = addr.broadcast or ""
            if "AF_INET" in family or "AddressFamily.AF_INET" in family:
                addr_lines.append(f"IPv4: {address}")
            elif "AF_INET6" in family or "AddressFamily.AF_INET6" in family:
                addr_lines.append(f"IPv6: {address}")
            elif "AF_LINK" in family or "AF_PACKET" in family or "mac" in family.lower():
                addr_lines.append(f"MAC:  {address}")
            else:
                addr_lines.append(f"{family}: {address}")

        status_str = "up" if iface_stats and iface_stats.isup else "down"
        speed_str = f"{iface_stats.speed} Mbps" if iface_stats and iface_stats.speed else "-"

        table.add_row(iface_name, "\n".join(addr_lines) if addr_lines else "-", status_str, speed_str)

    console.print(table)
