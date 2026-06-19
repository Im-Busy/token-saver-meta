"""Session repository — create, close, get_delta."""

from __future__ import annotations

import sqlite3
import time
from typing import Any, Optional


class SessionRepo:
    """CRUD for the *sessions* table."""

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

    # ── create ───────────────────────────────────────────────────

    def create(
        self,
        session_id: str,
        *,
        model: Optional[str] = None,
        agent: Optional[str] = None,
    ) -> dict[str, Any]:
        """Start a new session. Raises IntegrityError if session_id exists."""
        now = self._now()
        self._db.execute(
            """INSERT INTO sessions (id, started_at, model, agent)
               VALUES (?,?,?,?)""",
            (session_id, now, model, agent),
        )
        self._db.commit()
        row = self._db.execute(
            "SELECT * FROM sessions WHERE id=?", (session_id,)
        ).fetchone()
        return self._row_to_dict(row)

    # ── close ────────────────────────────────────────────────────

    def close(self, session_id: str) -> Optional[dict[str, Any]]:
        """End a session by setting ended_at. Returns None if session not found."""
        existing = self._db.execute(
            "SELECT id FROM sessions WHERE id=?", (session_id,)
        ).fetchone()
        if existing is None:
            return None
        now = self._now()
        self._db.execute(
            "UPDATE sessions SET ended_at=? WHERE id=?",
            (now, session_id),
        )
        self._db.commit()
        row = self._db.execute(
            "SELECT * FROM sessions WHERE id=?", (session_id,)
        ).fetchone()
        return self._row_to_dict(row)

    # ── delta ────────────────────────────────────────────────────

    def get_delta(self, session_id: str, since_ts: str) -> dict[str, int]:
        """Return counts for observations in *session_id*.

        Returns: ``{"changed": N, "deleted": 0, "total": M}``

        *changed* counts observations created after *since_ts*.
        *deleted* is always 0 (observations are not soft-deleted).
        *total* is all observations in this session.
        """
        changed = self._db.execute(
            """SELECT COUNT(*) FROM observations
               WHERE session_id=? AND created_at > ?""",
            (session_id, since_ts),
        ).fetchone()[0]

        total = self._db.execute(
            "SELECT COUNT(*) FROM observations WHERE session_id=?",
            (session_id,),
        ).fetchone()[0]

        return {"changed": changed, "deleted": 0, "total": total}
