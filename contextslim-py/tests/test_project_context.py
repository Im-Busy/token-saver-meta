from __future__ import annotations

from pathlib import Path

import pytest

from contextslim.analyzer.project_context import (
    detect_entry_points,
    generate_mini_tree,
)
from contextslim.analyzer.stack_detector import StackInfo


def _make_stack(name: str, language: str) -> StackInfo:
    return StackInfo(name=name, language=language)


class TestDetectEntryPoints:
    """Given a project directory and stack info,
    detect_entry_points must return the correct entry-point files."""

    def test_nodejs_entry_points(self, tmp_path: Path) -> None:
        """When Node.js stack, detect index.js / server.js / app.js."""
        (tmp_path / "package.json").write_text("{}")
        (tmp_path / "index.js").write_text("// entry")
        (tmp_path / "app.js").write_text("// app")

        stack = _make_stack("Node.js", "JavaScript")
        entries = detect_entry_points(tmp_path, stack)

        assert "index.js" in entries
        assert "app.js" in entries

    def test_python_entry_points(self, tmp_path: Path) -> None:
        """When Python stack, detect main.py / app.py."""
        (tmp_path / "main.py").write_text("# main")
        (tmp_path / "app.py").write_text("# app")

        stack = _make_stack("Python", "Python")
        entries = detect_entry_points(tmp_path, stack)

        assert "main.py" in entries
        assert "app.py" in entries

    def test_go_entry_points(self, tmp_path: Path) -> None:
        """When Go stack, detect cmd/*/main.go and main.go."""
        (tmp_path / "main.go").write_text("package main")
        cmd = tmp_path / "cmd" / "server"
        cmd.mkdir(parents=True)
        (cmd / "main.go").write_text("package main")

        stack = _make_stack("Go", "Go")
        entries = detect_entry_points(tmp_path, stack)

        assert "main.go" in entries
        assert "cmd/server/main.go" in entries

    def test_rust_entry_points(self, tmp_path: Path) -> None:
        """When Rust stack, detect src/main.rs."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.rs").write_text("fn main() {}")

        stack = _make_stack("Rust", "Rust")
        entries = detect_entry_points(tmp_path, stack)

        assert "src/main.rs" in entries

    def test_no_entry_points_when_missing(self, tmp_path: Path) -> None:
        """When no entry-point files exist, return empty list."""
        stack = _make_stack("Python", "Python")
        entries = detect_entry_points(tmp_path, stack)

        assert entries == []

    def test_none_stack_returns_empty(self, tmp_path: Path) -> None:
        """When stack is None, return empty list."""
        (tmp_path / "index.html").write_text("<html>")
        entries = detect_entry_points(tmp_path, None)  # type: ignore[arg-type]
        assert entries == []

    def test_unknown_stack_returns_empty(self, tmp_path: Path) -> None:
        """When stack has no known entry patterns, return empty list."""
        (tmp_path / "main.c").write_text("int main() {}")
        stack = _make_stack("C", "C")
        entries = detect_entry_points(tmp_path, stack)
        assert entries == []


class TestGenerateMiniTree:
    """Given a project directory, generate_mini_tree must produce
    a compact directory tree respecting max_depth and ignored dirs."""

    def test_basic_tree(self, tmp_path: Path) -> None:
        """Tree shows files and directories."""
        (tmp_path / "README.md").write_text("# Project")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hi')")

        tree = generate_mini_tree(tmp_path, max_depth=2)

        assert "README.md" in tree
        assert "src" in tree
        assert "main.py" in tree

    def test_depth_cap(self, tmp_path: Path) -> None:
        """Tree respects max_depth and shows '...' for truncated dirs."""
        deep = tmp_path / "a" / "b" / "c"
        deep.mkdir(parents=True)
        (deep / "deep.py").write_text("x=1")

        tree = generate_mini_tree(tmp_path, max_depth=2)

        # a/b visible, but b/c should not be expanded
        assert "a" in tree
        assert "b" in tree
        # c directory should not appear as a tree entry (depth capped at 2)
        # Check that "c" does not appear as a standalone entry line
        tree_lines = tree.split("\n")
        entry_names = [line.strip().removeprefix("├── ").removeprefix("└── ") for line in tree_lines if "──" in line]
        assert "c" not in entry_names
        assert "deep.py" not in tree

    def test_ignored_dirs_omitted(self, tmp_path: Path) -> None:
        """Ignored directories like node_modules are not shown."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hi')")
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "lodash").mkdir()
        (tmp_path / ".git").mkdir()

        tree = generate_mini_tree(tmp_path, max_depth=2)

        assert "node_modules" not in tree
        assert ".git" not in tree
        assert "src" in tree
        assert "main.py" in tree

    def test_hidden_files_omitted(self, tmp_path: Path) -> None:
        """Files/dirs starting with '.' are omitted."""
        (tmp_path / ".env").write_text("SECRET=1")
        (tmp_path / ".config").mkdir()
        (tmp_path / "data.txt").write_text("hello")

        tree = generate_mini_tree(tmp_path, max_depth=2)

        assert ".env" not in tree
        assert ".config" not in tree
        assert "data.txt" in tree

    def test_empty_dir(self, tmp_path: Path) -> None:
        """Empty directory produces only the root name."""
        tree = generate_mini_tree(tmp_path, max_depth=2)

        lines = tree.strip().split("\n")
        assert len(lines) == 1
        assert lines[0] == tmp_path.name

    def test_sorting_dirs_first(self, tmp_path: Path) -> None:
        """Directories appear before files in tree output."""
        (tmp_path / "zebra.txt").write_text("z")
        (tmp_path / "alpha").mkdir()
        (tmp_path / "alpha" / "a.txt").write_text("a")

        tree = generate_mini_tree(tmp_path, max_depth=2)

        # alpha (dir) should appear before zebra.txt (file)
        alpha_pos = tree.find("alpha")
        zebra_pos = tree.find("zebra.txt")
        assert alpha_pos < zebra_pos
