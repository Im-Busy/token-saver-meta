"""Tests for auto_summary.py — structural summary extraction using stdlib ast."""

from __future__ import annotations

import pytest

from token_saver_mem.code_memory.auto_summary import extract_summary


class TestExtractSummary:
    """extract_summary(source_code, file_path) -> str."""

    def test_extracts_function_signature(self):
        """Given a simple function with typed params and return type."""
        source = "def add(a: int, b: int) -> int:\n    return a + b"
        result = extract_summary(source, "math.py")
        assert "function: add" in result
        assert "params: a: int, b: int" in result
        assert "returns: int" in result
        assert "module: math.py" in result

    def test_extracts_function_with_no_annotations(self):
        """Given a function without type annotations."""
        source = "def greet(name):\n    return 'Hi ' + name"
        result = extract_summary(source, "hello.py")
        assert "function: greet" in result
        assert "params: name" in result
        assert "returns: unknown" in result

    def test_extracts_function_with_no_args(self):
        """Given a function with no parameters."""
        source = "def ping() -> str:\n    return 'pong'"
        result = extract_summary(source, "status.py")
        assert "function: ping" in result
        assert "params: none" in result
        assert "returns: str" in result

    def test_extracts_function_docstring(self):
        """Given a function with a docstring."""
        source = '''def process(data: list) -> list:
    """Filter and transform data items."""
    return [x * 2 for x in data if x > 0]'''
        result = extract_summary(source, "proc.py")
        assert "docstring: Filter and transform data items." in result

    def test_truncates_long_docstring(self):
        """Given a docstring > 200 chars, it's truncated with ellipsis."""
        long_doc = "A" * 250
        source = f'def long():\n    """{long_doc}"""\n    pass'
        result = extract_summary(source, "long.py")
        assert "..." in result
        doc_part = result.split("docstring: ")[1]
        assert len(doc_part) >= 200  # at least 200 chars before truncation

    def test_extracts_class_hierarchy(self):
        """Given a class with base classes."""
        source = '''from abc import ABC

class MyService(ABC, object):
    """Service base class."""
    def run(self) -> None:
        pass'''
        result = extract_summary(source, "service.py")
        assert "class: MyService" in result
        assert "bases: ABC, object" in result
        assert "docstring: Service base class." in result
        assert "includes method: run" in result

    def test_extracts_decorators(self):
        """Given a decorated function."""
        source = '''@staticmethod
@cache
def load_config() -> dict:
    """Load configuration."""
    return {}'''
        result = extract_summary(source, "config.py")
        assert "function: load_config" in result
        assert "decorators: staticmethod, cache" in result
        assert "params: none" in result
        assert "returns: dict" in result

    def test_extracts_class_decorators(self):
        """Given a decorated class."""
        source = '''@dataclass
@frozen
class Point:
    x: float
    y: float'''
        result = extract_summary(source, "point.py")
        assert "class: Point" in result
        assert "decorators: dataclass, frozen" in result
        assert "bases: none" in result

    def test_handles_syntax_error_gracefully(self):
        """Given source with syntax error, returns error node without crashing."""
        source = "def broken(:\n    pass"
        result = extract_summary(source, "broken.py")
        assert "function: <syntax_error>" in result or "error" in result.lower()
        assert "module: broken.py" in result

    def test_handles_empty_source(self):
        """Given empty/whitespace source, returns file-only summary."""
        result = extract_summary("", "empty.py")
        assert "module: empty.py" in result

    def test_handles_source_with_only_comments(self):
        """Given source with only comments."""
        result = extract_summary("# Just a comment\n# nothing here", "comments.py")
        assert "module: comments.py" in result

    def test_deterministic_output(self):
        """Given same input twice, produces identical output."""
        source = "def foo(x: int) -> str:\n    return str(x)"
        r1 = extract_summary(source, "a.py")
        r2 = extract_summary(source, "a.py")
        assert r1 == r2

    def test_async_function(self):
        """Given an async function, extracts correctly."""
        source = '''async def fetch(url: str) -> bytes:
    """Fetch URL content."""
    return b""'''
        result = extract_summary(source, "net.py")
        assert "function: fetch" in result
        assert "params: url: str" in result
        assert "returns: bytes" in result
        assert "docstring: Fetch URL content." in result

    def test_multiple_top_level_defs(self):
        """Given a module with multiple definitions, includes all."""
        source = '''def func_a() -> int:
    return 1

class MyClass:
    def method_b(self) -> str:
        return "b"'''
        result = extract_summary(source, "multi.py")
        assert "function: func_a" in result
        assert "class: MyClass" in result
        assert "includes method: method_b" in result
