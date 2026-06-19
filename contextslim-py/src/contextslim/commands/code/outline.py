"""Recursive signature extraction from all source files."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.tree import Tree as RichTree

from contextslim.analyzer.stack_detector import IGNORED_DIRS
from contextslim.compressor.code import extract_signatures
from contextslim.config import Config

console = Console(highlight=False)

CODE_EXTENSIONS: set[str] = {
    ".py", ".ts", ".tsx", ".js", ".jsx",
    ".go", ".rs", ".java", ".rb", ".php",
    ".cs", ".kt", ".swift", ".dart",
}


def _collect_source_files(root: Path) -> list[Path]:
    """Walk *root*, skip ignored dirs, return matching source files."""
    result: list[Path] = []
    for entry in sorted(root.rglob("*")):
        if any(ign in entry.parts for ign in IGNORED_DIRS):
            continue
        if entry.is_file() and entry.suffix.lower() in CODE_EXTENSIONS:
            result.append(entry)
    return result


def outline_command(directory: str, config: Config) -> None:
    """Walk project, extract signatures from every source file, display as tree."""
    project_dir = Path(directory).resolve()
    cap = config.limits.outline_max_sigs_per_file

    files = _collect_source_files(project_dir)
    if not files:
        console.print("[dim]No source files found.[/]")
        return

    root_tree = RichTree(f"[bold]{project_dir.name}[/]")

    for file_path in files:
        rel = file_path.relative_to(project_dir)
        # Build parent chain in the RichTree
        parts = rel.parts
        current = root_tree
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                # Leaf — the file itself; read + extract signatures
                try:
                    lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
                except OSError:
                    current.add(f"[red]{part}[/] (read error)")
                    continue
                sigs = extract_signatures(lines)
                if cap > 0:
                    sigs = sigs[:cap]
                file_node = current.add(f"[cyan]{part}[/]")
                if sigs:
                    for sig in sigs:
                        file_node.add(sig.rstrip()[:120])
                else:
                    file_node.add("[dim](no signatures)[/]")
            else:
                # Intermediate directory — walk or reuse existing branch
                existing = next((c for c in current.children if c.label == part), None)
                if existing is None:
                    current = current.add(part)
                else:
                    current = existing

    console.print(root_tree)
