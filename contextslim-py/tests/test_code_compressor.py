"""Tests for code compression utilities."""

from __future__ import annotations

import pytest
from contextslim.compressor.code import (
    extract_signatures,
    extract_imports,
    extract_types,
    strip_comments,
)


# ---------------------------------------------------------------------------
# extract_signatures
# ---------------------------------------------------------------------------

class TestExtractSignatures:
    def test_extracts_function_declarations(self) -> None:
        lines = [
            "function greet(name) {",
            "  return `Hello ${name}`",
            "}",
            "export async function fetchData(url) {",
            "  const resp = await fetch(url)",
            "}",
        ]
        result = extract_signatures(lines)
        assert result == [
            "function greet(name) {",
            "export async function fetchData(url) {",
        ]

    def test_extracts_class_declarations(self) -> None:
        lines = [
            "class User {",
            "  constructor(name) { this.name = name }",
            "}",
            "export class Admin extends User {}",
        ]
        result = extract_signatures(lines)
        assert result == [
            "class User {",
            "export class Admin extends User {}",
        ]

    def test_extracts_const_let_var(self) -> None:
        lines = [
            "const MAX = 100;",
            "let count = 0;",
            "var oldStyle = true;",
            "export const API_URL = '/api';",
        ]
        result = extract_signatures(lines)
        assert result == [
            "const MAX = 100;",
            "let count = 0;",
            "var oldStyle = true;",
            "export const API_URL = '/api';",
        ]

    def test_extracts_interface_type_enum(self) -> None:
        lines = [
            "interface Props {",
            "type ID = string;",
            "export type Status = 'ok' | 'err';",
            "enum Color { Red, Green }",
            "export enum Dir { N, S }",
        ]
        result = extract_signatures(lines)
        assert result == [
            "interface Props {",
            "type ID = string;",
            "export type Status = 'ok' | 'err';",
            "enum Color { Red, Green }",
            "export enum Dir { N, S }",
        ]

    def test_ignores_non_signature_lines(self) -> None:
        lines = [
            "// a comment",
            "  const x = 1;  // indented",
            "# python comment",
        ]
        result = extract_signatures(lines)
        assert result == []

    def test_empty_input(self) -> None:
        assert extract_signatures([]) == []


# ---------------------------------------------------------------------------
# extract_imports
# ---------------------------------------------------------------------------

class TestExtractImports:
    def test_extracts_es6_imports(self) -> None:
        lines = [
            "import React from 'react';",
            "import { useState } from 'react';",
            "import * as lib from './lib';",
        ]
        result = extract_imports(lines)
        assert result == [
            "import React from 'react';",
            "import { useState } from 'react';",
            "import * as lib from './lib';",
        ]

    def test_extracts_require_calls(self) -> None:
        lines = [
            "const fs = require('fs');",
            "const { join } = require('path');",
            "something = require('lib');",
        ]
        result = extract_imports(lines)
        assert result == [
            "const fs = require('fs');",
            "const { join } = require('path');",
            "something = require('lib');",
        ]

    def test_extracts_re_exports(self) -> None:
        lines = [
            "export { foo } from './foo';",
            "export * from './bar';",
        ]
        result = extract_imports(lines)
        assert result == [
            "export { foo } from './foo';",
            "export * from './bar';",
        ]

    def test_extracts_dynamic_import(self) -> None:
        lines = ["const mod = await import('./lazy.js');"]
        result = extract_imports(lines)
        assert result == ["const mod = await import('./lazy.js');"]

    def test_empty_input(self) -> None:
        assert extract_imports([]) == []


# ---------------------------------------------------------------------------
# extract_types
# ---------------------------------------------------------------------------

class TestExtractTypes:
    def test_extracts_interface_type_enum(self) -> None:
        lines = [
            "interface User { id: number }",
            "type ID = string;",
            "export type Resp<T> = { data: T };",
            "enum Color { Red }",
            "export enum Status { OK, ERR }",
        ]
        result = extract_types(lines)
        assert result == [
            "interface User { id: number }",
            "type ID = string;",
            "export type Resp<T> = { data: T };",
            "enum Color { Red }",
            "export enum Status { OK, ERR }",
        ]

    def test_ignores_function_class_const(self) -> None:
        lines = [
            "function f() {}",
            "class C {}",
            "const x = 1;",
        ]
        result = extract_types(lines)
        assert result == []

    def test_empty_input(self) -> None:
        assert extract_types([]) == []


# ---------------------------------------------------------------------------
# strip_comments
# ---------------------------------------------------------------------------

class TestStripComments:
    # -- auto mode -----------------------------------------------------------

    def test_auto_strips_c_style_inline(self) -> None:
        result = strip_comments("const x = 1; // inline comment")
        assert "// inline comment" not in result
        assert "const x = 1;" in result

    def test_auto_strips_block_comments(self) -> None:
        result = strip_comments("a = 1; /* block */ b = 2;")
        assert "/* block */" not in result
        assert "a = 1;" in result
        assert "b = 2;" in result

    def test_auto_strips_multiline_block(self) -> None:
        result = strip_comments("/* line1\n   line2 */ code();")
        assert "/*" not in result
        assert "line1" not in result
        assert "code();" in result

    def test_auto_strips_hash_comments(self) -> None:
        result = strip_comments("# top comment\nx = 1\ny = 2  # trailing")
        assert "# top comment" not in result
        assert "# trailing" not in result
        assert "x = 1" in result
        assert "y = 2" in result

    def test_auto_strips_triple_double_docstrings(self) -> None:
        content = '"""Module docstring.\n\nMultiline.\n"""\ndef f():\n    pass\n'
        result = strip_comments(content)
        assert '"""' not in result
        assert "def f():" in result
        assert "pass" in result

    def test_auto_strips_triple_single_docstrings(self) -> None:
        content = "'''Single-quoted docstring.'''\ndef f():\n    pass\n"
        result = strip_comments(content)
        assert "'''" not in result
        assert "def f():" in result

    # -- language-specific ---------------------------------------------------

    def test_js_only_strips_c_style(self) -> None:
        result = strip_comments(
            "// js comment\nconst x = 1;\n# not a hash comment in js", language="js"
        )
        assert "// js comment" not in result
        assert "# not a hash comment in js" in result

    def test_python_only_strips_hash(self) -> None:
        result = strip_comments(
            "# python comment\nx = 1\n// not a comment here", language="python"
        )
        assert "# python comment" not in result
        assert "// not a comment here" in result

    def test_python_docstrings_strips_hash_and_triple(self) -> None:
        content = '"""Module doc."""\n# comment\nx = 1\n'
        result = strip_comments(content, language="python-docstrings")
        assert '"""' not in result
        assert "# comment" not in result
        assert "x = 1" in result

    def test_unknown_language_falls_back_to_auto(self) -> None:
        result = strip_comments(
            "// c-style\n# hash-style", language="unknown"
        )
        assert "// c-style" not in result
        assert "# hash-style" not in result

    def test_empty_input(self) -> None:
        assert strip_comments("") == ""
