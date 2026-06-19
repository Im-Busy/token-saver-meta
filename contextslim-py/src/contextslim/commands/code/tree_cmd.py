"""`contextslim code tree` — directory tree with depth cap."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

from contextslim.analyzer.project_context import generate_mini_tree
from contextslim.analyzer.stack_detector import IGNORED_DIRS

if TYPE_CHECKING:
    from contextslim.config import Config

console = Console()


def tree_command(directory: str, max_depth: int, config: Config) -> None:
    """Directory tree with depth cap.

    Renders a compact tree skipping IGNORED_DIRS.
    Reports the count of hidden directories.
    """
    _ = config  # kept for interface consistency
    root = Path(directory).resolve()

    if not root.is_dir():
        console.print(f"[red]Error:[/] '{directory}' is not a directory")
        return

    # Count hidden dirs before generating the tree
    hidden_count = _count_hidden_dirs(root, max_depth)
    tree = generate_mini_tree(root, max_depth=max_depth)

    console.print(f"[bold underline]{root.name}/[/]")
    lines = tree.splitlines()
    if len(lines) > 1:
        for line in lines[1:]:
            console.print(line)
    else:
        console.print("  (empty)")

    if hidden_count:
        console.print(f"\n[bold]{hidden_count} heavy dirs hidden[/]")


def _count_hidden_dirs(root: Path, max_depth: int) -> int:
    """Count directories matching IGNORED_DIRS up to max_depth."""
    counter: list[int] = [0]
    _walk_count(root, depth=0, max_depth=max_depth, counter=counter)
    return counter[0]


def _walk_count(directory: Path, depth: int, max_depth: int, counter: list[int]) -> None:
    """Recursively count ignored dirs."""
    if depth >= max_depth:
        return
    try:
        for child in sorted(directory.iterdir()):
            if child.is_dir():
                if child.name in IGNORED_DIRS:
                    counter[0] += 1
                else:
                    _walk_count(child, depth + 1, max_depth, counter)
    except PermissionError:
        pass


