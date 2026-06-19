"""`contextslim db dbstats` — table row counts and index counts."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()


def dbstats_command(db_path: str, name_filter: str | None = None) -> None:
    """Show row counts and index counts for tables in SQLite DB.

    Args:
        db_path: Path to SQLite database.
        name_filter: Filter by table name (case-insensitive).
    """
    db = Path(db_path)
    if not db.is_file():
        console.print(f"[red]Error:[/] database not found: '{db_path}'")
        return

    try:
        conn = sqlite3.connect(str(db))
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as exc:
        console.print(f"[red]Error:[/] cannot open database: {exc}")
        return

    try:
        tables = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        ).fetchall()

        if name_filter:
            nf = name_filter.lower()
            tables = [t for t in tables if nf in t["name"].lower()]

        if not tables:
            console.print("[dim]No tables found[/]")
            return

        table_data: list[list[str]] = []
        total_rows = 0

        for tbl in tables:
            tbl_name = tbl["name"]
            row_count = conn.execute(f"SELECT COUNT(*) FROM [{tbl_name}]").fetchone()[0]
            total_rows += row_count

            idx_count = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master "
                "WHERE type='index' AND tbl_name=? AND name NOT LIKE 'sqlite_%'",
                (tbl_name,),
            ).fetchone()[0]

            table_data.append([tbl_name, str(row_count), str(idx_count)])

    finally:
        conn.close()

    tbl = Table(title=f"Database Stats: {db.name}", show_header=True, header_style="bold")
    tbl.add_column("Table", style="cyan")
    tbl.add_column("Rows", style="yellow", justify="right")
    tbl.add_column("Indexes", style="green", justify="right")

    for row in table_data:
        tbl.add_row(*row)

    console.print(tbl)
    console.print(f"[dim]{len(table_data)} table(s), {total_rows} total row(s)[/]")
