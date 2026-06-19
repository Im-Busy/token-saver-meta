"""Tests for contextslim.config."""

from __future__ import annotations

import tempfile
from pathlib import Path

from contextslim.config import DEFAULT_CONFIG, Config, Limits, load_config

# ============================================================================
# Defaults
# ============================================================================


class TestDefaults:
    """Default configuration carries expected values."""

    def test_default_config_exists(self) -> None:
        assert isinstance(DEFAULT_CONFIG, Config)
        assert isinstance(DEFAULT_CONFIG.limits, Limits)

    def test_default_limits(self) -> None:
        lim = DEFAULT_CONFIG.limits
        assert lim.cat_lines == 150
        assert lim.grep_matches_per_file == 5
        assert lim.grep_max_total == 50
        assert lim.tree_depth == 3
        assert lim.max_line_width == 120

    def test_load_config_no_file_returns_default(self) -> None:
        cfg = load_config(Path("/nonexistent_dir_xyz"))
        assert cfg.limits.cat_lines == 150
        assert cfg.limits.grep_max_total == 50


# ============================================================================
# TOML loading
# ============================================================================


_TOML_BASIC = """\
[limits]
cat_lines = 42
tree_depth = 7
"""


class TestTomlLoad:
    """TOML files override defaults."""

    def test_basic_override(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".contextslim.toml").write_text(_TOML_BASIC, encoding="utf-8")
            cfg = load_config(root)
            assert cfg.limits.cat_lines == 42
            assert cfg.limits.tree_depth == 7
            # Unspecified keys keep defaults.
            assert cfg.limits.grep_max_total == 50

    def test_partial_limits_section(self) -> None:
        toml = "[limits]\nmax_line_width = 80\n"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".contextslim.toml").write_text(toml, encoding="utf-8")
            cfg = load_config(root)
            assert cfg.limits.max_line_width == 80
            assert cfg.limits.cat_lines == 150  # untouched


# ============================================================================
# Deep merge
# ============================================================================


class TestDeepMerge:
    """Nested TOML sections merge without clobbering siblings."""

    def test_non_overlapping_keys_preserved(self) -> None:
        toml = "[limits]\ndb_sample_rows = 2\n"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".contextslim.toml").write_text(toml, encoding="utf-8")
            cfg = load_config(root)
            assert cfg.limits.db_sample_rows == 2
            assert cfg.limits.cat_lines == 150

    def test_all_limits_overridden(self) -> None:
        """Every Limits field can be set from TOML."""
        fields = {
            "cat_lines": 1,
            "grep_matches_per_file": 2,
            "grep_max_total": 3,
            "tree_depth": 4,
            "max_line_width": 5,
            "outline_max_sigs_per_file": 6,
            "db_sample_rows": 7,
            "db_max_columns": 8,
            "procs_limit": 9,
            "services_limit": 10,
            "findfiles_limit": 11,
            "todo_max_total": 12,
        }
        toml = "[limits]\n" + "\n".join(f"{k} = {v}" for k, v in fields.items())
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".contextslim.toml").write_text(toml, encoding="utf-8")
            cfg = load_config(root)
            for k, v in fields.items():
                assert getattr(cfg.limits, k) == v

    def test_missing_toml_file_returns_default(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cfg = load_config(Path(td))  # no .contextslim.toml
            assert cfg.limits == DEFAULT_CONFIG.limits


# ============================================================================
# CWD fallback
# ============================================================================


class TestCwdFallback:
    """load_config(None) uses CWD."""

    def test_none_uses_cwd(self) -> None:
        # load_config(None) resolves to Path.cwd().
        # In a test run under a temp dir that has no .contextslim.toml,
        # we just get the default config.
        cfg = load_config(None)
        assert isinstance(cfg, Config)
        assert cfg.limits.cat_lines == 150
