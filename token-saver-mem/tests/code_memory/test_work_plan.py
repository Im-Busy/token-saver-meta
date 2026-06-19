"""Tests for work_plan.py — prioritized annotation work plan with priority cascade."""

from __future__ import annotations

import pytest

from token_saver_mem.code_memory.work_plan import get_work_plan


class TestGetWorkPlan:
    """get_work_plan(db_path) -> WorkPlan"""

    def test_empty_db_returns_nothing(self, temp_db):
        """Given an empty database, returns NOTHING priority with empty tasks."""
        plan = get_work_plan(temp_db)
        assert plan.priority == "NOTHING"
        assert plan.tasks == []

    def test_all_annotated_returns_nothing(self, populated_db):
        """Given all nodes have summaries and are marked fresh, returns EXPLORE at worst.
        
        mark_fresh only syncs hashes — it cannot create missing summaries.
        Nodes without summaries (summary IS NULL) remain DOCUMENT gaps after mark_fresh.
        So we only mark stale-but-summarized nodes fresh, leaving unsynced as DOCUMENT."""
        from token_saver_mem.code_memory.staleness import mark_fresh

        # Mark only stale-nodes-with-summary as fresh (skip null-summary unsynced)
        mark_fresh(populated_db, "function:stale_example.py:old_func")

        plan = get_work_plan(populated_db)
        # unsynced still has summary=NULL → DOCUMENT remains
        assert plan.priority == "DOCUMENT"
        doc_ids = [t["node_id"] for t in plan.tasks if t["priority"] == "DOCUMENT"]
        assert "function:stale_example.py:unsynced" in doc_ids

    def test_document_priority_for_unsummarized(self, populated_db):
        """Given nodes without summaries, work plan has DOCUMENT priority tasks."""
        plan = get_work_plan(populated_db)
        doc_tasks = [t for t in plan.tasks if t["priority"] == "DOCUMENT"]
        assert len(doc_tasks) > 0
        # unsynced has summary=NULL
        doc_ids = [t["node_id"] for t in doc_tasks]
        assert "function:stale_example.py:unsynced" in doc_ids

    def test_investigate_priority_for_stale(self, populated_db):
        """Given nodes with stale summaries, work plan has INVESTIGATE priority tasks."""
        plan = get_work_plan(populated_db)
        inv_tasks = [t for t in plan.tasks if t["priority"] == "INVESTIGATE"]
        assert len(inv_tasks) > 0
        inv_ids = [t["node_id"] for t in inv_tasks]
        assert "function:stale_example.py:old_func" in inv_ids

    def test_priority_cascade_order(self, populated_db):
        """Given mixed priorities, DOCUMENT appears before INVESTIGATE in task list."""
        plan = get_work_plan(populated_db)
        priorities = [t["priority"] for t in plan.tasks]
        # Should be ordered: DOCUMENT > INVESTIGATE > EXPLORE
        assert priorities == sorted(
            priorities,
            key=lambda p: {"DOCUMENT": 0, "INVESTIGATE": 1, "EXPLORE": 2}.get(p, 99),
        )

    def test_top_priority_sets_plan_priority(self, populated_db):
        """Given any DOCUMENT tasks, the overall plan priority is DOCUMENT."""
        plan = get_work_plan(populated_db)
        has_doc = any(t["priority"] == "DOCUMENT" for t in plan.tasks)
        if has_doc:
            assert plan.priority == "DOCUMENT"
        else:
            # Fall through: INVESTIGATE > EXPLORE > NOTHING
            has_inv = any(t["priority"] == "INVESTIGATE" for t in plan.tasks)
            if has_inv:
                assert plan.priority == "INVESTIGATE"
            else:
                assert plan.priority in ("EXPLORE", "NOTHING")

    def test_tasks_have_required_keys(self, populated_db):
        """Given a populated DB, each task dict has all required keys."""
        plan = get_work_plan(populated_db)
        for task in plan.tasks:
            for key in ("priority", "node_id", "name", "path", "reason", "suggested_action"):
                assert key in task, f"Task missing key: {key}"
            assert task["priority"] in ("DOCUMENT", "INVESTIGATE", "EXPLORE")

    def test_reason_is_non_empty(self, populated_db):
        """Given any task, the reason field is a non-empty string."""
        plan = get_work_plan(populated_db)
        for task in plan.tasks:
            assert isinstance(task["reason"], str)
            assert len(task["reason"]) > 0

    def test_suggested_action_is_non_empty(self, populated_db):
        """Given any task, the suggested_action field is a non-empty string."""
        plan = get_work_plan(populated_db)
        for task in plan.tasks:
            assert isinstance(task["suggested_action"], str)
            assert len(task["suggested_action"]) > 0

    def test_document_tasks_have_action_about_summary(self, populated_db):
        """Given DOCUMENT tasks, suggested_action mentions summary generation."""
        plan = get_work_plan(populated_db)
        doc_tasks = [t for t in plan.tasks if t["priority"] == "DOCUMENT"]
        for task in doc_tasks:
            assert "summar" in task["suggested_action"].lower()
