"""`contextslim db dbsample` — SELECT * LIMIT N from a table."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from rich.console import Console

from contextslim.compressor.db import truncate_columns, limit_rows, format_table

console = Console()


def dbsample_command(table: str, db_path: str | None = None) -> None:
    """Sample rows from *table* in SQLite database.

    Args:
        table: Table name.
        db_path: Path to SQLite database. Required.
    """
    if db_path is None:
        console.print("[red]Error:[/] --db <path> required")
        return

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
        # Check table exists
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        if not exists:
            console.print(f"[red]Error:[/] table '{table}' not found")
            conn.close()
            return

        cur = conn.execute(f"SELECT * FROM [{table}] LIMIT 5")
        headers = [d[0] for d in cur.description]
        rows: list[list[str]] = [[str(v) for v in row] for row in cur.fetchall()]

    except sqlite3.Error as exc:
        console.print(f"[red]Error:[/] {exc}")
        conn.close()
        return
    finally:
        conn.close()

    if not rows:
        console.print(f"[dim]Table '{table}' is empty[/]")
        return

    rows = truncate_columns(rows, max_width=40)
    output = format_table(headers, rows, max_rows=5, max_cols=20)
    console.print(output)
