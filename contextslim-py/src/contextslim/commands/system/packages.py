"""`contextslim system packages` — installed packages list (platform-aware).

Windows: winget list → pip list.
Linux: dpkg -l → rpm -qa → pip list.
Extracts package name only (drops version).
"""

from __future__ import annotations

import subprocess
import sys
from typing import Iterable

from rich.console import Console

console = Console()


def _run_cmd(args: list[str], timeout: int = 30) -> str:
    """Run a command, return stdout or empty string on failure."""
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return ""


def _extract_names(raw: str, mode: str) -> list[str]:
    """Extract package names from raw command output.

    Args:
        raw: Raw stdout from a package manager.
        mode: One of ``'winget'``, ``'dpkg'``, ``'rpm'``, ``'pip'``.
    """
    names: set[str] = set()
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if mode == "winget":
            # winget list output: "Name  Id  Version  Available  Source"
            # Skip header lines
            if line.startswith("Name") or line.startswith("---"):
                continue
            parts = line.split(None, 1)
            if parts:
                names.add(parts[0])
        elif mode == "dpkg":
            # dpkg -l: "ii  pkgname  version  arch  description"
            if not line.startswith("ii  ") and not line.startswith("hi  "):
                continue
            parts = line.split(None, 3)
            if len(parts) >= 2:
                names.add(parts[1])
        elif mode == "rpm":
            # rpm -qa --qf "%{NAME}\\n"
            names.add(line)
        elif mode == "pip":
            # pip list: "pkgname   version"
            if line.startswith("Package") or line.startswith("---"):
                continue
            parts = line.split(None, 1)
            if parts:
                names.add(parts[0].lower())
    return sorted(names)


def packages_command(name_filter: str | None = None) -> None:
    """List installed packages, platform-aware.

    Args:
        name_filter: Filter by package name (case-insensitive substring).
    """
    names: list[str] = []

    if sys.platform == "win32":
        raw = _run_cmd(["winget", "list"], timeout=60)
        if raw and "Name" in raw:
            names = _extract_names(raw, "winget")
        else:
            # Fallback to pip
            raw = _run_cmd([sys.executable, "-m", "pip", "list"], timeout=30)
            if raw:
                names = _extract_names(raw, "pip")
    else:
        # Try dpkg first (Debian/Ubuntu)
        raw = _run_cmd(["dpkg", "-l"], timeout=30)
        if raw and "ii " in raw:
            names = _extract_names(raw, "dpkg")
        else:
            # Try rpm (RHEL/Fedora)
            raw = _run_cmd(["rpm", "-qa", "--qf", "%{NAME}\\n"], timeout=30)
            if raw:
                names = _extract_names(raw, "rpm")
            else:
                # Fallback to pip
                raw = _run_cmd([sys.executable, "-m", "pip", "list"], timeout=30)
                if raw:
                    names = _extract_names(raw, "pip")

    if not names:
        console.print("[dim]No packages found[/]")
        return

    # Filter
    if name_filter:
        nf = name_filter.lower()
        names = [n for n in names if nf in n.lower()]

    if not names:
        console.print(f"[dim]No packages matching '{name_filter}'[/]")
        return

    # Compact output — columns of names
    COLUMNS = 4
    max_width = max(len(n) for n in names) + 2
    console.print(f"[bold]{len(names)} package(s)[/]")
    for i in range(0, len(names), COLUMNS):
        row = names[i : i + COLUMNS]
        console.print("".join(n.ljust(max_width) for n in row))
