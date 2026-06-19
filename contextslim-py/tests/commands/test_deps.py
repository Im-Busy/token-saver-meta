"""Tests for contextslim.commands.code.deps."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from contextslim.commands.code.deps import (
    _collect_deps,
    _parse_cargo_toml,
    _parse_go_mod,
    _parse_package_json,
    _parse_pyproject_toml,
)


# ============================================================================
# package.json
# ============================================================================


class TestParsePackageJson:
    def test_deps_and_dev_deps(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pkg = root / "package.json"
            pkg.write_text(json.dumps({
                "dependencies": {"react": "^18.0", "lodash": "4.17.21"},
                "devDependencies": {"jest": "^29.0", "typescript": "5.0"},
            }), encoding="utf-8")
            groups = _parse_package_json(pkg)
            assert groups["dependencies"] == ["lodash", "react"]
            assert groups["devDependencies"] == ["jest", "typescript"]

    def test_no_deps(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pkg = root / "package.json"
            pkg.write_text(json.dumps({"name": "foo"}), encoding="utf-8")
            groups = _parse_package_json(pkg)
            assert groups == {}

    def test_missing_file(self) -> None:
        groups = _parse_package_json(Path("/nonexistent/package.json"))
        assert groups == {}

    def test_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pkg = root / "package.json"
            pkg.write_text("not json", encoding="utf-8")
            groups = _parse_package_json(pkg)
            assert groups == {}


# ============================================================================
# pyproject.toml
# ============================================================================


class TestParsePyprojectToml:
    def test_pep621_deps(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "pyproject.toml"
            manifest.write_text("""\
[project]
name = "test"
dependencies = [
    "rich>=13.0",
    "click~=8.0",
    "psutil",
]
""", encoding="utf-8")
            groups = _parse_pyproject_toml(manifest)
            assert groups["dependencies"] == ["click", "psutil", "rich"]

    def test_optional_deps(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "pyproject.toml"
            manifest.write_text("""\
[project]
name = "test"
dependencies = ["requests"]

[project.optional-dependencies]
db = ["pymysql>=1.0", "psycopg2-binary"]
test = ["pytest"]
""", encoding="utf-8")
            groups = _parse_pyproject_toml(manifest)
            assert groups["dependencies"] == ["requests"]
            assert groups["optional:db"] == ["psycopg2-binary", "pymysql"]
            assert groups["optional:test"] == ["pytest"]

    def test_no_deps(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "pyproject.toml"
            manifest.write_text('[project]\nname = "bare"\n', encoding="utf-8")
            groups = _parse_pyproject_toml(manifest)
            assert groups == {}

    def test_missing_file(self) -> None:
        groups = _parse_pyproject_toml(Path("/nonexistent/pyproject.toml"))
        assert groups == {}


# ============================================================================
# Cargo.toml
# ============================================================================


class TestParseCargoToml:
    def test_deps_and_build_deps(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "Cargo.toml"
            manifest.write_text("""\
[package]
name = "test"

[dependencies]
serde = "1.0"
tokio = { version = "1.0", features = ["full"] }

[dev-dependencies]
criterion = "0.4"

[build-dependencies]
cc = "1.0"
""", encoding="utf-8")
            groups = _parse_cargo_toml(manifest)
            assert groups["dependencies"] == ["serde", "tokio"]
            assert groups["dev-dependencies"] == ["criterion"]
            assert groups["build-dependencies"] == ["cc"]

    def test_no_deps(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "Cargo.toml"
            manifest.write_text('[package]\nname = "bare"\n', encoding="utf-8")
            groups = _parse_cargo_toml(manifest)
            assert groups == {}

    def test_missing_file(self) -> None:
        groups = _parse_cargo_toml(Path("/nonexistent/Cargo.toml"))
        assert groups == {}


# ============================================================================
# go.mod
# ============================================================================


class TestParseGoMod:
    def test_require_block(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "go.mod"
            manifest.write_text("""\
module example.com/app

go 1.21

require (
    github.com/gin-gonic/gin v1.9.0
    github.com/lib/pq v1.10.7
    golang.org/x/sync v0.5.0
)
""", encoding="utf-8")
            groups = _parse_go_mod(manifest)
            assert groups["require"] == [
                "github.com/gin-gonic/gin",
                "github.com/lib/pq",
                "golang.org/x/sync",
            ]

    def test_single_line_require(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "go.mod"
            manifest.write_text("""\
module example.com/app

go 1.21

require github.com/gorilla/mux v1.8.0
""", encoding="utf-8")
            groups = _parse_go_mod(manifest)
            assert groups["require"] == ["github.com/gorilla/mux"]

    def test_no_require(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "go.mod"
            manifest.write_text("module example.com/app\n\ngo 1.21\n", encoding="utf-8")
            groups = _parse_go_mod(manifest)
            assert groups == {}

    def test_missing_file(self) -> None:
        groups = _parse_go_mod(Path("/nonexistent/go.mod"))
        assert groups == {}


# ============================================================================
# _collect_deps (integration)
# ============================================================================


class TestCollectDeps:
    def test_no_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            collected = _collect_deps(td)
            assert collected == {}

    def test_multiple_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # package.json
            (root / "package.json").write_text(json.dumps({
                "dependencies": {"express": "4.18.2"},
            }), encoding="utf-8")
            # pyproject.toml
            (root / "pyproject.toml").write_text("""\
[project]
name = "test"
dependencies = ["fastapi>=0.100"]
""", encoding="utf-8")
            collected = _collect_deps(td)
            assert "npm" in collected
            assert "pip" in collected
            assert collected["npm"]["dependencies"] == ["express"]
            assert collected["pip"]["dependencies"] == ["fastapi"]
