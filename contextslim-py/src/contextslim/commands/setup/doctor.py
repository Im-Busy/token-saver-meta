"""doctor — check configuration health."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.text import Text

from contextslim.analyzer.stack_detector import detect_stack

console = Console(highlight=False)

# IDE rules files to check for
_IDE_FILES: dict[str, str] = {
    "cursor": ".cursorrules",
    "claude": "CLAUDE.md",
    "copilot": ".github/copilot-instructions.md",
    "windsurf": ".windsurfrules",
}


@dataclass
class Check:
    name: str
    status: str  # PASS, FAIL, WARN
    detail: str


def _check_config(project_dir: Path) -> Check:
    config_path = project_dir / ".contextslim.toml"
    if config_path.is_file():
        return Check(
            name=".contextslim.toml",
            status="PASS",
            detail=f"Found at {config_path}",
        )
    return Check(
        name=".contextslim.toml",
        status="FAIL",
        detail="Not found. Run `contextslim setup init` to create.",
    )


def _check_stack(project_dir: Path) -> Check:
    stack = detect_stack(project_dir)
    if stack is not None:
        detail = f"Detected: {stack.name} ({stack.language})"
        if stack.frameworks:
            detail += f" — {', '.join(stack.frameworks)}"
        if stack.has_typescript:
            detail += " (TypeScript)"
        return Check(name="Stack Detection", status="PASS", detail=detail)
    return Check(
        name="Stack Detection",
        status="WARN",
        detail="No stack detected. AI rules will use generic defaults.",
    )


def _check_ignore(project_dir: Path) -> Check:
    gitignore = project_dir / ".gitignore"
    if not gitignore.is_file():
        return Check(
            name=".gitignore",
            status="FAIL",
            detail="Not found. Run `contextslim setup init` to generate.",
        )
    content = gitignore.read_text(encoding="utf-8")
    if "ContextSlim" in content:
        return Check(name=".gitignore", status="PASS", detail="Contains ContextSlim patterns")
    if any(pat in content for pat in ("node_modules/", "__pycache__/", ".git/")):
        return Check(
            name=".gitignore",
            status="WARN",
            detail="Exists but missing ContextSlim patterns. Run `contextslim setup init` to add.",
        )
    return Check(
        name=".gitignore",
        status="WARN",
        detail="Exists but may not cover heavy dirs. Run `contextslim setup init` to add patterns.",
    )


def _check_ide_rules(project_dir: Path) -> Check:
    found: list[str] = []
    for ide, rel_path in _IDE_FILES.items():
        file_path = project_dir / rel_path
        if file_path.is_file():
            found.append(ide)

    if not found:
        return Check(
            name="AI/IDE Rules",
            status="WARN",
            detail="No IDE rule files found. Run `contextslim setup init` to generate.",
        )
    return Check(
        name="AI/IDE Rules",
        status="PASS",
        detail=f"Found for: {', '.join(found)}",
    )


def _check_git(project_dir: Path) -> Check:
    git_dir = project_dir / ".git"
    if git_dir.is_dir():
        return Check(name="Git Repository", status="PASS", detail=".git directory found")
    # Check with git command
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return Check(name="Git Repository", status="PASS", detail="Git detected via CLI")
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return Check(
        name="Git Repository",
        status="WARN",
        detail="Not a git repository. Some commands require git.",
    )


def _check_config_valid(project_dir: Path) -> Check:
    config_path = project_dir / ".contextslim.toml"
    if not config_path.is_file():
        return Check(
            name="Config Validity",
            status="WARN",
            detail="No config to validate. Run `contextslim setup init`.",
        )
    try:
        from contextslim.config import load_config

        load_config(project_dir)
        return Check(name="Config Validity", status="PASS", detail="Config parses successfully")
    except Exception as exc:
        return Check(
            name="Config Validity",
            status="FAIL",
            detail=f"Parse error: {exc}",
        )


def doctor_command(directory: str) -> None:
    """Check configuration health.

    Checks:
    - .contextslim.toml exists
    - Stack detection works
    - .gitignore exists with ContextSlim patterns
    - AI/IDE rule files exist
    - Git repository detected
    - Config validity (if exists)

    Displays results in a Rich table with PASS/FAIL/WARN status.
    """
    project_dir = Path(directory).resolve()
    if not project_dir.is_dir():
        console.print(f"[red]Error:[/red] Directory not found: {directory}")
        return

    # Header
    header = Text()
    header.append("ContextSlim Health Check", style="bold")
    header.append("  ", style="")
    header.append(str(project_dir), style="dim")
    console.print(header)
    console.print()

    # Run all checks
    checks = [
        _check_config(project_dir),
        _check_stack(project_dir),
        _check_ignore(project_dir),
        _check_ide_rules(project_dir),
        _check_git(project_dir),
        _check_config_valid(project_dir),
    ]

    # Build table
    table = Table(title="Configuration Health")
    table.add_column("Check", style="bold")
    table.add_column("Status")
    table.add_column("Detail", style="dim")

    pass_count = 0
    warn_count = 0
    fail_count = 0

    for check in checks:
        if check.status == "PASS":
            status_str = "[green]PASS[/green]"
            pass_count += 1
        elif check.status == "FAIL":
            status_str = "[red]FAIL[/red]"
            fail_count += 1
        else:
            status_str = "[yellow]WARN[/yellow]"
            warn_count += 1
        table.add_row(check.name, status_str, check.detail)

    console.print(table)
    console.print()

    # Summary
    summary_parts: list[str] = []
    if pass_count:
        summary_parts.append(f"[green]{pass_count} passed[/green]")
    if warn_count:
        summary_parts.append(f"[yellow]{warn_count} warnings[/yellow]")
    if fail_count:
        summary_parts.append(f"[red]{fail_count} failed[/red]")

    console.print("  ".join(summary_parts))

    if fail_count > 0:
        console.print()
        console.print("[red]Fix failures with:[/red] `contextslim setup init`")
    elif warn_count > 0:
        console.print()
        console.print("[yellow]Resolve warnings with:[/yellow] `contextslim setup init`")
    else:
        console.print()
        console.print("[green]✓[/green] All checks passed. ContextSlim is properly configured.")
