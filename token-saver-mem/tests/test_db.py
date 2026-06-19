"""Test database creation, schema, FTS5, WAL, FK enforcement, and migration idempotency."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from token_saver_mem.store.db import get_db, init_db, SCHEMA_SQL


@pytest.fixture
def db_path() -> str:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        f.write(b"")
    return f.name


@pytest.fixture
def db(db_path: str) -> sqlite3.Connection:
    conn = get_db(db_path)
    init_db(conn)
    yield conn
    conn.close()
    Path(db_path).unlink(missing_ok=True)


def assert_table_exists(db: sqlite3.Connection, table_name: str) -> None:
    """Assert that a table (or virtual table) exists."""
    cur = db.execute(
        "SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name=?",
        (table_name,),
    )
    assert cur.fetchone() is not None, f"Table {table_name!r} not found"


def assert_index_exists(db: sqlite3.Connection, index_name: str) -> None:
    cur = db.execute("SELECT name FROM sqlite_master WHERE type='index' AND name=?", (index_name,))
    assert cur.fetchone() is not None, f"Index {index_name!r} not found"


def assert_trigger_exists(db: sqlite3.Connection, trigger_name: str) -> None:
    cur = db.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name=?", (trigger_name,))
    assert cur.fetchone() is not None, f"Trigger {trigger_name!r} not found"


class TestSchemaCreation:
    """Given: a fresh database. When: init_db() runs. Then: all tables exist."""

    REQUIRED_TABLES = [
        "nodes", "edges", "observations", "sessions",
        "node_visits", "pack_cache", "nodes_fts",
    ]

    def test_all_required_tables_exist(self, db: sqlite3.Connection) -> None:
        """Then: every required table should exist in sqlite_master."""
        for tbl in self.REQUIRED_TABLES:
            assert_table_exists(db, tbl)

    def test_schema_sql_is_nonempty(self) -> None:
        """Then: the SCHEMA_SQL string should be non-empty."""
        assert SCHEMA_SQL, "SCHEMA_SQL must not be empty"
        assert "CREATE TABLE" in SCHEMA_SQL

    def test_nodes_table_columns(self, db: sqlite3.Connection) -> None:
        """Then: nodes table has the expected columns."""
        cur = db.execute("PRAGMA table_info('nodes')")
        cols = {row[1] for row in cur.fetchall()}
        expected = {
            "id", "path", "name", "kind", "content_hash", "summary_hash",
            "summary", "metadata", "created_at", "updated_at",
        }
        assert expected.issubset(cols), f"Missing columns: {expected - cols}"

    def test_edges_table_columns(self, db: sqlite3.Connection) -> None:
        """Then: edges table has the expected columns."""
        cur = db.execute("PRAGMA table_info('edges')")
        cols = {row[1] for row in cur.fetchall()}
        expected = {"id", "from_id", "to_id", "kind"}
        assert expected.issubset(cols), f"Missing columns: {expected - cols}"

    def test_observations_table_columns(self, db: sqlite3.Connection) -> None:
        """Then: observations table has the expected columns."""
        cur = db.execute("PRAGMA table_info('observations')")
        cols = {row[1] for row in cur.fetchall()}
        expected = {
            "id", "entity_name", "obs_type", "content", "confidence",
            "session_id", "created_at",
        }
        assert expected.issubset(cols), f"Missing columns: {expected - cols}"

    def test_sessions_table_columns(self, db: sqlite3.Connection) -> None:
        """Then: sessions table has the expected columns."""
        cur = db.execute("PRAGMA table_info('sessions')")
        cols = {row[1] for row in cur.fetchall()}
        expected = {"id", "started_at", "ended_at", "model", "agent"}
        assert expected.issubset(cols), f"Missing columns: {expected - cols}"

    def test_node_visits_table_columns(self, db: sqlite3.Connection) -> None:
        """Then: node_visits table has the expected columns."""
        cur = db.execute("PRAGMA table_info('node_visits')")
        cols = {row[1] for row in cur.fetchall()}
        expected = {"id", "node_id", "session_id", "visited_at"}
        assert expected.issubset(cols), f"Missing columns: {expected - cols}"

    def test_pack_cache_table_columns(self, db: sqlite3.Connection) -> None:
        """Then: pack_cache table has the expected columns."""
        cur = db.execute("PRAGMA table_info('pack_cache')")
        cols = {row[1] for row in cur.fetchall()}
        expected = {"hash", "content", "created_at"}
        assert expected.issubset(cols), f"Missing columns: {expected - cols}"


class TestFTS5:
    """Given: FTS5 extension available. When: schema created. Then: FTS5 works."""

    def test_fts5_virtual_table_exists(self, db: sqlite3.Connection) -> None:
        """Then: nodes_fts virtual table exists."""
        assert_table_exists(db, "nodes_fts")

    def test_fts5_insert_trigger(self, db: sqlite3.Connection) -> None:
        """Then: inserting a node triggers FTS5 index update."""
        assert_trigger_exists(db, "nodes_ai")
        db.execute(
            "INSERT INTO nodes (path, name, kind, created_at, updated_at) "
            "VALUES ('/test.py', 'test', 'module', '2025-01-01', '2025-01-01')"
        )
        db.commit()
        cur = db.execute("SELECT name FROM nodes_fts WHERE nodes_fts MATCH ?", ("module",))
        rows = cur.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "test"

    def test_fts5_update_trigger(self, db: sqlite3.Connection) -> None:
        """Then: updating a node triggers FTS5 re-index."""
        assert_trigger_exists(db, "nodes_au")
        db.execute(
            "INSERT INTO nodes (path, name, kind, summary, created_at, updated_at) "
            "VALUES ('/a.py', 'alpha', 'module', 'old summary', '2025-01-01', '2025-01-01')"
        )
        db.commit()

        # Update kind and summary
        db.execute("UPDATE nodes SET kind='function', summary='new summary' WHERE path='/a.py'")
        db.commit()

        # Old content should not match
        cur = db.execute("SELECT name FROM nodes_fts WHERE nodes_fts MATCH ?", ("old",))
        assert len(cur.fetchall()) == 0, "Old summary should not match after update"

        # New content should match
        cur = db.execute("SELECT name FROM nodes_fts WHERE nodes_fts MATCH ?", ("new",))
        assert len(cur.fetchall()) == 1

    def test_fts5_delete_trigger(self, db: sqlite3.Connection) -> None:
        """Then: deleting a node removes it from FTS5 index."""
        assert_trigger_exists(db, "nodes_ad")
        db.execute(
            "INSERT INTO nodes (path, name, kind, created_at, updated_at) "
            "VALUES ('/del.py', 'deleteme', 'module', '2025-01-01', '2025-01-01')"
        )
        db.commit()
        db.execute("DELETE FROM nodes WHERE path='/del.py'")
        db.commit()
        cur = db.execute("SELECT name FROM nodes_fts WHERE nodes_fts MATCH ?", ("deleteme",))
        assert len(cur.fetchall()) == 0

    def test_fts5_match_on_name_kind_summary(self, db: sqlite3.Connection) -> None:
        """Then: FTS5 matches across name, kind, and summary columns."""
        db.execute(
            "INSERT INTO nodes (path, name, kind, summary, created_at, updated_at) "
            "VALUES ('/x.py', 'file_x', 'class', 'handles authentication tokens', '2025-01-01', '2025-01-01')"
        )
        db.commit()

        # Match on name (join nodes_fts back to nodes for full row data)
        cur = db.execute(
            "SELECT n.path FROM nodes n JOIN nodes_fts f ON n.id = f.rowid "
            "WHERE nodes_fts MATCH ?", ("file_x",)
        )
        assert len(cur.fetchall()) == 1

        # Match on kind
        cur = db.execute(
            "SELECT n.path FROM nodes n JOIN nodes_fts f ON n.id = f.rowid "
            "WHERE nodes_fts MATCH ?", ("class",)
        )
        assert len(cur.fetchall()) == 1

        # Match on summary
        cur = db.execute(
            "SELECT n.path FROM nodes n JOIN nodes_fts f ON n.id = f.rowid "
            "WHERE nodes_fts MATCH ?", ("authentication",)
        )
        assert len(cur.fetchall()) == 1


class TestForeignKeys:
    """Given: foreign keys enabled. When: violating FK constraint. Then: error."""

    def test_edges_from_id_fk(self, db: sqlite3.Connection) -> None:
        """Then: inserting an edge with non-existent from_id fails."""
        # Insert a valid node first
        db.execute(
            "INSERT INTO nodes (id, path, name, kind, created_at, updated_at) "
            "VALUES (1, '/n1.py', 'n1', 'module', '2025-01-01', '2025-01-01')"
        )
        db.commit()

        # Valid edge: from_id=1 exists, to_id=999 does not
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO edges (from_id, to_id, kind) VALUES (1, 999, 'calls')"
            )

    def test_edges_to_id_fk(self, db: sqlite3.Connection) -> None:
        """Then: inserting an edge with non-existent to_id fails."""
        db.execute(
            "INSERT INTO nodes (id, path, name, kind, created_at, updated_at) "
            "VALUES (2, '/n2.py', 'n2', 'module', '2025-01-01', '2025-01-01')"
        )
        db.commit()

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO edges (from_id, to_id, kind) VALUES (999, 2, 'calls')"
            )

    def test_node_visits_node_id_fk(self, db: sqlite3.Connection) -> None:
        """Then: inserting a visit with non-existent node_id fails."""
        db.execute(
            "INSERT INTO sessions (id, started_at) VALUES ('s1', '2025-01-01')"
        )
        db.commit()

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO node_visits (node_id, session_id, visited_at) "
                "VALUES (999, 's1', '2025-01-01')"
            )

    def test_node_visits_session_id_fk(self, db: sqlite3.Connection) -> None:
        """Then: inserting a visit with non-existent session_id fails."""
        db.execute(
            "INSERT INTO nodes (id, path, name, kind, created_at, updated_at) "
            "VALUES (3, '/n3.py', 'n3', 'module', '2025-01-01', '2025-01-01')"
        )
        db.commit()

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO node_visits (node_id, session_id, visited_at) "
                "VALUES (3, 'nonexistent', '2025-01-01')"
            )

    def test_observations_session_id_fk(self, db: sqlite3.Connection) -> None:
        """Then: inserting an observation with non-existent session_id fails."""
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO observations (entity_name, obs_type, content, confidence, session_id, created_at) "
                "VALUES ('e1', 'fact', 'some content', 0.8, 'nonexistent', '2025-01-01')"
            )


class TestWALMode:
    """Given: a fresh database. When: init_db() runs. Then: WAL mode is set."""

    def test_wal_mode_enabled(self, db: sqlite3.Connection) -> None:
        """Then: the journal_mode should be 'wal'."""
        cur = db.execute("PRAGMA journal_mode")
        mode = cur.fetchone()[0]
        assert mode.lower() == "wal", f"Expected WAL mode, got {mode!r}"

    def test_foreign_keys_enabled(self, db: sqlite3.Connection) -> None:
        """Then: foreign_keys pragma should be ON."""
        cur = db.execute("PRAGMA foreign_keys")
        val = cur.fetchone()[0]
        assert val == 1, f"Expected foreign_keys=1, got {val}"


class TestMigrationIdempotency:
    """Given: an already-initialized database. When: init_db() runs again. Then: no error."""

    def test_init_db_twice_does_not_crash(self, db_path: str) -> None:
        """Then: calling init_db() twice on the same file works."""
        conn1 = get_db(db_path)
        init_db(conn1)
        conn1.close()

        conn2 = get_db(db_path)
        init_db(conn2)  # Should not raise
        conn2.close()
        assert True  # No exception = pass

    def test_tables_persist_after_reinit(self, db_path: str) -> None:
        """Then: data survives re-initialization."""
        conn1 = get_db(db_path)
        init_db(conn1)
        conn1.execute(
            "INSERT INTO nodes (path, name, kind, created_at, updated_at) "
            "VALUES ('/p.py', 'persist', 'module', '2025-01-01', '2025-01-01')"
        )
        conn1.commit()
        conn1.close()

        conn2 = get_db(db_path)
        init_db(conn2)  # Re-init
        cur = conn2.execute("SELECT name FROM nodes WHERE path='/p.py'")
        row = cur.fetchone()
        assert row is not None
        assert row[0] == "persist"
        conn2.close()
