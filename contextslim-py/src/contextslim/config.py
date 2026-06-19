from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:  # pragma: no cover — Python <3.11
    import tomli as tomllib  # type: ignore[no-redef]

DEFAULT_TOML_NAME = ".contextslim.toml"


@dataclass
class Limits:
    """Per-command output limits."""

    cat_lines: int = 150
    grep_matches_per_file: int = 5
    grep_max_total: int = 50
    tree_depth: int = 3
    max_line_width: int = 120
    outline_max_sigs_per_file: int = 15
    db_sample_rows: int = 5
    db_max_columns: int = 20
    procs_limit: int = 30
    services_limit: int = 30
    findfiles_limit: int = 30
    todo_max_total: int = 50


@dataclass
class Config:
    """Root configuration for ContextSlim."""

    limits: Limits = field(default_factory=Limits)


DEFAULT_CONFIG = Config()


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *override* into *base*, returning a new dict.

    Scalar values from *override* replace those in *base*.  Nested dicts
    are merged recursively; everything else (lists, etc.) is replaced
    wholesale.
    """
    merged: dict[str, Any] = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _toml_to_dict(data: dict[str, Any], section: str) -> dict[str, Any]:
    """Extract a TOML section, lower-casing keys for case-insensitive matching."""
    return {k.lower(): v for k, v in data.get(section, {}).items()}


def load_config(project_dir: Path | None = None) -> Config:
    """Load configuration, deep-merging a project ``.contextslim.toml``
    over :data:`DEFAULT_CONFIG`.

    *project_dir* defaults to the current working directory.  If no TOML
    file is found the default configuration is returned unchanged.
    """
    root = Path(project_dir) if project_dir is not None else Path.cwd()
    toml_path = root / DEFAULT_TOML_NAME

    if not toml_path.is_file():
        return DEFAULT_CONFIG

    raw = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    limits_raw = _toml_to_dict(raw, "limits")

    merged_limits = _deep_merge(
        {k: v for k, v in Limits().__dict__.items()},
        limits_raw,
    )

    return Config(limits=Limits(**merged_limits))
