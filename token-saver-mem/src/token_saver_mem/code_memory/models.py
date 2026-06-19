"""Data models for code_memory — ported from Loom, simplified for Python-only v1."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CodeNode:
    """A structural element extracted from Python source code.

    Mirrors Loom's Node but simplified: no Pydantic, no StrEnum, no extra fields.
    """

    id: str  # "function:module.py:func_name" or "class:module.py:ClassName"
    kind: str  # "function", "class", "method", "module"
    name: str
    path: str  # relative POSIX-style path
    start_line: int | None = None
    end_line: int | None = None
    content_hash: str | None = None
    summary: str | None = None
    summary_hash: str | None = None
    metadata: dict = field(default_factory=dict)  # params, return_type, docstring, decorators, bases

    @staticmethod
    def make_id(kind: str, path: str, name: str) -> str:
        """Format: kind:path:name (compatible with Loom convention)."""
        posix_path = path.replace("\\", "/")
        return f"{kind}:{posix_path}:{name}"


@dataclass
class FileFingerprint:
    """Stored fingerprint for incremental indexing."""

    file_path: str
    content_sha: str
    mtime_ns: int
    indexed_at: float


@dataclass
class ChangeReport:
    """Result of classify_changes — 3-tier change detection."""

    added: list[str] = field(default_factory=list)  # New files not in DB
    modified: list[str] = field(default_factory=list)  # Content changed
    deleted: list[str] = field(default_factory=list)  # In DB but not on disk
    unchanged: list[str] = field(default_factory=list)  # Content same

    @property
    def files_to_index(self) -> list[str]:
        """Files needing full parse — added + modified."""
        return self.added + self.modified
