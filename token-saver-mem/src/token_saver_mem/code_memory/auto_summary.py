"""auto_summary.py — structural summary extraction using stdlib ast (no tree-sitter).

Ported from Loom's indexer/extractor.py. Python-only v1 — no C extensions.
"""

from __future__ import annotations

import ast
from typing import Any


def _safe_parse(source: str) -> ast.Module | None:
    """Parse Python source, returning None on syntax errors."""
    try:
        return ast.parse(source)
    except SyntaxError:
        return None


def _get_decorator_names(node: ast.FunctionDef | ast.ClassDef | ast.AsyncFunctionDef) -> list[str]:
    """Extract decorator names from a function or class definition."""
    names: list[str] = []
    for dec in node.decorator_list:
        if isinstance(dec, ast.Name):
            names.append(dec.id)
        elif isinstance(dec, ast.Attribute):
            parts: list[str] = []
            current: Any = dec
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            names.append(".".join(reversed(parts)))
        elif isinstance(dec, ast.Call):
            if isinstance(dec.func, ast.Name):
                names.append(dec.func.id)
            elif isinstance(dec.func, ast.Attribute):
                names.append(dec.func.attr)
        else:
            names.append(type(dec).__name__)
    return names


def _extract_params(args: ast.arguments) -> str:
    """Extract parameter names with annotations."""
    params: list[str] = []
    # Positional args (including args with defaults)
    defaults_start = len(args.args) - len(args.defaults)
    for i, arg in enumerate(args.args):
        name = arg.arg
        annotation = ""
        if arg.annotation:
            annotation = f": {ast.unparse(arg.annotation)}"
        if i >= defaults_start:
            default_idx = i - defaults_start
            default_val = ast.unparse(args.defaults[default_idx])
            params.append(f"{name}{annotation}={default_val}")
        else:
            params.append(f"{name}{annotation}")

    # *args (vararg)
    if args.vararg:
        name = f"*{args.vararg.arg}"
        if args.vararg.annotation:
            name += f": {ast.unparse(args.vararg.annotation)}"
        params.append(name)

    # Keyword-only args
    for kw in args.kwonlyargs:
        name = kw.arg
        if kw.annotation:
            name += f": {ast.unparse(kw.annotation)}"
        params.append(name)

    # **kwargs
    if args.kwarg:
        name = f"**{args.kwarg.arg}"
        if args.kwarg.annotation:
            name += f": {ast.unparse(args.kwarg.annotation)}"
        params.append(name)

    return ", ".join(params) if params else "none"


def _get_docstring(node: ast.FunctionDef | ast.ClassDef | ast.AsyncFunctionDef | ast.Module) -> str | None:
    """Extract the docstring from a node, if present."""
    if not isinstance(node, ast.Module) and hasattr(node, "body"):
        body = node.body
    elif isinstance(node, ast.Module):
        body = node.body
    else:
        return None

    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        return body[0].value.value.strip()
    return None


def extract_summary(source: str, file_path: str) -> str:
    """Extract a structured text summary from Python source code using ast stdlib.

    No LLM, no tree-sitter, no C extensions. Purely static metadata extraction.

    Args:
        source: Python source code as a string.
        file_path: Absolute or relative path to the file (for module naming).

    Returns:
        Multi-line string summary. Returns error node for syntax errors,
        file-only summary for empty/non-Python sources.
    """
    tree = _safe_parse(source)

    lines: list[str] = []

    if tree is None:
        lines.append("function: <syntax_error>")
        lines.append(f"module: {file_path}")
        return "\n".join(lines)

    # Extract module-level docstring
    if tree.body and isinstance(tree.body[0], ast.Expr):
        doc = _get_docstring(tree)
        if doc:
            lines.append(f"module docstring: {doc[:200]}{'...' if len(doc) > 200 else ''}")

    # Walk top-level nodes
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _extract_function(node, lines, file_path)
        elif isinstance(node, ast.ClassDef):
            _extract_class(node, lines, file_path)

    if not lines:
        lines.append(f"file: {file_path}")

    lines.append(f"module: {file_path}")
    return "\n".join(lines)


def _extract_function(node: ast.FunctionDef | ast.AsyncFunctionDef, lines: list[str], file_path: str) -> None:
    """Append function summary lines."""
    prefix = "async function" if isinstance(node, ast.AsyncFunctionDef) else "function"
    lines.append(f"{prefix}: {node.name}")

    decorators = _get_decorator_names(node)
    if decorators:
        lines.append(f"decorators: {', '.join(decorators)}")

    params = _extract_params(node.args)
    lines.append(f"params: {params}")

    if node.returns:
        lines.append(f"returns: {ast.unparse(node.returns)}")
    else:
        lines.append("returns: unknown")

    doc = _get_docstring(node)
    if doc:
        truncated = doc if len(doc) <= 200 else doc[:200] + "..."
        lines.append(f"docstring: {truncated}")


def _extract_class(node: ast.ClassDef, lines: list[str], file_path: str) -> None:
    """Append class summary lines."""
    lines.append(f"class: {node.name}")

    decorators = _get_decorator_names(node)
    if decorators:
        lines.append(f"decorators: {', '.join(decorators)}")

    bases = [ast.unparse(b) for b in node.bases] if node.bases else []
    lines.append(f"bases: {', '.join(bases)}" if bases else "bases: none")

    doc = _get_docstring(node)
    if doc:
        truncated = doc if len(doc) <= 200 else doc[:200] + "..."
        lines.append(f"docstring: {truncated}")

    # Extract methods
    for member in node.body:
        if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
            prefix = "async method" if isinstance(member, ast.AsyncFunctionDef) else "method"
            lines.append(f"includes {prefix}: {member.name}")
