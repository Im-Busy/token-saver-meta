"""Unit tests for the AGENTS.md merged template and injector.

Phase 07a — Base Layer AGENTS.md Merge.
"""

from pathlib import Path


TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "agents_md_section.md"
START_MARKER = "<!-- TOKEN_SAVER_START -->"
END_MARKER = "<!-- TOKEN_SAVER_END -->"
PLATFORM_TERMS = ["Copilot", "Kevin", "/cost", "npx", "Claude Code", "wenyan",
                  "caveman mode", "/caveman", "/ponytail", "token-saver lite",
                  "token-saver full", "token-saver ultra", "token-saver off",
                  "tiktoken", "Not rude. Not cute.", "— saved ~N tokens"]
SOURCE_NAMES = ["caveman", "ponytail", "LG-token-saver", "kevin-copilot"]


class TestTemplate:
    """Tests for templates/agents_md_section.md."""

    def test_template_loads(self):
        """Template file exists and is readable."""
        assert TEMPLATE_PATH.exists(), f"Template not found at {TEMPLATE_PATH}"
        content = TEMPLATE_PATH.read_text(encoding="utf-8")
        assert len(content) > 100, "Template appears empty or too short"

    def test_template_has_markers(self):
        """Template contains both start and end markers."""
        content = TEMPLATE_PATH.read_text(encoding="utf-8")
        assert START_MARKER in content, "Missing start marker"
        assert END_MARKER in content, "Missing end marker"
        start_idx = content.index(START_MARKER)
        end_idx = content.index(END_MARKER)
        assert start_idx < end_idx, "End marker appears before start marker"

    def test_template_no_platform_specific(self):
        """Template contains no platform-specific references."""
        content = TEMPLATE_PATH.read_text(encoding="utf-8")
        for term in PLATFORM_TERMS:
            assert term not in content, f"Platform-specific term found: '{term}'"

    def test_template_line_count(self):
        """Template is ≤250 lines (compact enough not to bloat user's AGENTS.md)."""
        content = TEMPLATE_PATH.read_text(encoding="utf-8")
        # Count only lines between markers (the injectable content)
        start_idx = content.index(START_MARKER)
        end_idx = content.index(END_MARKER)
        block = content[start_idx:end_idx + len(END_MARKER)]
        line_count = block.count("\n")
        assert line_count <= 250, f"Template block is {line_count} lines, must be ≤250"

    def test_all_4_sources_represented(self):
        """Template references all 4 source tools in attribution comments."""
        content = TEMPLATE_PATH.read_text(encoding="utf-8")
        for name in SOURCE_NAMES:
            assert name in content, f"Source '{name}' not found in template"


class TestInjector:
    """Tests for src/agents_injector.py."""

    def test_injector_markers_match_template(self):
        """Injector uses the same markers as the template."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "agents_injector",
            Path(__file__).parent.parent / "src" / "agents_injector.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        # The injector should use the same markers as defined here
        assert hasattr(mod, 'START_MARKER') or hasattr(mod, '_START_MARKER'), \
            "Injector does not define START_MARKER"
        if hasattr(mod, 'START_MARKER'):
            assert mod.START_MARKER == START_MARKER, \
                f"Injector start marker mismatch: {mod.START_MARKER} != {START_MARKER}"
        if hasattr(mod, 'END_MARKER') or hasattr(mod, '_END_MARKER'):
            end = getattr(mod, 'END_MARKER', None) or getattr(mod, '_END_MARKER', None)
            assert end == END_MARKER, \
                f"Injector end marker mismatch: {end} != {END_MARKER}"

    def test_injector_has_is_injected(self):
        """Injector provides is_injected() function."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "agents_injector",
            Path(__file__).parent.parent / "src" / "agents_injector.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, 'is_injected'), \
            "Injector missing is_injected() function"

    def test_injector_has_remove_section(self):
        """Injector provides remove_injected_section() function."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "agents_injector",
            Path(__file__).parent.parent / "src" / "agents_injector.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, 'remove_injected_section'), \
            "Injector missing remove_injected_section() function"
