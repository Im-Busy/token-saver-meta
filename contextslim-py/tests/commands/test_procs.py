"""Tests for procs_command — sorted process list."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from contextslim.commands.system.procs import procs_command


def _make_proc(pid: int, name: str, mem: float, cpu: float, status: str = "running") -> MagicMock:
    """Create a mock process with .info dict."""
    p = MagicMock()
    p.info = {"pid": pid, "name": name, "memory_percent": mem, "cpu_percent": cpu, "status": status}
    return p


class TestProcsCommand:
    """Given mocked psutil.process_iter, procs_command prints sorted processes."""

    @pytest.fixture(autouse=True)
    def _mock_psutil(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Replace psutil with a mock."""
        import sys
        sys.modules["psutil"] = MagicMock()

    def test_lists_processes_sorted(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Given 3 processes. When procs_command runs. Then sorted by memory desc."""
        import psutil
        procs = [
            _make_proc(100, "app", 2.5, 1.0),
            _make_proc(200, "chrome", 12.0, 5.5),
            _make_proc(300, "python", 3.1, 2.0),
        ]
        psutil.process_iter.return_value = procs

        procs_command(None, 30)

        out = capsys.readouterr().out
        assert "chrome" in out
        assert "python" in out
        assert "app" in out
        # chrome (12.0%) should appear before python (3.1%)
        chrome_idx = out.index("chrome")
        python_idx = out.index("python")
        app_idx = out.index("app")
        assert chrome_idx < python_idx < app_idx

    def test_filters_by_name(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Given mixed processes. When filter='python'. Then only matching shown."""
        import psutil
        procs = [
            _make_proc(100, "chrome", 5.0, 2.0),
            _make_proc(200, "python", 3.0, 1.0),
            _make_proc(300, "node", 2.0, 1.5),
        ]
        psutil.process_iter.return_value = procs

        procs_command("python", 30)

        out = capsys.readouterr().out
        assert "python" in out
        assert "chrome" not in out
        assert "node" not in out

    def test_caps_at_limit(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Given 10 processes at limit=2. Then only 2 shown."""
        import psutil
        procs = [_make_proc(i, f"proc_{i}", float(10 - i), 1.0) for i in range(10)]
        psutil.process_iter.return_value = procs

        procs_command(None, 2)

        out = capsys.readouterr().out
        assert "2 process(es) shown" in out

    def test_shows_columns(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Given a process. When procs_command runs. Then PID, Name, Mem%, CPU%, Status shown."""
        import psutil
        psutil.process_iter.return_value = [_make_proc(42, "test", 1.0, 0.5, "sleeping")]
        procs_command(None, 30)
        out = capsys.readouterr().out
        assert "42" in out
        assert "test" in out
        assert "1.0" in out
        assert "0.5" in out
        assert "sleeping" in out

    def test_psutil_missing(self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
        """Given psutil not importable. When procs_command runs. Then install hint shown."""
        import sys
        sys.modules.pop("psutil", None)
        import builtins
        orig_import = builtins.__import__
        def block_psutil(name, *args, **kwargs):  # noqa: ANN202
            if name == "psutil":
                raise ImportError("No module named 'psutil'")
            return orig_import(name, *args, **kwargs)
        monkeypatch.setattr(builtins, "__import__", block_psutil)

        procs_command(None, 30)
        out = capsys.readouterr().out
        assert "psutil not installed" in out
