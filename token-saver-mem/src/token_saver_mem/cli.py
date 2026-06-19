"""Token Saver Mem CLI — Click group with serve, index, status commands."""

from __future__ import annotations

import click


@click.group(name="token-saver-mem")
@click.version_option(version="0.1.0", prog_name="token-saver-mem")
def cli() -> None:
    """Token Saver Mem — cross-session memory for token saving.

    Index codebases, serve MCP tools, and check memory status.
    """


@cli.command()
@click.option("--db", "db_path", default="./memory.db", help="Path to SQLite database file.")
@click.option("--write", is_flag=True, default=False, help="Enable write mode (allow mutations).")
@click.option("--port", type=int, default=8765, help="HTTP port for MCP server (future use).")
def serve(db_path: str, write: bool, port: int) -> None:
    """Start the MCP server (prints configuration; stdio loop deferred).

    Registers all tools in read-only mode by default.
    Use --write to enable mutating tools (store_understanding).
    """
    server_config = {
        "db_path": db_path,
        "read_only": not write,
        "port": port,
        "tools_registered": 8,
    }
    click.echo("MCP Server Configuration:")
    click.echo(f"  db_path: {db_path}")
    click.echo(f"  read_only: {not write}")
    click.echo(f"  port: {port}")
    click.echo(f"  write_mode: {write}")
    click.echo("  tools: context_pack, bootstrap_context, open_work, completion_check, "
               "unique_entities, store_understanding, list_entities, get_entity")
    click.echo("")
    click.echo("Server ready. (stdio transport deferred to integration)")


@cli.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--db", "db_path", default="./memory.db", help="Path to SQLite database file.")
def index(path: str, db_path: str) -> None:
    """Index a codebase into the memory database.

    Scans PATH recursively and indexes code nodes (files, functions, classes)
    into the SQLite database for later querying via MCP tools.
    """
    click.echo(f"Indexing codebase: {path}")
    click.echo(f"  database: {db_path}")
    click.echo("  Indexing... (stub — full indexer deferred)")
    click.echo("  Index complete.")


@cli.command()
@click.option("--db", "db_path", default="./memory.db", help="Path to SQLite database file.")
def status(db_path: str) -> None:
    """Show memory database status and statistics.

    Prints counts: nodes, edges, observations, sessions.
    """
    import os
    from pathlib import Path

    db_file = Path(db_path)
    click.echo("Memory Database Status:")
    click.echo(f"  path: {db_file.absolute()}")

    if db_file.exists():
        size_kb = db_file.stat().st_size / 1024
        click.echo(f"  size: {size_kb:.1f} KB")

        # Try to query actual stats
        try:
            import sqlite3
            conn = sqlite3.connect(f"file:{db_file}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row

            tables = [
                ("nodes", "SELECT COUNT(*) FROM nodes WHERE deleted_at IS NULL"),
                ("edges", "SELECT COUNT(*) FROM edges"),
                ("observations", "SELECT COUNT(*) FROM observations"),
                ("sessions", "SELECT COUNT(*) FROM sessions"),
            ]

            for label, query in tables:
                try:
                    count = conn.execute(query).fetchone()[0]
                    click.echo(f"  {label}: {count}")
                except sqlite3.OperationalError:
                    click.echo(f"  {label}: 0 (table not found)")

            conn.close()
        except Exception:
            click.echo("  (could not read stats — database may be uninitialized)")
    else:
        click.echo("  size: (does not exist)")
        click.echo("  nodes: 0")
        click.echo("  edges: 0")
        click.echo("  observations: 0")
        click.echo("  sessions: 0")
