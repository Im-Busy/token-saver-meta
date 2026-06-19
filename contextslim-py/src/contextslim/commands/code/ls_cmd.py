"""`contextslim code ls` — list directory, skip heavy/ignored dirs."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

from contextslim.analyzer.stack_detector import IGNORED_DIRS

if TYPE_CHECKING:
    from contextslim.config import Config

console = Console()


def ls_command(directory: str, config: Config) -> None:
    """List directory contents, hide heavy dirs.

    Skips entries whose name is in IGNORED_DIRS.
    Prints a summary line reporting how many entries were hidden.
    """
    _ = config  # kept for interface consistency
    root = Path(directory).resolve()

    if not root.is_dir():
        console.print(f"[red]Error:[/] '{directory}' is not a directory")
        return

    entries: list[Path] = []
    hidden_count = 0
    try:
        for child in sorted(root.iterdir()):
            if child.name in IGNORED_DIRS:
                hidden_count += 1
                continue
            entries.append(child)
    except PermissionError:
        console.print(f"[red]Error:[/] Permission denied reading '{root}'")
        return

    dirs = [e for e in entries if e.is_dir()]
    files = [e for e in entries if e.is_file()]

    # Print directories in cyan
    for d in dirs:
        console.print(f"[cyan]{d.name}/[/]")

    # Print files in white
    for f in files:
        console.print(f"[white]{f.name}[/]")

    # Summary
    hidden_str = f" ({hidden_count} heavy dirs hidden)" if hidden_count else ""
    console.print(
        f"\n[bold]{len(dirs)} dirs, {len(files)} files[/]{hidden_str}"
    )
