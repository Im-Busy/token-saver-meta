"""`contextslim db dbquery` — execute SQL with truncated output."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from rich.console import Console

from contextslim.compressor.db import truncate_columns, limit_rows, format_table

console = Console()


def dbquery_command(sql_or_file: str, db_path: str | None = None) -> None:
    """Execute SQL query on SQLite DB, output truncated.

    Args:
        sql_or_file: SQL statement or path to ``.sql`` file.
        db_path: Path to SQLite database. Required.
    """
    if db_path is None:
        console.print("[red]Error:[/] --db <path> required")
        return

    db = Path(db_path)
    if not db.is_file():
        console.print(f"[red]Error:[/] database not found: '{db_path}'")
        return

    # Read SQL from file if sql_or_file looks like a .sql path
    sql = sql_or_file
    sql_path = Path(sql_or_file)
    if sql_path.suffix == ".sql" and sql_path.is_file():
        sql = sql_path.read_text(encoding="utf-8")

    try:
        conn = sqlite3.connect(str(db))
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as exc:
        console.print(f"[red]Error:[/] cannot open database: {exc}")
        return

    try:
        cur = conn.execute(sql)

        # Handle non-SELECT (INSERT, UPDATE, CREATE, etc.)
        if cur.description is None:
            rowcount = cur.rowcount
            console.print(f"[green]{rowcount} row(s) affected[/]")
            conn.commit()
            return

        headers = [d[0] for d in cur.description]
        rows: list[list[str]] = [[str(v) for v in row] for row in cur.fetchall()]

    except sqlite3.Error as exc:
        console.print(f"[red]Error:[/] {exc}")
        conn.close()
        return
    finally:
        conn.close()

    if not rows:
        console.print("[dim]0 rows returned[/]")
        return

    # Truncation pipeline
    rows = truncate_columns(rows, max_width=40)
    rows = limit_rows(rows, max_rows=10)

    output = format_table(headers, rows, max_rows=99, max_cols=20)
    console.print(output)
