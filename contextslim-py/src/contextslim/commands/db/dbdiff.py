"""`contextslim db dbdiff` — compare two SQLite database schemas using difflib."""

from __future__ import annotations

import difflib
import sqlite3
from pathlib import Path

from rich.console import Console

console = Console()


def _get_schema_lines(db_path: str) -> list[str]:
    """Extract schema from SQLite DB as sorted lines of DDL."""
    try:
        conn = sqlite3.connect(db_path)
        rows = conn.execute(
            "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type, name"
        ).fetchall()
        conn.close()

        lines: list[str] = []
        for (sql,) in rows:
            for line in sql.splitlines():
                stripped = line.strip()
                if stripped:
                    lines.append(stripped)
        return lines
    except sqlite3.Error:
        return []


def dbdiff_command(schema1: str, schema2: str) -> None:
    """Compare schemas of two SQLite databases.

    Args:
        schema1: Path to first SQLite database.
        schema2: Path to second SQLite database.
    """
    p1 = Path(schema1)
    p2 = Path(schema2)

    if not p1.is_file():
        console.print(f"[red]Error:[/] file not found: '{schema1}'")
        return
    if not p2.is_file():
        console.print(f"[red]Error:[/] file not found: '{schema2}'")
        return

    lines1 = _get_schema_lines(str(p1))
    lines2 = _get_schema_lines(str(p2))

    if not lines1 and not lines2:
        console.print("[dim]Both databases have no schema[/]")
        return

    diff = list(
        difflib.unified_diff(
            lines1,
            lines2,
            fromfile=p1.name,
            tofile=p2.name,
            lineterm="",
        )
    )

    if not diff:
        console.print(f"[green]Schemas are identical:[/] {p1.name} == {p2.name}")
        return

    for line in diff:
        if line.startswith("---") or line.startswith("+++"):
            console.print(f"[bold]{line}[/]")
        elif line.startswith("@@"):
            console.print(f"[cyan]{line}[/]")
        elif line.startswith("+"):
            console.print(f"[green]{line}[/]")
        elif line.startswith("-"):
            console.print(f"[red]{line}[/]")
        else:
            console.print(f"  {line}")
