"""One-call bootstrap — detect project scope + build context pack.

Combines project scope resolution with context pack building into
a single function call. Useful as the first thing a newly-loaded
agent does to orient itself without needing separate tool calls.

Architecture:
  - scope_resolve(): Filesystem-based project scope detection.
  - bootstrap_context(): Combined scope + context pack in one call.
  - BootstrapResult: scope dict + ContextPack.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from token_saver_mem.session_memory.continuity import ContextPack, build_context_pack

# ── Language detection markers ────────────────────────────────────

_LANGUAGE_MARKERS: list[tuple[str, str]] = [
    ("python", "requirements.txt"),
    ("python", "pyproject.toml"),
    ("python", "setup.py"),
    ("python", "setup.cfg"),
    ("python", "Pipfile"),
    ("python", "*.py"),
    ("typescript", "tsconfig.json"),
    ("typescript", "*.ts"),
    ("typescript", "*.tsx"),
    ("typescript", "package.json"),
    ("rust", "Cargo.toml"),
    ("rust", "*.rs"),
    ("go", "go.mod"),
    ("go", "go.sum"),
    ("go", "*.go"),
]

# Framework detection by requirements/dependencies content
_FRAMEWORKS_PYTHON: dict[str, list[str]] = {
    "fastapi": ["fastapi"],
    "django": ["django", "manage.py"],
    "flask": ["flask"],
    "typer": ["typer"],
    "textual": ["textual"],
    "pydantic-ai": ["pydantic-ai", "pydantic_ai"],
    "click": ["click"],
}

_FRAMEWORKS_TYPESCRIPT: dict[str, list[str]] = {
    "react": ["react"],
    "next.js": ["next"],
    "hono": ["hono"],
    "express": ["express"],
    "nestjs": ["@nestjs"],
}

_FRAMEWORKS_RUST: dict[str, list[str]] = {
    "axum": ["axum"],
    "actix": ["actix"],
    "tokio": ["tokio"],
    "clap": ["clap"],
    "bevy": ["bevy"],
}

# Project type classification by framework
_PROJECT_TYPE_MAP: dict[str, str] = {
    "fastapi": "web",
    "django": "web",
    "flask": "web",
    "react": "web",
    "next.js": "web",
    "hono": "web",
    "express": "web",
    "nestjs": "web",
    "axum": "web",
    "actix": "web",
    "typer": "cli",
    "click": "cli",
    "clap": "cli",
    "textual": "tui",
    "bevy": "game",
    "pydantic-ai": "agent",
}

# File patterns that are "key files" — worth including in scope
_KEY_FILE_EXTS: set[str] = {".py", ".ts", ".tsx", ".rs", ".go", ".toml", ".json", ".yaml", ".yml"}
_KEY_FILE_NAMES: set[str] = {
    "main.py", "app.py", "server.py", "manage.py",
    "index.ts", "server.ts", "main.rs", "main.go",
    "pyproject.toml", "Cargo.toml", "go.mod", "package.json",
    "Dockerfile", "docker-compose.yml",
}
_KEY_FILE_IGNORE_DIRS: set[str] = {
    "__pycache__", ".git", "node_modules", "target", "dist", "build",
    ".venv", "venv", ".tox", ".mypy_cache", ".pytest_cache",
}


# ── BootstrapResult ───────────────────────────────────────────────


@dataclass
class BootstrapResult:
    """Combined result of scope resolution + context pack building.

    Attributes:
        scope: Scope dict with language, project_type, frameworks, key_files.
        context_pack: ContextPack with Markdown text, stats, and state.
    """

    scope: dict[str, Any]
    context_pack: ContextPack


# ── scope_resolve ─────────────────────────────────────────────────


def scope_resolve(project_path: str | None) -> dict[str, Any]:
    """Detect project type, language, and key files from filesystem.

    Scans the project directory for language markers, framework
    indicators in dependency files, and key source files.

    Args:
        project_path: Absolute or relative path to project root.
                      If None or non-existent, returns unknown scope.

    Returns:
        Dict with keys:
          - language: str — detected language ("python", "typescript", etc.)
          - project_type: str — "web", "cli", "tui", "agent", "unknown"
          - frameworks: list[str] — detected frameworks
          - key_files: list[str] — relative paths to key source/config files
    """
    if not project_path:
        return {
            "language": "unknown",
            "project_type": "unknown",
            "frameworks": [],
            "key_files": [],
        }

    root = Path(project_path)
    if not root.exists() or not root.is_dir():
        return {
            "language": "unknown",
            "project_type": "unknown",
            "frameworks": [],
            "key_files": [],
        }

    # Gather all files in the project (max depth 3, non-ignored)
    files: list[Path] = []
    for p in root.rglob("*"):
        if p.is_file() and not any(ignore in p.parts for ignore in _KEY_FILE_IGNORE_DIRS):
            # Limit depth to 3 for speed
            rel = p.relative_to(root)
            if len(rel.parts) <= 3:
                files.append(p)

    rel_files = [str(f.relative_to(root)) for f in files]

    # Detect language
    language = "unknown"
    for lang, marker in _LANGUAGE_MARKERS:
        # For glob-style markers (e.g., "*.py")
        if marker.startswith("*."):
            ext = marker[1:]
            if any(f.suffix == ext for f in files):
                language = lang
                break
        # For exact filenames
        elif any(f.name == marker for f in files):
            language = lang
            break

    # Detect frameworks from dependency files
    frameworks = _detect_frameworks(language, files)

    # Detect project type from frameworks
    project_type = "unknown"
    for fw in frameworks:
        if fw in _PROJECT_TYPE_MAP:
            project_type = _PROJECT_TYPE_MAP[fw]
            break

    # Collect key files
    key_files: list[str] = []
    for rel in rel_files:
        name = Path(rel).name
        ext = Path(rel).suffix
        if name in _KEY_FILE_NAMES or ext in _KEY_FILE_EXTS:
            # Only include source/config files, not README
            if name.lower() not in ("readme.md", "readme.rst", ".gitignore"):
                key_files.append(rel)

    # Sort and limit key files
    key_files.sort()
    key_files = key_files[:20]  # Max 20 key files

    return {
        "language": language,
        "project_type": project_type,
        "frameworks": frameworks,
        "key_files": key_files,
    }


def _detect_frameworks(language: str, files: list[Path]) -> list[str]:
    """Detect frameworks from dependency/content files."""
    if language == "python":
        return _detect_frameworks_from_content(files, _FRAMEWORKS_PYTHON)
    elif language == "typescript":
        return _detect_frameworks_from_content(files, _FRAMEWORKS_TYPESCRIPT)
    elif language == "rust":
        return _detect_frameworks_from_content(files, _FRAMEWORKS_RUST)
    return []


def _detect_frameworks_from_content(
    files: list[Path],
    framework_map: dict[str, list[str]],
) -> list[str]:
    """Scan dependency/config files for framework indicators."""
    found: list[str] = []
    seen: set[str] = set()

    dep_files = {".txt", ".toml", ".json", ".yaml", ".yml", ".cfg", ".ini"}
    dep_names = {"requirements.txt", "pyproject.toml", "package.json", "Cargo.toml"}

    for f in files:
        if f.name in dep_names or f.suffix in dep_files:
            try:
                content = f.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            for fw_name, markers in framework_map.items():
                if fw_name in seen:
                    continue
                for marker in markers:
                    if marker in content.lower():
                        found.append(fw_name)
                        seen.add(fw_name)
                        break

    # Also check for manage.py (Django) by filename
    if "django" not in seen:
        if any("manage.py" in str(f) for f in files):
            found.append("django")
            seen.add("django")

    return found


# ── Text-based scope detection ────────────────────────────────────


def _text_scope_detect(session_text: str) -> dict[str, Any]:
    """Detect project scope from session text (no filesystem access).

    Used as fallback when project_path is not provided.
    """
    text_lower = session_text.lower()

    # Language detection from keywords in text
    language = "unknown"
    py_indicators = [
        r"\bfastapi\b", r"\bdjango\b", r"\bflask\b", r"\bpython\b",
        r"\bpydantic\b", r"\bsqlalchemy\b", r"\.py\b", r"\buvicorn\b",
        r"\brestapi\s+", r"\bpip\s+install", r"\bpyproject\.toml\b",
        r"\brelative\s+import", r"\bdef\s+\w+\(self",
    ]
    ts_indicators = [
        r"\btypescript\b", r"\breact\b", r"\bnext\.js\b", r"\bhono\b",
        r"\.tsx?\b", r"\bnode_modules\b", r"\bpackage\.json\b",
        r"\bnpm\s+(install|run)", r"\byarn\s+(add|install)",
        r"\bconst\s+\w+\s*:\s*\w+", r"\binterface\s+\w+\s*\{",
    ]
    rs_indicators = [
        r"\brust\b", r"\bcargo\b", r"\bactix\b", r"\baxum\b",
        r"\btokio\b", r"\.rs\b", r"\bimpl\s+\w+\s+for\s+",
        r"\bstruct\s+\w+\s*\{", r"\bvec!\b", r"\bCargo\.toml\b",
    ]
    go_indicators = [
        r"\bgo\s+(build|run|mod|test)\b", r"\bgolang\b",
        r"\.go\b", r"\bgo\.mod\b", r"\bfunc\s+\w+\(.*\)\s+error",
        r"\bpackage\s+main\b", r"\berr\s*:=\s*",
    ]

    py_score = sum(1 for p in py_indicators if re.search(p, text_lower))
    ts_score = sum(1 for p in ts_indicators if re.search(p, text_lower))
    rs_score = sum(1 for p in rs_indicators if re.search(p, text_lower))
    go_score = sum(1 for p in go_indicators if re.search(p, text_lower))

    scores = {"python": py_score, "typescript": ts_score, "rust": rs_score, "go": go_score}
    if any(scores.values()):
        language = max(scores, key=lambda k: scores[k])  # type: ignore[arg-type, return-value]

    # Framework detection from text
    frameworks: list[str] = []
    _ALL_FW_MAPS = [_FRAMEWORKS_PYTHON, _FRAMEWORKS_TYPESCRIPT, _FRAMEWORKS_RUST]
    for fw_map in _ALL_FW_MAPS:
        for fw_name, markers in fw_map.items():
            if any(m in text_lower for m in markers):
                frameworks.append(fw_name)

    # Project type
    project_type = "unknown"
    for fw in frameworks:
        if fw in _PROJECT_TYPE_MAP:
            project_type = _PROJECT_TYPE_MAP[fw]
            break

    # If no frameworks but certain keywords suggest a type
    if project_type == "unknown":
        if any(kw in text_lower for kw in ("api", "endpoint", "http", "rest", "graphql", "server")):
            project_type = "web"
        elif any(kw in text_lower for kw in ("cli", "command-line", "terminal", "argparse", "subcommand")):
            project_type = "cli"

    return {
        "language": language,
        "project_type": project_type,
        "frameworks": frameworks,
        "key_files": [],  # Text-based has no filesystem
    }


# ── Main bootstrap entry point ────────────────────────────────────


def bootstrap_context(
    session_text: str,
    *,
    project_path: str | None = None,
) -> BootstrapResult:
    """Bootstrap context in a single call: scope resolve + context pack.

    Combines project scope detection and context pack building into
    one function. If project_path is provided, scope is detected from
    the filesystem. Otherwise, scope is detected from session text.

    Args:
        session_text: Raw agent session/conversation text for context pack.
        project_path: Optional path to project root directory. If provided,
                      filesystem-based scope detection is used.

    Returns:
        BootstrapResult with scope dict and ContextPack.
    """
    # Resolve scope
    if project_path and Path(project_path).exists():
        scope = scope_resolve(project_path)
    else:
        # Try project_path first even if invalid, then fall back
        scope = scope_resolve(project_path)
        if scope["language"] == "unknown":
            scope = _text_scope_detect(session_text)

    # Build context pack (auto-budget)
    pack = build_context_pack(session_text, budget="auto")

    return BootstrapResult(scope=scope, context_pack=pack)
