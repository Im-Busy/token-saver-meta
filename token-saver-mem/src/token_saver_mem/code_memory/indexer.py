"""indexer.py — directory walk, SHA-256, ast.parse, incremental indexing.

Ported from Loom's indexer/incremental.py + indexer/utils.py + indexer/walker.py.
Python-only v1 — no tree-sitter, no C extensions. Uses stdlib ast + ProcessPoolExecutor.
"""

from __future__ import annotations

import ast
import hashlib
import os
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count
from pathlib import Path
from typing import Any

from token_saver_mem.code_memory.auto_summary import _extract_class, _extract_function, _safe_parse
from token_saver_mem.code_memory.db import (
    get_all_fingerprints,
    get_connection,
    soft_delete_nodes,
    upsert_fingerprint,
    upsert_nodes,
)
from token_saver_mem.code_memory.models import ChangeReport, CodeNode

_SKIP_DIRS: frozenset[str] = frozenset({
    ".git", "__pycache__", ".venv", "venv", ".tox", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", "node_modules", "dist", "build",
    ".eggs", "*.egg-info",
})


def sha256_of_file(path: Path) -> str:
    """Compute SHA-256 hash of a file. Matches hashlib.sha256."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _walk_py_files(root: Path) -> list[Path]:
    """Walk a directory tree and return all .py files (absolute paths).

    Skips hidden dirs, virtual envs, cache dirs, and node_modules.
    """
    files: list[Path] = []
    stack: list[Path] = [root]

    while stack:
        cur = stack.pop()
        try:
            with os.scandir(cur) as it:
                for entry in it:
                    name = entry.name
                    if entry.is_dir(follow_symlinks=False):
                        if entry.is_symlink():
                            continue
                        if name in _SKIP_DIRS or name.startswith("."):
                            continue
                        stack.append(Path(entry.path))
                    elif entry.is_file(follow_symlinks=False):
                        if name.endswith(".py"):
                            files.append(Path(entry.path))
        except PermissionError:
            continue

    return files


def _parse_file_worker(file_path: str) -> dict[str, Any]:
    """Parse a single .py file into a list of code node dicts.

    Runs in a worker process (ProcessPoolExecutor target).
    Must be a module-level function for pickling.

    Returns:
        Dict with keys: path, nodes (list of node dicts), error (str or None).
    """
    path = Path(file_path)
    nodes: list[dict] = []

    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return {"path": file_path, "nodes": [], "error": str(exc)}

    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    tree = _safe_parse(content)

    if tree is None:
        # Syntax error — return empty nodes (file will still be fingerprinted)
        return {"path": file_path, "nodes": [], "error": "syntax_error"}

    posix_path = file_path.replace("\\", "/")

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            node_id = CodeNode.make_id("function", posix_path, node.name)
            source_lines = content.split("\n")
            fn_source = "\n".join(source_lines[node.lineno - 1: node.end_lineno]) if node.end_lineno else ""
            fn_hash = hashlib.sha256(fn_source.encode("utf-8")).hexdigest()
            nodes.append({
                "id": node_id,
                "kind": "function",
                "name": node.name,
                "path": posix_path,
                "start_line": node.lineno,
                "end_line": node.end_lineno,
                "content_hash": fn_hash,
                "summary": None,
                "summary_hash": None,
                "metadata": "{}",  # Will be enriched later
                "deleted_at": None,
            })
        elif isinstance(node, ast.AsyncFunctionDef):
            node_id = CodeNode.make_id("function", posix_path, node.name)
            source_lines = content.split("\n")
            fn_source = "\n".join(source_lines[node.lineno - 1: node.end_lineno]) if node.end_lineno else ""
            fn_hash = hashlib.sha256(fn_source.encode("utf-8")).hexdigest()
            nodes.append({
                "id": node_id,
                "kind": "function",
                "name": node.name,
                "path": posix_path,
                "start_line": node.lineno,
                "end_line": node.end_lineno,
                "content_hash": fn_hash,
                "summary": None,
                "summary_hash": None,
                "metadata": "{}",
                "deleted_at": None,
            })
        elif isinstance(node, ast.ClassDef):
            class_id = CodeNode.make_id("class", posix_path, node.name)
            source_lines = content.split("\n")
            class_source = "\n".join(source_lines[node.lineno - 1: node.end_lineno]) if node.end_lineno else ""
            class_hash = hashlib.sha256(class_source.encode("utf-8")).hexdigest()
            nodes.append({
                "id": class_id,
                "kind": "class",
                "name": node.name,
                "path": posix_path,
                "start_line": node.lineno,
                "end_line": node.end_lineno,
                "content_hash": class_hash,
                "summary": None,
                "summary_hash": None,
                "metadata": "{}",
                "deleted_at": None,
            })
            # Extract methods within class
            for member in node.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_id = CodeNode.make_id("method", posix_path, f"{node.name}.{member.name}")
                    ms_lines = content.split("\n")
                    ms_source = "\n".join(ms_lines[member.lineno - 1: member.end_lineno]) if member.end_lineno else ""
                    ms_hash = hashlib.sha256(ms_source.encode("utf-8")).hexdigest()
                    nodes.append({
                        "id": method_id,
                        "kind": "method",
                        "name": f"{node.name}.{member.name}",
                        "path": posix_path,
                        "start_line": member.lineno,
                        "end_line": member.end_lineno,
                        "content_hash": ms_hash,
                        "summary": None,
                        "summary_hash": None,
                        "metadata": "{}",
                        "deleted_at": None,
                    })

    return {"path": file_path, "nodes": nodes, "error": None}


def index_directory(path: str | Path, db_path: str) -> dict[str, int]:
    """Index all .py files in a directory into the code_memory database.

    Uses 3-tier change detection:
      1. Check stored fingerprint (mtime + SHA-256)
      2. If mtime changed, recompute SHA-256
      3. If SHA-256 changed, re-parse the file

    Parallel parsing via ProcessPoolExecutor for directories with >= 8 files.

    Args:
        path: Root directory to index.
        db_path: Path to the SQLite database.

    Returns:
        Dict with keys: files_found, files_indexed, files_unchanged,
        nodes_written, errors.
    """
    root = Path(path).resolve()
    py_files = _walk_py_files(root)

    result = {
        "files_found": len(py_files),
        "files_indexed": 0,
        "files_unchanged": 0,
        "nodes_written": 0,
        "errors": 0,
    }

    if not py_files:
        return result

    # Classify changes
    abs_paths = [f.as_posix() for f in py_files]
    report = classify_changes(abs_paths, db_path)
    result["files_unchanged"] = len(report.unchanged)

    # Files needing parse: added + modified
    files_to_parse = report.files_to_index
    result["files_indexed"] = len(files_to_parse)
    if report.deleted:
        conn = get_connection(db_path)
        try:
            for d in report.deleted:
                # Get path from the fingerprint
                soft_delete_nodes(conn, d)
            conn.commit()
        finally:
            conn.close()

    if not files_to_parse:
        return result

    # Parse files (parallel for >= 8 files, serial for fewer)
    if len(files_to_parse) >= 8:
        with ProcessPoolExecutor(max_workers=min(cpu_count() or 1, 8)) as pool:
            parsed_results = list(pool.map(_parse_file_worker, files_to_parse, chunksize=10))
    else:
        parsed_results = [_parse_file_worker(f) for f in files_to_parse]

    # Upsert nodes and fingerprints
    all_nodes: list[dict] = []
    conn = get_connection(db_path)
    try:
        for pr in parsed_results:
            fp = pr["path"]
            if pr["error"]:
                result["errors"] += 1
            else:
                all_nodes.extend(pr["nodes"])

            # Always upsert fingerprint (even for errors — prevents re-processing)
            try:
                fpath = Path(fp)
                content_sha = sha256_of_file(fpath)
                mtime_ns = fpath.stat().st_mtime_ns
                upsert_fingerprint(conn, fp, content_sha, mtime_ns)
            except (OSError, FileNotFoundError):
                result["errors"] += 1

        if all_nodes:
            upsert_nodes(conn, all_nodes)
            result["nodes_written"] = len(all_nodes)

        conn.commit()
    finally:
        conn.close()

    return result


def classify_changes(discovered_files: list[str], db_path: str) -> ChangeReport:
    """Classify which files are new, modified, unchanged, or deleted.

    Uses stored fingerprints for 3-tier detection:
      1. File not in DB → 'added'
      2. mtime matches → 'unchanged' (fast path)
      3. SHA-256 matches → 'unchanged' (mtime-only change)
      4. SHA-256 differs → 'modified' (full re-parse needed)
      5. File in DB but not on disk → 'deleted'

    Args:
        discovered_files: List of absolute file paths from walk.
        db_path: Path to the SQLite database.

    Returns:
        ChangeReport with categorized file lists.
    """
    conn = get_connection(db_path)
    try:
        stored = get_all_fingerprints(conn)
    finally:
        conn.close()

    report = ChangeReport()
    discovered_set = set(discovered_files)

    for path in discovered_files:
        try:
            stat_result = Path(path).stat()
        except FileNotFoundError:
            report.deleted.append(path)
            continue

        mtime_ns = stat_result.st_mtime_ns

        if path not in stored:
            report.added.append(path)
            continue

        stored_sha, stored_mtime = stored[path]

        if stored_mtime == mtime_ns:
            report.unchanged.append(path)
            continue

        try:
            content_sha = sha256_of_file(Path(path))
        except FileNotFoundError:
            report.deleted.append(path)
            continue

        if stored_sha == content_sha:
            # mtime changed but content didn't — update fingerprint but don't re-parse
            conn = get_connection(db_path)
            try:
                upsert_fingerprint(conn, path, content_sha, mtime_ns)
                conn.commit()
            finally:
                conn.close()
            report.unchanged.append(path)
            continue

        report.modified.append(path)

    # Files in DB but not in discovered set → deleted
    for stored_path in stored:
        if stored_path not in discovered_set:
            report.deleted.append(stored_path)

    return report
