"""Service list command — platform-aware (Windows / Unix)."""

from __future__ import annotations

import subprocess
import sys

from rich.console import Console
from rich.table import Table


def services_command(name_filter: str | None, limit: int) -> None:
    """Print services grouped by status (running / stopped).

    Platform-aware:
      - Windows: uses ``sc query``
      - Unix:    uses ``systemctl list-units`` or ``psutil`` fallback

    Args:
        name_filter: Optional substring filter (case-insensitive).
        limit: Maximum services to show.
    """
    console = Console()
    services: list[dict[str, str]] = []

    if sys.platform == "win32":
        services = _windows_services()
    else:
        services = _unix_services()

    if name_filter:
        services = [s for s in services if name_filter.lower() in s["name"].lower()]

    running = [s for s in services if s["status"] == "running"]
    stopped = [s for s in services if s["status"] != "running"]

    # Cap running+stopped separately then merge
    running = running[:limit]
    stopped = stopped[:limit]

    table = Table(title="Services", padding=(0, 1))
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="yellow")

    for s in running:
        table.add_row(s["name"], s["status"])
    for s in stopped:
        table.add_row(s["name"], s["status"])

    console.print(table)
    console.print(f"[dim]Running: {len(running)} shown | Stopped: {len(stopped)} shown[/dim]")


def _windows_services() -> list[dict[str, str]]:
    """Get Windows services via ``sc query``."""
    result: list[dict[str, str]] = []
    try:
        output = subprocess.check_output(
            ["sc", "query", "state=", "all"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return result

    current: dict[str, str] = {}
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("SERVICE_NAME:"):
            if current.get("name"):
                result.append(current)
            current = {"name": line.split(":", 1)[1].strip(), "status": "unknown"}
        elif line.startswith("STATE "):
            raw = line.split(":", 1)[-1].strip()
            # Parse numeric state: "4  RUNNING"
            parts = raw.split(None, 1)
            state_str = parts[-1].lower() if parts else ""
            if state_str in ("running",):
                current["status"] = "running"
            elif state_str in ("stopped", "stopped",):
                current["status"] = "stopped"
            else:
                current["status"] = state_str or "unknown"

    if current.get("name"):
        result.append(current)
    return result


def _unix_services() -> list[dict[str, str]]:
    """Get Unix services via systemctl or psutil fallback."""
    # Try systemctl first
    try:
        output = subprocess.check_output(
            ["systemctl", "list-units", "--type=service", "--no-legend", "--no-pager"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
        result: list[dict[str, str]] = []
        for line in output.splitlines():
            parts = line.split()
            if len(parts) >= 3:
                result.append({
                    "name": parts[0].replace(".service", ""),
                    "status": "running" if parts[3] == "running" else "stopped",
                })
        if result:
            return result
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass

    # Fallback: psutil process list (show processes that look like services/daemons)
    try:
        import psutil

        result = []
        for p in psutil.process_iter(["name", "status"]):
            try:
                info = p.info
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            name = info.get("name") or ""
            status_str = info.get("status", "")
            result.append({
                "name": name,
                "status": "running" if status_str.lower() in ("running", "sleeping") else status_str.lower() or "unknown",
            })
        return result
    except ImportError:
        return []
