"""Environment variables info command — grouped, sensitive vars hidden."""

from __future__ import annotations

import os

from rich.console import Console
from rich.table import Table

# Regex patterns for sensitive variable names
_SENSITIVE_PATTERNS = ("API_KEY", "TOKEN", "SECRET", "PASSWORD", "KEY")

# Category mapping: prefix/substring → category label
_CATEGORY_RULES: list[tuple[set[str], str]] = [
    ({"PATH", "PATHEXT"}, "PATH"),
    ({"HOME", "USER", "USERNAME", "USERPROFILE", "HOMEDRIVE", "HOMEPATH"}, "HOME/USER"),
    ({"PYTHON", "PYTHONPATH", "PYENV", "VIRTUAL_ENV", "CONDA", "PIP", "UV_"}, "PYTHON"),
    ({"NODE", "NPM", "YARN", "PNPM_", "BUN_", "DENO_"}, "NODE"),
    ({"DOCKER", "KUBERNETES", "KUBE_", "HELM_"}, "DOCKER"),
    ({"AWS_", "AWS"}, "AWS"),
    ({"GIT_", "GIT"}, "GIT"),
    ({"CI", "JENKINS", "GITHUB_", "GITLAB_", "TRAVIS", "CIRCLE", "BUILDKITE"}, "CI"),
]


def envinfo_command(name_filter: str | None) -> None:
    """Print environment variables grouped by category.

    Sensitive variables (matching API_KEY, TOKEN, SECRET, PASSWORD, KEY)
    are shown as ``***HIDDEN***``.

    Args:
        name_filter: Optional substring to filter variable names (case-insensitive).
    """
    console = Console()

    # Group variables
    groups: dict[str, list[tuple[str, str]]] = {}
    for key, val in sorted(os.environ.items()):
        if name_filter and name_filter.lower() not in key.lower():
            continue
        cat = _classify_var(key)
        groups.setdefault(cat, []).append((key, val))

    table = Table(title="Environment Variables", padding=(0, 1))
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white", max_width=80)

    for cat in ("PATH", "HOME/USER", "PYTHON", "NODE", "DOCKER", "AWS", "GIT", "CI", "OTHER"):
        items = groups.pop(cat, [])
        if not items:
            continue
        for key, val in items:
            display_val = _redact(key, val)
            table.add_row(key, display_val)

    # Any remaining uncategorized
    for cat_name in sorted(groups.keys()):
        items = groups[cat_name]
        if not items:
            continue
        for key, val in items:
            table.add_row(key, _redact(key, val))

    console.print(table)


def _classify_var(name: str) -> str:
    """Classify a variable name into a category."""
    upper = name.upper()
    for prefixes, cat in _CATEGORY_RULES:
        for prefix in prefixes:
            if upper == prefix or upper.startswith(prefix):
                return cat
    return "OTHER"


def _redact(key: str, val: str) -> str:
    """Redact sensitive values."""
    upper_key = key.upper()
    for pat in _SENSITIVE_PATTERNS:
        if pat in upper_key:
            return "***HIDDEN***"
    return val
