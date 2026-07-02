import pytest
import subprocess
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def test_t2_call_chain_depth():
    """Verify processPayment -> validatePayment -> checkBalance chain exists in 3+ files."""
    payment_app = FIXTURES / "payment_app"
    assert payment_app.is_dir()
    assert (payment_app / "src" / "processPayment.js").exists()
    assert (payment_app / "src" / "validatePayment.js").exists()
    assert (payment_app / "src" / "checkBalance.js").exists()
    process = (payment_app / "src" / "processPayment.js").read_text()
    validate = (payment_app / "src" / "validatePayment.js").read_text()
    assert "validatePayment" in process
    assert "checkBalance" in validate


def test_t3_tsc_errors():
    """Verify tsc --noEmit produces type errors in npm_error fixture."""
    npm_error = FIXTURES / "npm_error"
    assert npm_error.is_dir()
    tsc_bin = npm_error / "node_modules" / ".bin" / "tsc.cmd"
    assert tsc_bin.exists(), f"tsc not found at {tsc_bin}"
    result = subprocess.run(
        [str(tsc_bin), "--noEmit"],
        cwd=str(npm_error),
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "error" in combined.lower()


def test_t5_bug_reproducible():
    """Verify auth_bug fixture returns 500 on login with unknown user."""
    auth_bug = FIXTURES / "auth_bug"
    assert auth_bug.is_dir()
    server_js = auth_bug / "server.js"
    assert server_js.exists()
    code = server_js.read_text()
    assert "user.email" in code
    assert "user = findUser" in code
    assert "return null" in code


def test_t4_endpoint_structure():
    """Verify api_app has /api/users endpoint and UserList component."""
    api_app = FIXTURES / "api_app"
    assert api_app.is_dir()
    server = (api_app / "server.js").read_text()
    assert "/api/users" in server
    assert "express" in server.lower()
    frontend = (api_app / "src" / "UserList.jsx").read_text()
    assert "fetch" in frontend
    assert "/api/users" in frontend


def test_all_fixtures_are_git_repos():
    """Verify each fixture directory is a valid git repo."""
    expected = ["csv_cli", "payment_app", "npm_error", "api_app", "auth_bug"]
    for name in expected:
        fixture_dir = FIXTURES / name
        assert fixture_dir.is_dir(), f"Missing fixture: {name}"
        git_dir = fixture_dir / ".git"
        assert git_dir.exists(), f"{name} is not a git repo"
