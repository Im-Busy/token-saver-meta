"""`contextslim search grep` — search files, skip heavy dirs, cap results."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

from contextslim.analyzer.stack_detector import IGNORED_DIRS

if TYPE_CHECKING:
    from contextslim.config import Config

BINARY_EXTENSIONS: set[str] = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf",
    ".zip", ".tar", ".gz", ".tgz", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib",
    ".pyc", ".pyo", ".o", ".a", ".obj",
    ".mp3", ".mp4", ".mov", ".avi", ".mkv", ".webm",
    ".ttf", ".woff", ".woff2", ".eot", ".otf",
    ".class", ".jar", ".war",
    ".db", ".sqlite", ".sqlite3",
    ".bin", ".dat", ".pkl", ".pickle",
}

console = Console()


def grep_command(query: str, directory: str, config: Config) -> None:
    """Search files for *query*, skipping heavy dirs and binary files.

    Capped per file (``grep_matches_per_file``) and globally
    (``grep_max_total``).  Results are grouped by file with line numbers.
    """
    root = Path(directory).resolve()
    if not root.is_dir():
        console.print(f"[red]Error:[/] '{directory}' is not a directory")
        return

    try:
        pattern = re.compile(re.escape(query), re.IGNORECASE)
    except re.error:
        console.print(f"[red]Error:[/] invalid regex in query '{query}'")
        return

    per_file_cap = config.limits.grep_matches_per_file
    total_cap = config.limits.grep_max_total
    max_width = config.limits.max_line_width

    # Collect results: dict[file_path, list[(line_no, line_text)]]
    results: dict[Path, list[tuple[int, str]]] = {}
    total_matches = 0
    skipped_count = 0

    for file_path in _walk_files(root):
        if total_matches >= total_cap:
            skipped_count += 1
            continue

        file_matches: list[tuple[int, str]] = []
        try:
            with file_path.open(encoding="utf-8", errors="replace") as fh:
                for lineno, line in enumerate(fh, start=1):
                    if pattern.search(line):
                        stripped = line.rstrip("\n\r")
                        if len(stripped) > max_width:
                            stripped = stripped[:max_width] + "..."
                        file_matches.append((lineno, stripped))
                        if len(file_matches) >= per_file_cap:
                            break
        except (OSError, UnicodeDecodeError):
            continue

        if file_matches:
            rel = _relpath(file_path, root)
            results[Path(rel)] = file_matches
            total_matches += len(file_matches)

    # Rich output
    for file_key, matches in results.items():
        console.print(f"\n[bold cyan]{file_key}[/]")
        for lineno, line_text in matches:
            console.print(f"  [dim]{lineno:>5}[/]  {line_text}")

    if not results:
        console.print(f"[yellow]No matches found for '{query}'[/]")
    else:
        hidden = ""
        if total_matches >= total_cap:
            hidden = f" (results capped, {skipped_count} files skipped)"
        console.print(
            f"\n[bold]{total_matches} matches across {len(results)} file(s)[/]{hidden}"
        )


def _walk_files(root: Path):
    """Yield text-file paths under *root*, skipping IGNORED_DIRS and binary ext."""
    try:
        for child in sorted(root.iterdir()):
            if child.is_dir():
                if child.name not in IGNORED_DIRS and not child.name.startswith("."):
                    yield from _walk_files(child)
            elif child.is_file():
                if child.suffix.lower() not in BINARY_EXTENSIONS:
                    yield child
    except PermissionError:
        pass


def _relpath(file_path: Path, root: Path) -> str:
    """Return a relative path string using forward slashes."""
    try:
        return file_path.relative_to(root).as_posix()
    except ValueError:
        return file_path.as_posix()
