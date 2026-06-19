"""Node repository — upsert, query, FTS5 search, staleness."""

from __future__ import annotations

import sqlite3
import time
from typing import Any, Optional


class NodeRepo:
    """CRUD + FTS5 search for the *nodes* table."""

    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    # ── helpers ──────────────────────────────────────────────────

    @staticmethod
    def _now() -> str:
        # Microsecond precision — needed for conditional updated_at comparisons
        return time.strftime("%Y-%m-%dT%H:%M:%S.", time.gmtime()) + f"{int(time.time() * 1_000_000) % 1_000_000:06d}Z"

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        return dict(row)

    # ── upsert ───────────────────────────────────────────────────

    def upsert(
        self,
        *,
        path: str,
        name: str,
        kind: str,
        content_hash: Optional[str] = None,
        summary_hash: Optional[str] = None,
        summary: Optional[str] = None,
        metadata: str = "{}",
    ) -> dict[str, Any]:
        """Insert or update a node keyed by *path*.

        updated_at is bumped only when *content_hash* differs from current value.
        """
        existing = self._db.execute(
            "SELECT id, content_hash, updated_at FROM nodes WHERE path=?",
            (path,),
        ).fetchone()

        if existing is None:
            # Insert
            now = self._now()
            cur = self._db.execute(
                """INSERT INTO nodes (path, name, kind, content_hash,
                   summary_hash, summary, metadata, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (path, name, kind, content_hash, summary_hash, summary, metadata, now, now),
            )
            self._db.commit()
            return self.get(cur.lastrowid)  # type: ignore[return-value]

        # Update existing — conditional updated_at bump
        eid = existing["id"]
        now = self._now()
        content_changed = existing["content_hash"] != content_hash
        updated_at = now if content_changed else existing["updated_at"]

        self._db.execute(
            """UPDATE nodes SET name=?, kind=?, content_hash=?,
               summary_hash=?, summary=?, metadata=?, updated_at=?
               WHERE id=?""",
            (name, kind, content_hash, summary_hash, summary, metadata, updated_at, eid),
        )
        self._db.commit()
        return self.get(eid)  # type: ignore[return-value]

    def bulk_upsert(self, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Upsert a batch of nodes. Each dict must have 'path', 'name', 'kind'."""
        results: list[dict[str, Any]] = []
        for node in nodes:
            result = self.upsert(
                path=node["path"],
                name=node["name"],
                kind=node["kind"],
                content_hash=node.get("content_hash"),
                summary_hash=node.get("summary_hash"),
                summary=node.get("summary"),
                metadata=node.get("metadata", "{}"),
            )
            results.append(result)
        return results

    # ── query ────────────────────────────────────────────────────

    def get(self, node_id: int) -> Optional[dict[str, Any]]:
        """Get a node by id. Returns None if not found."""
        row = self._db.execute("SELECT * FROM nodes WHERE id=?", (node_id,)).fetchone()
        return self._row_to_dict(row) if row else None

    def get_by_path(self, path: str) -> Optional[dict[str, Any]]:
        """Get a node by path. Returns None if not found."""
        row = self._db.execute("SELECT * FROM nodes WHERE path=?", (path,)).fetchone()
        return self._row_to_dict(row) if row else None

    # ── FTS5 search ──────────────────────────────────────────────

    def search_fts(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        """Full-text search across name, kind, and summary.

        Joins nodes_fts back to nodes for full row data.
        """
        rows = self._db.execute(
            """SELECT n.* FROM nodes n
               JOIN nodes_fts f ON n.id = f.rowid
               WHERE nodes_fts MATCH ?
               ORDER BY rank
               LIMIT ?""",
            (query, limit),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    # ── staleness ────────────────────────────────────────────────

    def mark_stale(self, node_id: int) -> None:
        """Bump updated_at to mark a node as stale (forces re-index)."""
        self._db.execute(
            "UPDATE nodes SET updated_at=? WHERE id=?",
            (self._now(), node_id),
        )
        self._db.commit()
