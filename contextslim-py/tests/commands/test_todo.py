"""Tests for contextslim.commands.search.todo."""

from __future__ import annotations

import tempfile
from pathlib import Path

from contextslim.commands.search.todo import _is_binary, _walk_todos
from contextslim.config import Config, Limits


class TestWalkTodos:
    def test_basic_todos(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "main.py").write_text(
                "# TODO: fix this\nprint('hello')\n# FIXME: broken logic\n",
                encoding="utf-8",
            )
            (root / "utils.py").write_text(
                "// HACK: workaround\n// NOTE: remove later\n",
                encoding="utf-8",
            )
            results = _walk_todos(td)
            assert "main.py" in results
            assert len(results["main.py"]) == 2
            assert results["main.py"][0][1] == "TODO"
            assert results["main.py"][1][1] == "FIXME"
            assert "utils.py" in results
            assert len(results["utils.py"]) == 2

    def test_skips_ignored_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            node_modules = root / "node_modules"
            node_modules.mkdir()
            (node_modules / "lib.js").write_text("// TODO: ignore me\n", encoding="utf-8")
            (root / "README.md").write_text("TODO: write docs\n", encoding="utf-8")
            results = _walk_todos(td)
            assert "node_modules/lib.js" not in results
            assert "README.md" in results

    def test_skips_binary_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00")
            (root / "real.py").write_text("# TODO: real\n", encoding="utf-8")
            results = _walk_todos(td)
            assert "image.png" not in results
            assert "real.py" in results

    def test_no_matches(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "clean.py").write_text("print('clean')\n", encoding="utf-8")
            results = _walk_todos(td)
            assert results == {}

    def test_empty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            results = _walk_todos(td)
            assert results == {}

    def test_all_tags_matched(self) -> None:
        """All tags (TODO, FIXME, HACK, BUG, XXX, OPTIMIZE, NOTE, REFACTOR, TEMP) are found."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            content = "".join(f"// {tag}: message for {tag}\n" for tag in [
                "TODO", "FIXME", "HACK", "BUG", "XXX", "OPTIMIZE", "NOTE", "REFACTOR", "TEMP",
            ])
            (root / "tags.js").write_text(content, encoding="utf-8")
            results = _walk_todos(td)
            assert len(results["tags.js"]) == 9

    def test_binary_detection_null_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "data.bin").write_bytes(b"\x00\x01\x02\x03")
            assert _is_binary(root / "data.bin") is True

    def test_binary_detection_known_ext(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "image.jpg").write_text("not really jpg but ext matches", encoding="utf-8")
            assert _is_binary(root / "image.jpg") is True

    def test_non_binary_text_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "script.py").write_text("print('hello')", encoding="utf-8")
            assert _is_binary(root / "script.py") is False
