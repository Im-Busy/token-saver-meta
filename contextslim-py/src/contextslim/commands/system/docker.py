"""`contextslim system docker` — containers + images overview.

Graceful when Docker is not installed.
"""

from __future__ import annotations

import subprocess
import sys

from rich.console import Console
from rich.table import Table

console = Console()


def _docker_available() -> bool:
    """Check if ``docker`` CLI is on PATH."""
    try:
        subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            timeout=5,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _run_docker(args: list[str]) -> str:
    """Run a docker command, return stdout or empty string on failure."""
    try:
        result = subprocess.run(
            ["docker", *args],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        return ""


def docker_command(name_filter: str | None = None) -> None:
    """Show running Docker containers and images.

    Requires Docker CLI on PATH.  Filters by *name_filter* (container
    or image name, case-insensitive).
    """
    if not _docker_available():
        console.print("[dim]Docker not available[/]")
        return

    # ── Containers ────────────────────────────────────────────
    containers_raw = _run_docker([
        "ps",
        "--format", "{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}",
    ])

    container_rows: list[list[str]] = []
    if containers_raw:
        for line in containers_raw.split("\n"):
            parts = line.split("\t")
            if len(parts) >= 3:
                container_rows.append(parts)

    if name_filter:
        nf = name_filter.lower()
        container_rows = [
            r for r in container_rows
            if nf in r[0].lower() or nf in r[1].lower()
        ]

    console.print(f"\n[bold]Containers ({len(container_rows)})[/]")
    if container_rows:
        table = Table(show_header=True, header_style="bold")
        table.add_column("Name", style="cyan", max_width=30)
        table.add_column("Image", style="yellow", max_width=30)
        table.add_column("Status", style="green")
        table.add_column("Ports", style="white", max_width=40)
        for row in container_rows[:20]:
            table.add_row(*row)
        console.print(table)
        if len(container_rows) > 20:
            console.print(f"[dim]... and {len(container_rows) - 20} more[/]")
    else:
        console.print("  [dim]no running containers[/]")

    # ── Images ─────────────────────────────────────────────────
    images_raw = _run_docker([
        "images",
        "--format", "{{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}",
    ])

    image_rows: list[list[str]] = []
    if images_raw:
        for line in images_raw.split("\n"):
            parts = line.split("\t")
            if len(parts) >= 2:
                # Shorten the CreatedAt to just the date part
                if len(parts) >= 4:
                    parts[3] = parts[3].split(" ")[0]  # date only
                image_rows.append(parts)

    if name_filter:
        nf = name_filter.lower()
        image_rows = [
            r for r in image_rows
            if nf in r[0].lower() or (len(r) > 1 and nf in r[1].lower())
        ]

    console.print(f"\n[bold]Images ({len(image_rows)})[/]")
    if image_rows:
        table = Table(show_header=True, header_style="bold")
        table.add_column("Repository", style="cyan", max_width=30)
        table.add_column("Tag", style="yellow")
        table.add_column("Size", style="green")
        table.add_column("Created", style="white")
        for row in image_rows[:20]:
            # Ensure 4 columns
            while len(row) < 4:
                row.append("-")
            table.add_row(*row[:4])
        console.print(table)
        if len(image_rows) > 20:
            console.print(f"[dim]... and {len(image_rows) - 20} more[/]")
    else:
        console.print("  [dim]no images[/]")
