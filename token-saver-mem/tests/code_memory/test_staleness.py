"""Tests for staleness.py — summary_hash vs content_hash divergence detection."""

from __future__ import annotations

import hashlib

import pytest

from token_saver_mem.code_memory.db import get_connection
from token_saver_mem.code_memory.staleness import check_staleness, mark_fresh


class TestCheckStaleness:
    """check_staleness(db_path) -> list[dict]"""

    def test_detects_stale_nodes(self, populated_db):
        """Given a node where summary_hash != content_hash, it's detected."""
        stale_nodes = check_staleness(populated_db)
        assert len(stale_nodes) >= 1
        stale = stale_nodes[0]
        assert stale["summary_hash"] != stale["content_hash"]

    def test_returns_empty_for_fresh_db(self, temp_db):
        """Given an empty database, returns empty list."""
        assert check_staleness(temp_db) == []

    def test_includes_node_ids(self, populated_db):
        """Given stale nodes, returned dicts include id."""
        stale_nodes = check_staleness(populated_db)
        for node in stale_nodes:
            assert "id" in node
            assert "name" in node
            assert "path" in node
            assert "summary_hash" in node
            assert "content_hash" in node

    def test_nodes_with_null_summary_hash_are_stale(self, populated_db):
        """Given a node with summary_hash=None, it's considered stale."""
        stale_nodes = check_staleness(populated_db)
        ids = [n["id"] for n in stale_nodes]
        assert "function:stale_example.py:unsynced" in ids

    def test_does_not_flag_fresh_nodes(self, populated_db):
        """Given nodes with summary_hash == content_hash, they are not stale."""
        stale_nodes = check_staleness(populated_db)
        ids = [n["id"] for n in stale_nodes]
        assert "function:utils.py:add" not in ids


class TestMarkFresh:
    """mark_fresh(db_path, node_id) -> bool"""

    def test_marks_stale_node_fresh(self, populated_db):
        """Given a stale node, mark_fresh sets summary_hash = content_hash."""
        # Confirm it's stale first
        stale = check_staleness(populated_db)
        assert len(stale) > 0
        target_id = stale[0]["id"]

        result = mark_fresh(populated_db, target_id)
        assert result is True

        # Verify it's no longer stale
        conn = get_connection(populated_db)
        try:
            row = conn.execute(
                "SELECT summary_hash, content_hash FROM code_nodes WHERE id = ?",
                (target_id,),
            ).fetchone()
            assert row["summary_hash"] == row["content_hash"]
        finally:
            conn.close()

    def test_returns_false_for_nonexistent_node(self, temp_db):
        """Given a node ID that doesn't exist, returns False."""
        result = mark_fresh(temp_db, "function:nope.py:nope")
        assert result is False

    def test_marks_unsynced_node(self, populated_db):
        """Given a node with summary_hash=None, mark_fresh sets it."""
        result = mark_fresh(populated_db, "function:stale_example.py:unsynced")
        assert result is True

        conn = get_connection(populated_db)
        try:
            row = conn.execute(
                "SELECT summary_hash, content_hash FROM code_nodes WHERE id = ?",
                ("function:stale_example.py:unsynced",),
            ).fetchone()
            assert row["summary_hash"] == row["content_hash"]
            assert row["summary_hash"] is not None
        finally:
            conn.close()

    def test_idempotent(self, populated_db):
        """Given already-fresh node, mark_fresh is a no-op and returns True."""
        conn = get_connection(populated_db)
        try:
            row = conn.execute(
                "SELECT summary_hash, content_hash FROM code_nodes WHERE id = ?",
                ("function:utils.py:add",),
            ).fetchone()
            assert row["summary_hash"] == row["content_hash"]  # Already fresh
        finally:
            conn.close()

        result = mark_fresh(populated_db, "function:utils.py:add")
        assert result is True
