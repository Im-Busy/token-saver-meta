"""Development environment prerequisite checker for token-saver-meta."""
from __future__ import annotations

import shutil
import socket
import subprocess
import tempfile
from pathlib import Path


def _check_executable(name: str) -> dict:
    """Check if an executable exists via shutil.which and capture its --version output."""
    path = shutil.which(name)
    if path is None:
        return {"status": "missing", "version": None, "path": None}

    try:
        result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version = result.stdout.strip().split("\n")[0]
            return {"status": "ok", "version": version, "path": path}
        return {"status": "error", "version": result.stderr.strip(), "path": path}
    except (subprocess.TimeoutExpired, OSError):
        return {"status": "error", "version": None, "path": path}


def _check_npx() -> dict:
    """Check if npx is available."""
    path = shutil.which("npx")
    return {"status": "ok"} if path else {"status": "missing"}


def _check_internet() -> dict:
    """Check internet connectivity by connecting to pypi.org:443."""
    try:
        sock = socket.create_connection(("pypi.org", 443), timeout=5)
        sock.close()
        return {"status": "ok"}
    except OSError:
        return {"status": "unreachable"}


def _check_disk_free(project_path: Path) -> float:
    """Return free disk space in MB."""
    usage = shutil.disk_usage(project_path)
    return round(usage.free / (1024 * 1024), 1)


def _check_can_write(project_path: Path) -> bool:
    """Check if we can write to the project directory."""
    try:
        with tempfile.NamedTemporaryFile(dir=str(project_path), delete=True) as f:
            f.write(b"test")
        return True
    except OSError:
        return False


def check_prerequisites(project_path: Path) -> dict:
    """Check all prerequisites for token-saver-meta.

    Returns a dict with status for each prerequisite: node, npm, npx, python, uv, internet,
    disk_free_mb, can_write, plus computed fields all_ok, node_only_fallback, and issues.
    """
    node = _check_executable("node")
    npm = _check_executable("npm")
    npx = _check_npx()
    python = _check_executable("python")
    uv = _check_executable("uv")
    internet = _check_internet()
    disk_free_mb = _check_disk_free(project_path)
    can_write = _check_can_write(project_path)

    issues: list[str] = []

    if node["status"] != "ok":
        issues.append("Node.js not found. Install from https://nodejs.org")
    if npm["status"] != "ok":
        issues.append("npm not found. Install Node.js from https://nodejs.org")
    if npx["status"] != "ok":
        issues.append("npx not found. Install Node.js from https://nodejs.org")
    if python["status"] != "ok":
        issues.append("Python not found. Install from https://python.org")
    if uv["status"] != "ok":
        issues.append("uv not found. Install with: pip install uv")
    if internet["status"] != "ok":
        issues.append("No internet connection. Check network settings.")
    if not can_write:
        issues.append(f"Cannot write to {project_path}")

    node_ok = node["status"] == "ok"
    python_ok = python["status"] == "ok"
    uv_ok = uv["status"] == "ok"

    node_only_fallback = (
        node_ok
        and npm["status"] == "ok"
        and npx["status"] == "ok"
        and not python_ok
        and not uv_ok
    )

    all_ok = node_ok and npm["status"] == "ok" and npx["status"] == "ok"

    return {
        "node": node,
        "npm": npm,
        "npx": npx,
        "python": python,
        "uv": uv,
        "internet": internet,
        "disk_free_mb": disk_free_mb,
        "can_write": can_write,
        "all_ok": all_ok,
        "node_only_fallback": node_only_fallback,
        "issues": issues,
    }
