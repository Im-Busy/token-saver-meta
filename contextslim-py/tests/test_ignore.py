"""Tests for contextslim.generators.ignore — ignore file generation."""

from __future__ import annotations

from pathlib import Path

import pytest

from contextslim.generators.ignore import generate_ignore, write_ignore


class TestGenerateIgnore:
    """Unit tests for generate_ignore()."""

    def test_always_includes_base_patterns(self) -> None:
        """Given: any stack. When: generate_ignore. Then: base patterns always present."""
        patterns = generate_ignore("node")
        for base in [".git/", "node_modules/", "dist/", "build/", "__pycache__/"]:
            assert base in patterns

    def test_includes_contextslim_marker(self) -> None:
        """Given: any stack. When: generate_ignore. Then: ContextSlim markers present."""
        patterns = generate_ignore("python")
        as_str = "\n".join(patterns)
        assert "ContextSlim Auto-Generated" in as_str
        assert "End ContextSlim" in as_str

    def test_node_stack_adds_next_dir(self) -> None:
        """Given: node stack. When: generate_ignore. Then: .next/ included."""
        patterns = generate_ignore("node")
        assert ".next/" in patterns

    def test_node_stack_adds_log_and_cache(self) -> None:
        """Given: node stack. When: generate_ignore. Then: *.log and .cache/ included."""
        patterns = generate_ignore("node")
        assert "*.log" in patterns
        assert ".cache/" in patterns

    def test_python_stack_adds_venv_and_pyc(self) -> None:
        """Given: python stack. When: generate_ignore. Then: venv + *.pyc included."""
        patterns = generate_ignore("python")
        assert "venv/" in patterns
        assert "*.pyc" in patterns
        assert "*.egg-info/" in patterns

    def test_python_stack_adds_mypy_and_pytest_cache(self) -> None:
        """Given: python stack. When: generate_ignore. Then: cache dirs included."""
        patterns = generate_ignore("python")
        assert ".mypy_cache/" in patterns
        assert ".pytest_cache/" in patterns

    def test_rust_stack_adds_target(self) -> None:
        """Given: rust stack. When: generate_ignore. Then: target/ included."""
        patterns = generate_ignore("rust")
        assert "target/" in patterns
        assert "Cargo.lock" in patterns

    def test_go_stack_adds_vendor(self) -> None:
        """Given: go stack. When: generate_ignore. Then: vendor/ included."""
        patterns = generate_ignore("go")
        assert "vendor/" in patterns
        assert "go.sum" in patterns

    def test_java_stack_adds_class_files(self) -> None:
        """Given: java stack. When: generate_ignore. Then: *.class + *.jar included."""
        patterns = generate_ignore("java")
        assert "*.class" in patterns
        assert "*.jar" in patterns

    def test_returns_list_of_strings(self) -> None:
        """Given: any input. When: generate_ignore. Then: returns list[str]."""
        patterns = generate_ignore("python")
        assert isinstance(patterns, list)
        assert all(isinstance(p, str) for p in patterns)

    def test_unknown_stack_returns_base_only(self) -> None:
        """Given: unknown stack name. When: generate_ignore. Then: base patterns only."""
        patterns = generate_ignore("haskell")
        # Base + markers; no stack-specific sections
        as_str = "\n".join(patterns)
        assert ".git/" in patterns
        assert "target/" not in patterns  # no Rust patterns for haskell
        assert "venv/" not in patterns  # no Python patterns


class TestStackAliases:
    """Unit tests for stack name normalization."""

    def test_next_js_maps_to_node(self) -> None:
        """Given: "next.js" stack. When: generate_ignore. Then: node patterns included."""
        patterns = generate_ignore("next.js")
        assert ".next/" in patterns

    def test_lowercase_variant(self) -> None:
        """Given: "PYTHON" (uppercase). When: generate_ignore. Then: python patterns included."""
        patterns = generate_ignore("PYTHON")
        assert "venv/" in patterns

    def test_react_maps_to_node(self) -> None:
        """Given: "React" stack. When: generate_ignore. Then: node patterns included."""
        patterns = generate_ignore("React")
        assert ".next/" in patterns  # Node stack


class TestWriteIgnore:
    """Integration tests for write_ignore()."""

    def test_writes_new_gitignore(self, tmp_path: Path) -> None:
        """Given: no existing .gitignore. When: write_ignore. Then: file created with patterns."""
        added = write_ignore(tmp_path, "python")
        assert (tmp_path / ".gitignore").exists()
        assert len(added) > 0

    def test_returns_newly_added_patterns(self, tmp_path: Path) -> None:
        """Given: empty project. When: write_ignore. Then: returns list of pattern strings."""
        added = write_ignore(tmp_path, "node")
        assert isinstance(added, list)
        assert all(isinstance(p, str) for p in added)
        assert ".next/" in added

    def test_added_patterns_exclude_comments_and_blanks(self, tmp_path: Path) -> None:
        """Given: new .gitignore. When: write_ignore. Then: return value excludes comments."""
        added = write_ignore(tmp_path, "python")
        for pat in added:
            assert not pat.startswith("#"), f"Comment '{pat}' in return value"
            assert pat.strip(), f"Blank '{pat}' in return value"

    def test_merges_with_existing_gitignore_no_duplicates(self, tmp_path: Path) -> None:
        """Given: existing .gitignore with some patterns. When: write_ignore. Then: only new patterns added."""
        existing = tmp_path / ".gitignore"
        existing.write_text(".git/\n.env\n")
        added = write_ignore(tmp_path, "node")
        # .git/ already exists, should not be in added
        assert ".git/" not in added
        content = existing.read_text()
        assert content.count(".git/") == 1  # not duplicated

    def test_does_not_duplicate_existing_contextslim_patterns(self, tmp_path: Path) -> None:
        """Given: .gitignore with previous ContextSlim run. When: write_ignore. Then: no duplicated patterns."""
        existing = tmp_path / ".gitignore"
        # First run
        write_ignore(tmp_path, "python")
        after_first = existing.read_text()
        # Second run — same stack
        _ = write_ignore(tmp_path, "python")
        after_second = existing.read_text()
        assert after_second == after_first

    def test_line_exact_match_no_duplication(self, tmp_path: Path) -> None:
        """Given: .gitignore with "node_modules/". When: write_ignore(node). Then: node_modules/ not added again."""
        existing = tmp_path / ".gitignore"
        existing.write_text("node_modules/\n")
        added = write_ignore(tmp_path, "node")
        assert "node_modules/" not in added

    def test_writes_zero_patterns_when_all_exist(self, tmp_path: Path) -> None:
        """Given: .gitignore with all base + node patterns. When: write_ignore. Then: returns empty list."""
        existing = tmp_path / ".gitignore"
        all_pats = generate_ignore("node")
        existing.write_text("\n".join(all_pats) + "\n")
        added = write_ignore(tmp_path, "node")
        assert added == []  # nothing new

    def test_multiple_stacks_accumulate(self, tmp_path: Path) -> None:
        """Given: python patterns written. When: rust stack also written. Then: both present, no dupes."""
        write_ignore(tmp_path, "python")
        write_ignore(tmp_path, "rust")
        content = (tmp_path / ".gitignore").read_text()
        assert "venv/" in content
        assert "target/" in content
        # Check no duplicate markers
        assert content.count("ContextSlim Auto-Generated") == 1
