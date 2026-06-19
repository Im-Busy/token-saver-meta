"""~300-token project summary command (stack, entry points, tree)."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from contextslim.analyzer.project_context import detect_entry_points, generate_mini_tree
from contextslim.analyzer.stack_detector import detect_stack

console = Console(highlight=False)


def brief_command(directory: str) -> None:
    """Emit a ~300-token project summary: stack, entry points, tree."""
    project_dir = Path(directory).resolve()

    stack = detect_stack(project_dir)
    if stack is None:
        console.print(Panel("No project stack detected.", title="Project Brief"))
        return

    # Build compact body as Rich Text
    body = Text()
    body.append(f"Language:  {stack.language}\n")
    if stack.has_typescript:
        body.append("TypeScript: yes\n")
    if stack.frameworks:
        body.append(f"Frameworks: {', '.join(stack.frameworks)}\n")

    # Entry points
    entries = detect_entry_points(project_dir, stack)
    body.append(f"Entry:     {', '.join(entries) if entries else '(none)'}\n")

    # Mini tree
    tree = generate_mini_tree(project_dir, max_depth=2)
    body.append("\n")
    body.append(tree, style="dim")

    # Token estimate
    raw = body.plain
    est_tokens = max(1, len(raw) // 4)
    body.append(f"\n\n~{est_tokens} tokens", style="italic")

    title = f"Project Brief — {stack.name}"
    console.print(Panel(body, title=title))
