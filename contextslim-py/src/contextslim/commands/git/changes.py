"""Compact git log — last N commits with changed-file counts."""

from __future__ import annotations

import os
import subprocess


def _git_env() -> dict[str, str]:
    """Return environment with GIT_DIR/WORK_TREE cleared to avoid parent-repo leakage."""
    env = os.environ.copy()
    env.pop("GIT_DIR", None)
    env.pop("GIT_WORK_TREE", None)
    return env


def _run_git_log(count: int) -> list[str]:
    """Run ``git log --oneline -n {count}``, return lines or [] on failure."""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", f"-n{count}"],
            capture_output=True, text=True, timeout=10, env=_git_env(),
        )
        return result.stdout.strip().splitlines() if result.stdout.strip() else []
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []


def _changed_file_count(commit_hash: str) -> int:
    """Count files changed in *commit_hash*."""
    try:
        result = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
            capture_output=True, text=True, timeout=10, env=_git_env(),
        )
        files = [line for line in result.stdout.splitlines() if line.strip()]
        return len(files)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return 0


def changes_command(count: int = 10) -> None:
    """Compact git log — last *count* commits with changed file counts."""
    lines = _run_git_log(count)
    if not lines:
        print("  [dim]No commits found.[/dim]")
        return

    for line in lines:
        # git log --oneline outputs: "<hash> <message>"
        parts = line.split(" ", 1)
        commit_hash = parts[0]
        message = parts[1] if len(parts) > 1 else commit_hash
        n_files = _changed_file_count(commit_hash)
        print(f"  {commit_hash}  {message}  ({n_files} files)")
