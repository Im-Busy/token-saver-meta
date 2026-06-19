"""Tests for prerequisites module."""
from __future__ import annotations

from pathlib import Path
from unittest import mock

from src.prerequisites import check_prerequisites


class TestPrerequisites:
    """Tests for check_prerequisites()."""

    def test_node_detected(self):
        """When node is on PATH, status is 'ok' with version and path."""
        with (
            mock.patch("src.prerequisites.shutil.which") as mock_which,
            mock.patch("src.prerequisites.subprocess.run") as mock_run,
            mock.patch("src.prerequisites._check_internet", return_value={"status": "unreachable"}),
            mock.patch("src.prerequisites._check_disk_free", return_value=100.0),
            mock.patch("src.prerequisites._check_can_write", return_value=True),
        ):
            mock_which.side_effect = lambda cmd: "/usr/bin/node" if cmd == "node" else None
            mock_run.return_value = mock.Mock(returncode=0, stdout="v22.0.0\n")

            result = check_prerequisites(Path("."))

            assert result["node"]["status"] == "ok"
            assert result["node"]["version"] == "v22.0.0"
            assert result["node"]["path"] == "/usr/bin/node"

    def test_node_missing(self):
        """When node is not on PATH, status is 'missing'."""
        with (
            mock.patch("src.prerequisites.shutil.which", return_value=None),
            mock.patch("src.prerequisites._check_internet", return_value={"status": "unreachable"}),
            mock.patch("src.prerequisites._check_disk_free", return_value=100.0),
            mock.patch("src.prerequisites._check_can_write", return_value=True),
        ):
            result = check_prerequisites(Path("."))

            assert result["node"]["status"] == "missing"
            assert result["node"]["version"] is None
            assert result["node"]["path"] is None

    def test_internet_check(self):
        """When socket connects, internet status is 'ok'."""
        with (
            mock.patch("src.prerequisites.shutil.which", return_value=None),
            mock.patch("src.prerequisites.socket.create_connection") as mock_connect,
            mock.patch("src.prerequisites._check_disk_free", return_value=100.0),
            mock.patch("src.prerequisites._check_can_write", return_value=True),
        ):
            mock_sock = mock.Mock()
            mock_connect.return_value = mock_sock

            result = check_prerequisites(Path("."))

            assert result["internet"]["status"] == "ok"

    def test_node_only_fallback(self):
        """When node+npm+npx are ok but python+uv missing, fallback is True."""
        def exe_side_effect(name: str) -> dict:
            versions = {"node": "v20.11.0", "npm": "10.2.0"}
            if name in versions:
                return {"status": "ok", "version": versions[name], "path": f"/usr/bin/{name}"}
            return {"status": "missing", "version": None, "path": None}

        with (
            mock.patch("src.prerequisites._check_executable", side_effect=exe_side_effect),
            mock.patch("src.prerequisites._check_npx", return_value={"status": "ok"}),
            mock.patch("src.prerequisites._check_internet", return_value={"status": "ok"}),
            mock.patch("src.prerequisites._check_disk_free", return_value=100.0),
            mock.patch("src.prerequisites._check_can_write", return_value=True),
        ):
            result = check_prerequisites(Path("."))

            assert result["node_only_fallback"] is True
            assert result["all_ok"] is True  # node+npm+npx are ok

    def test_all_ok(self):
        """When everything is detected, all_ok is True."""
        def exe_side_effect(name: str) -> dict:
            versions = {"node": "v20.11.0", "npm": "10.2.0", "python": "3.12.0", "uv": "0.2.0"}
            return {"status": "ok", "version": versions.get(name, "0.0.0"), "path": f"/usr/bin/{name}"}

        with (
            mock.patch("src.prerequisites._check_executable", side_effect=exe_side_effect),
            mock.patch("src.prerequisites._check_npx", return_value={"status": "ok"}),
            mock.patch("src.prerequisites._check_internet", return_value={"status": "ok"}),
            mock.patch("src.prerequisites._check_disk_free", return_value=500.0),
            mock.patch("src.prerequisites._check_can_write", return_value=True),
        ):
            result = check_prerequisites(Path("."))

            assert result["all_ok"] is True
            assert result["node_only_fallback"] is False
            assert result["node"]["status"] == "ok"
            assert result["python"]["status"] == "ok"
