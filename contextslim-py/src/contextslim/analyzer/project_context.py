from __future__ import annotations

from pathlib import Path

from .stack_detector import IGNORED_DIRS, StackInfo

# Per-stack entry point patterns: (glob_pattern, label)
_ENTRY_PATTERNS: dict[str, list[tuple[str, str]]] = {
    "Node.js": [
        ("index.js", "index.js"),
        ("index.ts", "index.ts"),
        ("src/index.js", "src/index.js"),
        ("src/index.ts", "src/index.ts"),
        ("app.js", "app.js"),
        ("app.ts", "app.ts"),
        ("server.js", "server.js"),
        ("server.ts", "server.ts"),
        ("main.js", "main.js"),
        ("main.ts", "main.ts"),
    ],
    "Python": [
        ("main.py", "main.py"),
        ("app.py", "app.py"),
        ("run.py", "run.py"),
        ("manage.py", "manage.py (Django)"),
        ("src/main.py", "src/main.py"),
        ("src/app.py", "src/app.py"),
    ],
    "Rust": [
        ("src/main.rs", "src/main.rs"),
        ("main.rs", "main.rs"),
    ],
    "Go": [
        ("main.go", "main.go"),
        ("cmd/main.go", "cmd/main.go"),
        ("cmd/*/main.go", None),  # handled specially
    ],
    "Java": [
        ("src/main/java", "src/main/java/"),
    ],
    "Ruby": [
        ("app.rb", "app.rb"),
        ("main.rb", "main.rb"),
        ("config.ru", "config.ru (Rack)"),
    ],
    "PHP": [
        ("index.php", "index.php"),
        ("public/index.php", "public/index.php"),
    ],
    "Elixir": [
        ("lib/*.ex", None),
    ],
}


def detect_entry_points(project_dir: Path, stack: StackInfo) -> list[str]:
    """Detect likely entry-point files based on the detected stack."""
    if stack is None:
        return []

    patterns = _ENTRY_PATTERNS.get(stack.name, [])
    found: list[str] = []

    for pattern, label in patterns:
        matches = sorted(project_dir.glob(pattern))
        for m in matches:
            if any(ign in m.parts for ign in IGNORED_DIRS):
                continue
            entry = label or str(m.relative_to(project_dir)).replace("\\", "/")
            if entry not in found:
                found.append(entry)

    # Go special: cmd/*/main.go
    if stack.name == "Go":
        cmd_main = sorted(project_dir.glob("cmd/*/main.go"))
        for p in cmd_main:
            rel = str(p.relative_to(project_dir)).replace("\\", "/")
            if rel not in found:
                found.append(rel)

    return found


def generate_mini_tree(project_dir: Path, max_depth: int = 2) -> str:
    """Generate a compact directory tree of the project.

    Limits depth to *max_depth* and skips directories in IGNORED_DIRS.
    """
    if not project_dir.is_dir():
        return ""

    lines: list[str] = [project_dir.name or str(project_dir)]
    _tree_walk(project_dir, prefix="", depth=0, max_depth=max_depth, lines=lines, is_last_root=True)
    return "\n".join(lines)


def _tree_walk(
    directory: Path,
    prefix: str,
    depth: int,
    max_depth: int,
    lines: list[str],
    is_last_root: bool = False,
) -> None:
    """Recursively build tree lines."""
    if depth >= max_depth:
        return

    entries: list[Path] = []
    for child in sorted(directory.iterdir()):
        if child.name in IGNORED_DIRS or child.name.startswith("."):
            continue
        entries.append(child)

    # Sort: dirs first, then files
    entries.sort(key=lambda p: (not p.is_dir(), p.name.lower()))

    for i, entry in enumerate(entries):
        is_last = i == len(entries) - 1
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")

        if entry.is_dir() and depth + 1 < max_depth:
            extension = "    " if is_last else "│   "
            _tree_walk(entry, prefix + extension, depth + 1, max_depth, lines)
