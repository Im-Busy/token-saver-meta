"""Compact dependency listing — package names only, no versions.

Parses package.json, pyproject.toml, Cargo.toml, go.mod.
Outputs a Rich table grouped by manifest source.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:  # pragma: no cover — Python <3.11
    import tomli as tomllib  # type: ignore[no-redef]

from rich.console import Console
from rich.table import Table

_MANIFEST_FILES: dict[str, str] = {
    "package.json": "npm",
    "pyproject.toml": "pip",
    "Cargo.toml": "cargo",
    "go.mod": "go",
}


def _parse_package_json(path: Path) -> dict[str, list[str]]:
    """Extract dependency names (no versions) from package.json."""
    groups: dict[str, list[str]] = {}
    try:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return groups
    for section in ("dependencies", "devDependencies"):
        deps = data.get(section, {})
        if isinstance(deps, dict) and deps:
            groups[section] = sorted(deps.keys())
    return groups


def _parse_pyproject_toml(path: Path) -> dict[str, list[str]]:
    """Extract dependency names from pyproject.toml (PEP 621)."""
    groups: dict[str, list[str]] = {}
    try:
        data: dict[str, Any] = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError):
        return groups

    # PEP 621: [project] dependencies
    project = data.get("project", {})
    raw_deps = project.get("dependencies", [])
    if isinstance(raw_deps, list):
        names: list[str] = []
        for d in raw_deps:
            if isinstance(d, str):
                # Strip version specifiers: "rich>=13.0" → "rich"
                names.append(re.split(r"[<>=!~;]", d)[0].strip())
        if names:
            groups["dependencies"] = sorted(names)

    # Optional dependencies
    opt_deps: dict[str, Any] = project.get("optional-dependencies", {})
    if isinstance(opt_deps, dict):
        for group_name, deps in opt_deps.items():
            if isinstance(deps, list):
                names_opt: list[str] = []
                for d in deps:
                    if isinstance(d, str):
                        names_opt.append(re.split(r"[<>=!~;]", d)[0].strip())
                if names_opt:
                    groups[f"optional:{group_name}"] = sorted(names_opt)

    return groups


def _parse_cargo_toml(path: Path) -> dict[str, list[str]]:
    """Extract dependency names from Cargo.toml."""
    groups: dict[str, list[str]] = {}
    try:
        data: dict[str, Any] = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError):
        return groups
    for section in ("dependencies", "dev-dependencies", "build-dependencies"):
        deps: dict[str, Any] = data.get(section, {})
        if isinstance(deps, dict) and deps:
            groups[section] = sorted(deps.keys())
    return groups


# go.mod: `require (...)` block or single-line `require module/path version`
# Use [^\S\r\n] (horizontal space) to prevent \s from matching newlines.
_GO_REQUIRE_BLOCK = re.compile(r"^require[^\S\r\n]*\((.*?)\)", re.DOTALL | re.MULTILINE)
_GO_REQUIRE_LINE = re.compile(r"^require[^\S\r\n]+(\S+)[^\S\r\n]+\S+", re.MULTILINE)
_GO_DIRECT_LINE = re.compile(r"^[^\S\r\n]*(\S+)[^\S\r\n]+\S+", re.MULTILINE)


def _parse_go_mod(path: Path) -> dict[str, list[str]]:
    """Extract dependency names from go.mod require blocks."""
    groups: dict[str, list[str]] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return groups

    names: list[str] = []
    # Block form: require ( ... )
    for match in _GO_REQUIRE_BLOCK.finditer(text):
        block = match.group(1)
        for line in block.splitlines():
            m = _GO_DIRECT_LINE.match(line.strip())
            if m:
                names.append(m.group(1))
    # Single-line form: require module/path version
    for match in _GO_REQUIRE_LINE.finditer(text):
        names.append(match.group(1))

    if names:
        groups["require"] = sorted(names)
    return groups


def _collect_deps(directory: str) -> dict[str, dict[str, list[str]]]:
    """Scan *directory* for manifests and return parsed dependency groups."""
    result: dict[str, dict[str, list[str]]] = {}
    dir_path = Path(directory)
    for filename, label in _MANIFEST_FILES.items():
        manifest = dir_path / filename
        if not manifest.is_file():
            continue
        if filename == "package.json":
            groups = _parse_package_json(manifest)
        elif filename == "pyproject.toml":
            groups = _parse_pyproject_toml(manifest)
        elif filename == "Cargo.toml":
            groups = _parse_cargo_toml(manifest)
        elif filename == "go.mod":
            groups = _parse_go_mod(manifest)
        else:
            continue
        if groups:
            result[label] = groups
    return result


def deps_command(directory: str) -> None:
    """Compact dependency listing (no version numbers)."""
    console = Console()
    collected = _collect_deps(directory)

    if not collected:
        console.print("[dim]No dependency manifests found.[/dim]")
        return

    table = Table(title="Dependencies", show_header=True, header_style="bold")
    table.add_column("Source", style="cyan")
    table.add_column("Group", style="green")
    table.add_column("Packages", style="white")

    for source, groups in collected.items():
        first = True
        for group_name, pkg_list in groups.items():
            count = len(pkg_list)
            label = f"{group_name} ({count})"
            packages = ", ".join(pkg_list)
            if first:
                table.add_row(source, label, packages)
                first = False
            else:
                table.add_row("", label, packages)

    console.print(table)
