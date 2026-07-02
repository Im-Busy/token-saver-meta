"""SQLite read-only access to CBM database + own SQLite for custom nodes."""
import sqlite3
import os
from pathlib import Path

def get_cbm_db_path() -> Path:
    """Get CBM database path from env or default."""
    env_path = os.environ.get("CBM_DB_PATH")
    if env_path:
        return Path(env_path)
    return Path.home() / ".cache" / "codebase-memory-mcp"

def open_cbm_db(readonly: bool = True) -> sqlite3.Connection:
    """Open CBM SQLite database. Read-only with WAL mode."""
    db_path = get_cbm_db_path()
    if not db_path.exists():
        raise FileNotFoundError(f"CBM database not found at {db_path}")
    uri = f"file:{db_path}?mode=ro" if readonly else str(db_path)
    conn = sqlite3.connect(uri, uri=readonly)
    conn.row_factory = sqlite3.Row
    return conn

def open_sidecar_db() -> sqlite3.Connection:
    """Open sidecar's own SQLite database for custom nodes."""
    db_path = Path.home() / ".token-saver-meta" / "cbm_sidecar.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    # Create custom tables if needed
    conn.execute("""
        CREATE TABLE IF NOT EXISTS custom_nodes (
            id INTEGER PRIMARY KEY,
            name TEXT,
            label TEXT,
            properties TEXT
        )
    """)
    conn.commit()
    return conn
