"""Tests for contextslim.commands.git.changes."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from contextslim.commands.git.changes import _run_git_log


def _git_env() -> dict[str, str]:
    """Return environment with GIT_DIR/WORK_TREE cleared to avoid parent-repo leakage."""
    env = os.environ.copy()
    env.pop("GIT_DIR", None)
    env.pop("GIT_WORK_TREE", None)
    return env


def _init_git_repo(directory: Path) -> None:
    """Initialize a git repo in *directory* with one commit."""
    subprocess.run(
        ["git", "init"], cwd=str(directory),
        capture_output=True, timeout=10, env=_git_env(),
    )
    (directory / "README.md").write_text("# test\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "."], cwd=str(directory),
        capture_output=True, timeout=10, env=_git_env(),
    )
    subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@test.com",
         "commit", "-m", "initial commit"],
        cwd=str(directory), capture_output=True, timeout=10, env=_git_env(),
    )


class TestRunGitLog:
    def test_non_git_directory(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            lines = _run_git_log(10)
            assert isinstance(lines, list)


class TestRunGitLogIntegration:
    def test_git_log_in_repo(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _init_git_repo(root)
            saved = os.getcwd()
            try:
                os.chdir(str(root))
                lines = _run_git_log(10)
            finally:
                os.chdir(saved)
            assert len(lines) >= 1
            assert "initial commit" in lines[0]

    def test_count_limits(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _init_git_repo(root)
            # Add more commits
            for i in range(3):
                (root / f"file{i}.txt").write_text(f"content {i}\n", encoding="utf-8")
                subprocess.run(
                    ["git", "add", "."], cwd=str(root),
                    capture_output=True, timeout=10, env=_git_env(),
                )
                subprocess.run(
                    ["git", "-c", "user.name=test", "-c", "user.email=test@test.com",
                     "commit", "-m", f"commit {i}"],
                    cwd=str(root), capture_output=True, timeout=10, env=_git_env(),
                )
            saved = os.getcwd()
            try:
                os.chdir(str(root))
                lines = _run_git_log(2)
            finally:
                os.chdir(saved)
            assert len(lines) == 2
