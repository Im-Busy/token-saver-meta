"""Tests for contextslim.commands.system.packages."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from contextslim.commands.system.packages import packages_command, _extract_names


class TestExtractNames:
    """Parsing package manager output."""

    def test_extract_pip_names(self) -> None:
        """Given: pip list output. When: extract. Then: package names only."""
        raw = "Package    Version\n-------    -------\nclick      8.1.7\nrich       13.7.0\n"
        names = _extract_names(raw, "pip")
        assert names == ["click", "rich"]

    def test_extract_winget_names(self) -> None:
        """Given: winget list output. When: extract. Then: package names."""
        raw = "Name  Id                  Version\n----  --                  -------\nGit   Git.Git             2.44.0\n"
        names = _extract_names(raw, "winget")
        assert names == ["Git"]

    def test_extract_dpkg_names(self) -> None:
        """Given: dpkg -l output. When: extract. Then: names."""
        raw = "ii  bash  5.2.21  amd64  GNU Bourne Again SHell\nii  curl  8.7.1   amd64  URL transfer tool\n"
        names = _extract_names(raw, "dpkg")
        assert "bash" in names
        assert "curl" in names

    def test_extract_rpm_names(self) -> None:
        """Given: rpm -qa output. When: extract. Then: names."""
        raw = "bash\ncurl\nvim\n"
        names = _extract_names(raw, "rpm")
        assert names == ["bash", "curl", "vim"]


class TestPackagesCommand:
    """Platform-aware package listing."""

    def test_no_packages_found(self, capsys) -> None:
        """Given: no package managers. When: packages. Then: message."""
        with patch("contextslim.commands.system.packages._run_cmd", return_value=""):
            packages_command()
        out = capsys.readouterr().out
        assert "No packages" in out

    def test_filters_by_name(self, capsys) -> None:
        """Given: pip packages. When: filter 'rich'. Then: only 'rich'."""
        raw = "Package    Version\n-------    -------\nclick      8.1.7\nrich       13.7.0\n"
        with patch("contextslim.commands.system.packages._run_cmd", return_value=raw):
            packages_command(name_filter="rich")
        out = capsys.readouterr().out
        assert "rich" in out
        assert "click" not in out

    def test_filter_no_match(self, capsys) -> None:
        """Given: packages. When: filter 'zzz'. Then: 'No packages matching'."""
        raw = "Package    Version\n-------    -------\nclick    8.1.7\n"
        with patch("contextslim.commands.system.packages._run_cmd", return_value=raw):
            packages_command(name_filter="zzz")
        out = capsys.readouterr().out
        assert "No packages matching" in out
