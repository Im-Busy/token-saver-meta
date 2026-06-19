"""Ignore file generation for ContextSlim.

Generates .gitignore patterns per language stack with merge logic
that never duplicates existing entries.
"""

from __future__ import annotations

from pathlib import Path

# ── Base patterns (all stacks) ──────────────────────────────────
_BASE_PATTERNS = [
    "# ===== ContextSlim Auto-Generated =====",
    ".git/",
    "node_modules/",
    "dist/",
    "build/",
    "__pycache__/",
]

# ── Stack-specific patterns ─────────────────────────────────────
_STACK_PATTERNS: dict[str, list[str]] = {
    "node": [
        ".next/",
        "*.log",
        ".cache/",
    ],
    "python": [
        "venv/",
        ".venv/",
        "*.pyc",
        "*.pyo",
        "__pycache__/",
        ".mypy_cache/",
        ".pytest_cache/",
        "*.egg-info/",
    ],
    "rust": [
        "target/",
        "*.rlib",
        "Cargo.lock",
    ],
    "go": [
        "vendor/",
        "go.sum",
    ],
    "java": [
        "*.class",
        "*.jar",
        "*.war",
        ".gradle/",
        "build/",
    ],
}

# ── Stack aliases (normalized name lookups) ─────────────────────
_STACK_ALIASES: dict[str, list[str]] = {
    "node": ["node", "node.js", "nodejs", "next.js", "next", "react", "vue", "nuxt", "angular", "svelte", "typescript", "javascript", "js", "ts"],
    "python": ["python", "django", "flask", "fastapi", "py"],
    "rust": ["rust", "rs"],
    "go": ["go", "golang"],
    "java": ["java", "kotlin", "scala", "gradle", "maven"],
}


def _normalize_stack(stack_name: str) -> str | None:
    """Map a stack name to its canonical pattern group."""
    lower = stack_name.lower()
    for canonical, aliases in _STACK_ALIASES.items():
        if lower in aliases:
            return canonical
    return None


def generate_ignore(stack_name: str) -> list[str]:
    """Get ignore patterns for a stack.

    Args:
        stack_name: Stack identifier (e.g. "node", "python", "rust", "go", "next.js").

    Returns:
        List of ignore pattern strings.
    """
    patterns = list(_BASE_PATTERNS)
    canonical = _normalize_stack(stack_name)
    if canonical and canonical in _STACK_PATTERNS:
        patterns.append("")
        patterns.append(f"# {canonical.title()}-specific")
        patterns.extend(_STACK_PATTERNS[canonical])
    patterns.append("")
    patterns.append("# ===== End ContextSlim =====")
    return patterns


def write_ignore(project_dir: Path, stack_name: str) -> list[str]:
    """Write or merge ignore patterns into the project .gitignore.

    Reads the existing .gitignore (if any), adds only patterns
    that don't already appear (line-exact match), and writes back.

    Args:
        project_dir: Root directory of the target project.
        stack_name: Stack identifier for stack-specific patterns.

    Returns:
        List of newly added patterns (excluding comments and blanks).
    """
    gitignore = project_dir / ".gitignore"
    new_patterns = generate_ignore(stack_name)

    existing_lines: list[str] = []
    if gitignore.exists():
        raw = gitignore.read_text(encoding="utf-8")
        existing_lines = [line.rstrip("\n").rstrip("\r") for line in raw.splitlines()]

    # Build set of existing patterns for O(1) lookup
    existing_set = set(existing_lines)

    # Collect only truly new patterns (non-comment, non-blank)
    added: list[str] = []
    for pat in new_patterns:
        if pat in existing_set:
            continue
        added.append(pat)

    if added:
        # Append new patterns to existing content
        if existing_lines and existing_lines[-1] != "":
            existing_lines.append("")
        existing_lines.extend(added)
        gitignore.write_text("\n".join(existing_lines) + "\n", encoding="utf-8")

    # Return newly added non-comment, non-blank patterns
    return [p for p in added if p.strip() and not p.strip().startswith("#")]
