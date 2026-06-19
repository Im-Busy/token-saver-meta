from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

IGNORED_DIRS: set[str] = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    ".tox",
    ".mypy_cache",
    "target",
    ".idea",
    ".vscode",
}

STACK_SIGNALS: list[tuple[str, str, str]] = [
    ("Node.js", "package.json", "JavaScript"),
    ("Python", "pyproject.toml", "Python"),
    ("Python", "setup.py", "Python"),
    ("Python", "requirements.txt", "Python"),
    ("Rust", "Cargo.toml", "Rust"),
    ("Go", "go.mod", "Go"),
    ("Go", "go.sum", "Go"),
    ("Java", "pom.xml", "Java"),
    ("Java", "build.gradle", "Java"),
    ("Ruby", "Gemfile", "Ruby"),
    ("PHP", "composer.json", "PHP"),
    ("C#", "*.csproj", "C#"),
    ("Kotlin", "*.gradle.kts", "Kotlin"),
    ("Swift", "Package.swift", "Swift"),
    ("Dart", "pubspec.yaml", "Dart"),
    ("Elixir", "mix.exs", "Elixir"),
    ("Haskell", "stack.yaml", "Haskell"),
    ("Zig", "build.zig", "Zig"),
]

NODE_FRAMEWORKS: dict[str, str] = {
    "next": "Next.js",
    "react": "React",
    "vue": "Vue",
    "express": "Express",
    "fastify": "Fastify",
    "nestjs": "NestJS",
    "svelte": "Svelte",
    "astro": "Astro",
}

PYTHON_FRAMEWORKS: dict[str, str] = {
    "django": "Django",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "pydantic": "Pydantic",
    "sqlalchemy": "SQLAlchemy",
}


@dataclass
class StackInfo:
    name: str
    language: str
    has_typescript: bool = False
    detected_files: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)


def detect_stack(project_dir: Path) -> StackInfo | None:
    """Detect the project stack by scanning for known signal files.

    Checks the root directory first, then scans one level of subdirectories
    for signal files not found at root (e.g. monorepo sub-projects).
    """
    if not project_dir.is_dir():
        return None

    # Phase 1: check root directory for exact filename signals
    matched: list[tuple[str, str, str]] = []

    for stack_name, signal, language in STACK_SIGNALS:
        files: list[Path] = list(project_dir.glob(signal))
        for f in files:
            if f.name in IGNORED_DIRS:
                continue
            matched.append((stack_name, str(f.relative_to(project_dir)).replace("\\", "/"), language))
            break  # one match per signal type

    # Phase 2: one-level subdirectory scan for missed signals
    if not matched:
        for child in sorted(project_dir.iterdir()):
            if not child.is_dir() or child.name in IGNORED_DIRS or child.name.startswith("."):
                continue
            for stack_name, signal, language in STACK_SIGNALS:
                files = list(child.glob(signal))
                for f in files:
                    matched.append(
                        (stack_name, str(f.relative_to(project_dir)).replace("\\", "/"), language)
                    )
                    break  # one match per signal type per subdir
            if matched:
                break  # first subdir with matches wins

    if not matched:
        return None

    # Pick the first detected stack as primary
    primary = matched[0]
    name = primary[0]
    language = primary[2]
    detected_files = [m[1] for m in matched]

    # Check for TypeScript config alongside Node.js
    has_typescript = (
        name == "Node.js"
        and (
            (project_dir / "tsconfig.json").exists()
            or any(f.suffix in {".ts", ".tsx"} for f in project_dir.rglob("*.ts") if not any(ign in f.parts for ign in IGNORED_DIRS))
        )
    )

    # Framework detection
    frameworks: list[str] = []
    if name == "Node.js":
        frameworks = _detect_frameworks_node(project_dir)
    elif name == "Python":
        frameworks = _detect_frameworks_python(project_dir)

    return StackInfo(
        name=name,
        language=language,
        has_typescript=has_typescript,
        detected_files=detected_files,
        frameworks=frameworks,
    )


def _detect_frameworks_node(project_dir: Path) -> list[str]:
    """Detect Node.js frameworks from package.json dependencies."""
    pkgs: set[str] = set()
    pkg_path = project_dir / "package.json"
    if not pkg_path.is_file():
        return []

    try:
        data = json.loads(pkg_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    for section in ("dependencies", "devDependencies"):
        for dep in data.get(section, {}):
            pkgs.add(dep)

    found: list[str] = []
    for key, label in NODE_FRAMEWORKS.items():
        if key in pkgs:
            found.append(label)

    return found


def _detect_frameworks_python(project_dir: Path) -> list[str]:
    """Detect Python frameworks from requirements.txt or pyproject.toml."""
    pkgs: set[str] = set()

    # Check requirements.txt
    req_path = project_dir / "requirements.txt"
    if req_path.is_file():
        for line in req_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Extract package name before version specifier
            pkg = line.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].split("!=")[0].split("[")[0].strip().lower()
            pkgs.add(pkg)

    # Check pyproject.toml dependencies
    toml_path = project_dir / "pyproject.toml"
    if toml_path.is_file():
        try:
            content = toml_path.read_text(encoding="utf-8")
        except OSError:
            pass
        else:
            in_deps = False
            for line in content.splitlines():
                stripped = line.strip()
                if stripped == "[project]" or stripped.startswith("[project.optional-dependencies]"):
                    in_deps = True
                    continue
                if stripped.startswith("[") and stripped.endswith("]") and stripped != "[project]":
                    in_deps = False
                if in_deps and '="' in stripped:
                    pkg = stripped.split("=")[0].strip().strip('"').lower()
                    pkgs.add(pkg)

    found: list[str] = []
    for key, label in PYTHON_FRAMEWORKS.items():
        if key in pkgs:
            found.append(label)

    return found
