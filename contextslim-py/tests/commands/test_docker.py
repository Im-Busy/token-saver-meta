"""Tests for contextslim.commands.system.docker."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from contextslim.commands.system.docker import docker_command, _docker_available


class TestDockerAvailable:
    """Docker presence detection."""

    def test_docker_present(self) -> None:
        """Given: docker on PATH. When: check. Then: True."""
        with patch("subprocess.run", return_value=None):
            assert _docker_available() is True

    def test_docker_missing(self) -> None:
        """Given: docker not on PATH. When: check. Then: False."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert _docker_available() is False


class TestDockerCommand:
    """Docker containers and images display."""

    def test_docker_not_available(self, capsys) -> None:
        """Given: no Docker. When: docker. Then: 'not available' message."""
        with patch(
            "contextslim.commands.system.docker._docker_available",
            return_value=False,
        ):
            docker_command()
        out = capsys.readouterr().out
        assert "not available" in out

    def test_no_containers_or_images(self, capsys) -> None:
        """Given: Docker available, nothing running. When: docker. Then: empty."""
        with patch(
            "contextslim.commands.system.docker._docker_available",
            return_value=True,
        ), patch(
            "contextslim.commands.system.docker._run_docker",
            return_value="",
        ):
            docker_command()
        out = capsys.readouterr().out
        assert "no running containers" in out
        assert "no images" in out

    def test_shows_containers(self, capsys) -> None:
        """Given: running containers. When: docker. Then: listed."""
        containers = "myapp\tnginx:alpine\tUp 2 hours\t0.0.0.0:8080->80/tcp"
        with patch(
            "contextslim.commands.system.docker._docker_available",
            return_value=True,
        ), patch(
            "contextslim.commands.system.docker._run_docker",
            side_effect=[containers, ""],
        ):
            docker_command()
        out = capsys.readouterr().out
        assert "myapp" in out
        assert "nginx:alpine" in out
        assert "Up 2 hours" in out

    def test_shows_images(self, capsys) -> None:
        """Given: Docker images. When: docker. Then: listed."""
        images = "python\t3.12-slim\t150MB\t2024-01-15 10:00"
        with patch(
            "contextslim.commands.system.docker._docker_available",
            return_value=True,
        ), patch(
            "contextslim.commands.system.docker._run_docker",
            side_effect=["", images],
        ):
            docker_command()
        out = capsys.readouterr().out
        assert "no running containers" in out
        assert "python" in out
        assert "3.12-slim" in out

    def test_filters_by_name(self, capsys) -> None:
        """Given: multiple containers. When: filter 'web'. Then: only web shown."""
        containers = "web-app\tnginx:alpine\tUp 1h\t80/tcp\ndb-svc\tpostgres:16\tUp 2h\t5432/tcp"
        images = "nginx\tlatest\t100MB\t2024-01-01\npostgres\t16\t300MB\t2024-01-01"
        with patch(
            "contextslim.commands.system.docker._docker_available",
            return_value=True,
        ), patch(
            "contextslim.commands.system.docker._run_docker",
            side_effect=[containers, images],
        ):
            docker_command(name_filter="web")
        out = capsys.readouterr().out
        assert "web-app" in out
        assert "db-svc" not in out
