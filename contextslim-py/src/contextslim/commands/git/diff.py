"""Compact git diff or file diff — filtered of heavy dirs and lockfiles."""

from __future__ import annotations

import difflib
import subprocess
import sys
from pathlib import Path

from contextslim.compressor.text import strip_blanks

_DIFF_MAX_LINES = 200

# Skip patterns for git diff (paths to exclude).
_FILTER_PATHS: list[str] = [
    ":!package-lock.json", ":!yarn.lock", ":!pnpm-lock.yaml",
    ":!Cargo.lock", ":!go.sum", ":!uv.lock",
    ":!*.min.js", ":!*.min.css",
    ":!node_modules/**", ":!dist/**", ":!build/**", ":!.next/**",
    ":!venv/**", ":!.venv/**", ":!__pycache__/**",
    ":!target/**", ":!vendor/**",
]


def _run_git_diff(args: list[str]) -> str:
    """Run ``git diff`` with *args* and return stdout (empty string on failure)."""
    try:
        result = subprocess.run(
            ["git", "diff"] + args,
            capture_output=True, text=True, timeout=30,
        )
        return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return ""


def _git_diff_head() -> str:
    """git diff HEAD, excluding lockfiles and heavy dirs."""
    return _run_git_diff(["HEAD"] + _FILTER_PATHS)


def _git_diff_target(target: str) -> str:
    """git diff {target}, excluding lockfiles and heavy dirs."""
    return _run_git_diff([target] + _FILTER_PATHS)


def _file_diff(file1: str, file2: str) -> str:
    """Unified diff of two files."""
    path1 = Path(file1)
    path2 = Path(file2)
    try:
        a_lines = path1.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        b_lines = path2.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    except OSError as exc:
        return f"Error reading files: {exc}"
    diff = difflib.unified_diff(
        a_lines, b_lines,
        fromfile=str(path1), tofile=str(path2),
    )
    return "".join(diff)


def _cap_output(text: str, max_lines: int) -> str:
    """Truncate output to *max_lines*, inserting a marker."""
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    head = max_lines // 2
    tail = max_lines - head - 1
    return "\n".join(
        lines[:head]
        + [f"… [truncated {len(lines) - head - tail} lines] …"]
        + lines[-tail:]
    )


def diff_command(target: str | None = None, target2: str | None = None) -> None:
    """Compact git diff or file diff.

    - No args: ``git diff HEAD`` (filtered of lockfiles / heavy dirs).
    - One arg: ``git diff {target}`` (filtered).
    - Two args: unified diff of two files.
    """
    if target is not None and target2 is not None:
        output = _file_diff(target, target2)
    elif target is not None:
        output = _git_diff_target(target)
    else:
        output = _git_diff_head()

    if not output or not output.strip():
        print("  [dim]No changes found.[/dim]" if sys.stdout.isatty() else "  No changes found.")
        return

    filtered, _ = strip_blanks(output.splitlines())
    text = "\n".join(filtered)
    text = _cap_output(text, _DIFF_MAX_LINES)
    print(text)
