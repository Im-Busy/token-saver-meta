from __future__ import annotations

import json
from pathlib import Path

import pytest

from contextslim.analyzer.stack_detector import detect_stack, StackInfo


class TestStackDetector:
    """Given a project directory with stack signal files,
    detect_stack must return the correct StackInfo."""

    def test_nodejs_detection(self, tmp_path: Path) -> None:
        """When package.json exists, detect Node.js stack."""
        (tmp_path / "package.json").write_text(json.dumps({"name": "test"}))
        (tmp_path / "index.js").write_text("console.log('hi')")

        result = detect_stack(tmp_path)

        assert result is not None
        assert result.name == "Node.js"
        assert result.language == "JavaScript"
        assert result.has_typescript is False
        assert "package.json" in result.detected_files

    def test_nodejs_with_typescript_detection(self, tmp_path: Path) -> None:
        """When tsconfig.json exists alongside package.json, detect TypeScript."""
        (tmp_path / "package.json").write_text(json.dumps({"name": "test"}))
        (tmp_path / "tsconfig.json").write_text("{}")

        result = detect_stack(tmp_path)

        assert result is not None
        assert result.name == "Node.js"
        assert result.has_typescript is True

    def test_python_pyproject_detection(self, tmp_path: Path) -> None:
        """When pyproject.toml exists, detect Python stack."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")

        result = detect_stack(tmp_path)

        assert result is not None
        assert result.name == "Python"
        assert result.language == "Python"
        assert "pyproject.toml" in result.detected_files

    def test_python_requirements_detection(self, tmp_path: Path) -> None:
        """When requirements.txt exists, detect Python stack."""
        (tmp_path / "requirements.txt").write_text("requests\nflask\n")

        result = detect_stack(tmp_path)

        assert result is not None
        assert result.name == "Python"
        assert "requirements.txt" in result.detected_files

    def test_rust_detection(self, tmp_path: Path) -> None:
        """When Cargo.toml exists, detect Rust stack."""
        (tmp_path / "Cargo.toml").write_text("[package]\nname='test'\n")

        result = detect_stack(tmp_path)

        assert result is not None
        assert result.name == "Rust"
        assert result.language == "Rust"

    def test_go_detection(self, tmp_path: Path) -> None:
        """When go.mod exists, detect Go stack."""
        (tmp_path / "go.mod").write_text("module example.com/test\n")

        result = detect_stack(tmp_path)

        assert result is not None
        assert result.name == "Go"
        assert result.language == "Go"

    def test_empty_dir_returns_none(self, tmp_path: Path) -> None:
        """When no signal files exist, return None."""
        result = detect_stack(tmp_path)
        assert result is None

    def test_non_existent_dir_returns_none(self, tmp_path: Path) -> None:
        """When directory does not exist, return None."""
        result = detect_stack(tmp_path / "nope")
        assert result is None

    def test_subdirectory_detection(self, tmp_path: Path) -> None:
        """When signal files are in a subdirectory, still detect stack."""
        sub = tmp_path / "myapp"
        sub.mkdir()
        (sub / "package.json").write_text(json.dumps({"name": "myapp"}))

        result = detect_stack(tmp_path)

        assert result is not None
        assert result.name == "Node.js"
        assert "myapp/package.json" in result.detected_files

    def test_ignored_dirs_skipped(self, tmp_path: Path) -> None:
        """Signal files inside node_modules are ignored."""
        nm = tmp_path / "node_modules"
        nm.mkdir()
        (nm / "package.json").write_text(json.dumps({"name": "dep"}))
        # But root also has package.json
        (tmp_path / "package.json").write_text(json.dumps({"name": "root"}))

        result = detect_stack(tmp_path)

        assert result is not None
        assert result.name == "Node.js"
        assert result.detected_files == ["package.json"]

    def test_framework_detection_node(self, tmp_path: Path) -> None:
        """When package.json lists React, framework is detected."""
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"react": "^18.0", "express": "^4.0"}})
        )

        result = detect_stack(tmp_path)

        assert result is not None
        assert "React" in result.frameworks
        assert "Express" in result.frameworks

    def test_framework_detection_python(self, tmp_path: Path) -> None:
        """When requirements.txt lists fastapi, framework is detected."""
        (tmp_path / "requirements.txt").write_text("fastapi==0.100.0\nuvicorn\n")

        result = detect_stack(tmp_path)

        assert result is not None
        assert "FastAPI" in result.frameworks

    def test_multiple_stacks_first_wins(self, tmp_path: Path) -> None:
        """When multiple stacks coexist, the first matched signal is primary."""
        (tmp_path / "package.json").write_text(json.dumps({"name": "test"}))
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")

        result = detect_stack(tmp_path)

        assert result is not None
        # package.json is matched first
        assert result.name == "Node.js"
        # Both files still recorded
        assert "package.json" in result.detected_files
        assert "pyproject.toml" in result.detected_files

    def test_dart_detection(self, tmp_path: Path) -> None:
        """When pubspec.yaml exists, detect Dart stack."""
        (tmp_path / "pubspec.yaml").write_text("name: test\n")

        result = detect_stack(tmp_path)

        assert result is not None
        assert result.name == "Dart"
        assert result.language == "Dart"
