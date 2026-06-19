"""Test fixtures for token-saver-meta phase 07."""

from pathlib import Path

import pytest


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory with platform detection markers."""
    markers = {
        ".kilo": True,
        "kilo.json": False,
        "CLAUDE.md": False,
        ".cursor": True,
        "opencode.json": False,
        "AGENTS.md": False,
    }
    for name, is_dir in markers.items():
        target = tmp_path / name
        if is_dir:
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.write_text("")
    return tmp_path


@pytest.fixture
def sample_mcp_config() -> dict:
    """Simulate an existing user MCP config with a non-token-saver server."""
    return {
        "mcpServers": {
            "user-server": {"command": "echo", "args": ["hello"]},
        }
    }


@pytest.fixture(scope="session")
def matrix_data() -> dict:
    """Load the platform matrix once per test session."""
    import json

    matrix_path = Path(__file__).resolve().parent.parent / "platforms" / "matrix.json"
    if matrix_path.exists():
        with open(matrix_path) as f:
            return json.load(f)
    return {}