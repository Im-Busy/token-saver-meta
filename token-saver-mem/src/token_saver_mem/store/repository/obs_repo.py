"""Observation repository — add, query by entity or session."""

from __future__ import annotations

import sqlite3
import time
from typing import Any, Optional


class ObsRepo:
    """CRUD for the *observations* table."""

    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    # ── helpers ──────────────────────────────────────────────────

    @staticmethod
    def _now() -> str:
        # Microsecond precision
        return time.strftime("%Y-%m-%dT%H:%M:%S.", time.gmtime()) + f"{int(time.time() * 1_000_000) % 1_000_000:06d}Z"

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        return dict(row)

    # ── add ──────────────────────────────────────────────────────

    def add(
        self,
        *,
        entity_name: str,
        obs_type: str,
        content: str,
        confidence: float = 0.5,
        session_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Insert a new observation. Returns the created row as dict."""
        now = self._now()
        cur = self._db.execute(
            """INSERT INTO observations (entity_name, obs_type, content,
               confidence, session_id, created_at)
               VALUES (?,?,?,?,?,?)""",
            (entity_name, obs_type, content, confidence, session_id, now),
        )
        self._db.commit()
        row = self._db.execute(
            "SELECT * FROM observations WHERE id=?", (cur.lastrowid,)
        ).fetchone()
        return self._row_to_dict(row)

    # ── query ────────────────────────────────────────────────────

    def get_by_entity(self, entity_name: str) -> list[dict[str, Any]]:
        """Get all observations for a given entity, newest first."""
        rows = self._db.execute(
            "SELECT * FROM observations WHERE entity_name=? ORDER BY created_at DESC",
            (entity_name,),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_by_session(self, session_id: str) -> list[dict[str, Any]]:
        """Get all observations linked to a specific session, newest first."""
        rows = self._db.execute(
            "SELECT * FROM observations WHERE session_id=? ORDER BY created_at DESC",
            (session_id,),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]
