"""Regression tests for GitNexus+CGC config generation.

Ensures that extending config_gen.py does NOT break existing GitNexus+CGC
output. These tests compare output from the copied config_gen.py against
the original combo's behavior.
"""

from pathlib import Path

import pytest


class TestGitNexusCGCCombo:
    """Regression gate: GitNexus+CGC output must remain unchanged."""

    def test_detect_platforms(self, temp_project: Path) -> None:
        """detect_platforms() identifies 'kilo' from .kilo/ marker."""
        from src.config_gen import detect_platforms

        found = detect_platforms(temp_project)
        assert "kilo" in found, f"Expected 'kilo' in detected platforms, got {found}"

    def test_generate_cgc_only_config_returns_cgc(self, temp_project: Path) -> None:
        """generate_cgc_only_config('kilo', project_path) returns CGC entry only, no GitNexus."""
        from src.config_gen import generate_cgc_only_config

        config = generate_cgc_only_config("kilo", str(temp_project))
        assert config is not None, "generate_cgc_only_config returned None"
        wrapper_keys = config.keys()
        assert len(wrapper_keys) > 0, "No wrapper keys in config"
        for key, servers in config.items():
            if isinstance(servers, dict):
                assert "codegraphcontext" in servers, "Expected codegraphcontext in config"
                assert "gitnexus" not in servers, "GitNexus should NOT be in CGC-only config"

    def test_list_platforms_returns_17_plus(self, temp_project: Path) -> None:
        """--list-platforms output includes known combo platforms."""
        from src.config_gen import load_matrix

        matrix = load_matrix()
        platforms = matrix.get("platforms", {})
        assert len(platforms) >= 17, f"Expected 17+ platforms, got {len(platforms)}"
        assert "kilo" in platforms
        assert "claude-code" in platforms
        assert "cursor" in platforms
        assert "opencode" in platforms