"""`contextslim db dbschema` — compact SQLite schema tree."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from rich.console import Console
from rich.tree import Tree

console = Console()


def dbschema_command(db_path: str, name_filter: str | None = None) -> None:
    """Show compact schema tree for SQLite database at *db_path*.

    Queries ``sqlite_master`` for tables, uses ``PRAGMA table_info``
    for column details, rendered as a Rich tree.
    """
    path = Path(db_path)
    if not path.is_file():
        console.print(f"[red]Error:[/] database not found: '{db_path}'")
        return

    try:
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as exc:
        console.print(f"[red]Error:[/] cannot open database: {exc}")
        return

    try:
        # Get tables
        rows = conn.execute(
            "SELECT name, type FROM sqlite_master "
            "WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%' "
            "ORDER BY type, name"
        ).fetchall()

        if name_filter:
            nf = name_filter.lower()
            rows = [r for r in rows if nf in r["name"].lower()]

        if not rows:
            console.print("[dim]No tables/views found[/]")
            return

        tree = Tree(f"[bold]{path.name}[/]")

        for row in rows:
            obj_name = row["name"]
            obj_type = row["type"]

            if obj_type == "view":
                node_label = f"[cyan]{obj_name}[/] [dim](view)[/]"
            else:
                node_label = f"[cyan]{obj_name}[/]"

            tbl_node = tree.add(node_label)

            if obj_type == "table":
                # Get columns via PRAGMA
                cols = conn.execute(f"PRAGMA table_info('{obj_name}')").fetchall()
                for col in cols:
                    col_name = col["name"]
                    col_type = col["type"] or "-"
                    pk = " [bold green]PK[/]" if col["pk"] else ""
                    notnull = " [dim]NOT NULL[/]" if col["notnull"] else ""
                    dflt = f" [dim]= {col['dflt_value']}[/]" if col["dflt_value"] is not None else ""
                    tbl_node.add(f"{col_name}: [yellow]{col_type}[/]{pk}{notnull}{dflt}")

                # Get indexes
                indexes = conn.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='index' AND tbl_name=? "
                    "AND name NOT LIKE 'sqlite_%'",
                    (obj_name,),
                ).fetchall()
                if indexes:
                    idx_node = tbl_node.add("[dim]indexes[/]")
                    for idx in indexes:
                        idx_node.add(f"[dim]{idx['name']}[/]")

    finally:
        conn.close()

    console.print(tree)
