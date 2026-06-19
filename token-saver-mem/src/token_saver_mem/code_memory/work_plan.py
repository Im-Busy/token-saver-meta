"""work_plan.py — prioritized annotation work plan for code_memory.

Produces a compact task list (< ~200 tokens) sorted by priority cascade:
  DOCUMENT > INVESTIGATE > EXPLORE > NOTHING
"""

from __future__ import annotations

from dataclasses import dataclass, field

from token_saver_mem.code_memory.db import get_connection


@dataclass
class WorkPlan:
    """Prioritized annotation work plan.

    Attributes:
        priority: Highest priority among tasks (DOCUMENT/INVESTIGATE/EXPLORE/NOTHING).
        tasks: Ordered list of task dicts. Each dict has:
          priority, node_id, name, path, reason, suggested_action.
    """

    priority: str = "NOTHING"
    tasks: list[dict] = field(default_factory=list)


_PRIORITY_ORDER: dict[str, int] = {
    "DOCUMENT": 0,
    "INVESTIGATE": 1,
    "EXPLORE": 2,
}

_MAX_TASKS = 10


def get_work_plan(db_path: str) -> WorkPlan:
    """Build a prioritized annotation work plan from the code_memory database.

    Priority cascade:
      DOCUMENT   — nodes with no summary at all (summary IS NULL)
      INVESTIGATE — nodes with stale summaries (summary_hash != content_hash)
      EXPLORE    — nodes with fresh summaries but low visit count
      NOTHING    — everything annotated and fresh, or empty DB

    Returns:
        WorkPlan with ordered tasks and overall priority.
    """
    tasks: list[dict] = []

    _collect_document_tasks(db_path, tasks)
    _collect_investigate_tasks(db_path, tasks)
    _collect_explore_tasks(db_path, tasks)

    # Determine overall plan priority
    if not tasks:
        return WorkPlan(priority="NOTHING")

    best_priority = min(tasks, key=lambda t: _PRIORITY_ORDER.get(t["priority"], 99))
    return WorkPlan(priority=best_priority["priority"], tasks=tasks)


def _collect_document_tasks(db_path: str, tasks: list[dict]) -> None:
    """Add DOCUMENT tasks for nodes with no summary."""
    if len(tasks) >= _MAX_TASKS:
        return

    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            """SELECT id, name, path, kind
               FROM code_nodes
               WHERE deleted_at IS NULL AND summary IS NULL
               ORDER BY updated_at DESC
               LIMIT ?""",
            (_MAX_TASKS - len(tasks),),
        ).fetchall()

        for r in rows:
            tasks.append({
                "priority": "DOCUMENT",
                "node_id": r["id"],
                "name": r["name"],
                "path": r["path"],
                "reason": f"no summary exists for {r['kind']} '{r['name']}'",
                "suggested_action": f"generate summary for {r['kind']} {r['name']} in {r['path']}",
            })
    finally:
        conn.close()


def _collect_investigate_tasks(db_path: str, tasks: list[dict]) -> None:
    """Add INVESTIGATE tasks for nodes with stale summaries."""
    if len(tasks) >= _MAX_TASKS:
        return

    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            """SELECT id, name, path, kind
               FROM code_nodes
               WHERE deleted_at IS NULL
                 AND summary IS NOT NULL
                 AND summary_hash IS NOT NULL
                 AND summary_hash != content_hash
               ORDER BY updated_at DESC
               LIMIT ?""",
            (_MAX_TASKS - len(tasks),),
        ).fetchall()

        for r in rows:
            tasks.append({
                "priority": "INVESTIGATE",
                "node_id": r["id"],
                "name": r["name"],
                "path": r["path"],
                "reason": f"stale summary for {r['kind']} '{r['name']}' (content changed)",
                "suggested_action": f"review and update summary for {r['kind']} {r['name']} in {r['path']}",
            })
    finally:
        conn.close()


def _collect_explore_tasks(db_path: str, tasks: list[dict]) -> None:
    """Add EXPLORE tasks for fresh nodes with low visit count.

    Uses LEFT JOIN with node_visits to find nodes visited the fewest times.
    """
    if len(tasks) >= _MAX_TASKS:
        return

    conn = get_connection(db_path)
    try:
        remaining = _MAX_TASKS - len(tasks)
        rows = conn.execute(
            """SELECT cn.id, cn.name, cn.path, cn.kind,
                      COALESCE(vc.visit_count, 0) AS visits
               FROM code_nodes cn
               LEFT JOIN (
                   SELECT node_id, COUNT(*) AS visit_count
                   FROM node_visits
                   GROUP BY node_id
               ) vc ON cn.id = vc.node_id
               WHERE cn.deleted_at IS NULL
                 AND cn.summary IS NOT NULL
               ORDER BY visits ASC, cn.updated_at DESC
               LIMIT ?""",
            (remaining,),
        ).fetchall()

        for r in rows:
            tasks.append({
                "priority": "EXPLORE",
                "node_id": r["id"],
                "name": r["name"],
                "path": r["path"],
                "reason": f"{r['kind']} '{r['name']}' has summary but low visits ({r['visits']})",
                "suggested_action": f"verify summary accuracy for {r['kind']} {r['name']} in {r['path']}",
            })
    finally:
        conn.close()
