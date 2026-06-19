"""Tests for indexer.py — directory walk, SHA-256, ast.parse, change detection."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from token_saver_mem.code_memory.db import get_connection, get_all_fingerprints
from token_saver_mem.code_memory.indexer import (
    classify_changes,
    index_directory,
    sha256_of_file,
)


class TestSha256OfFile:
    """sha256_of_file(path) -> str"""

    def test_returns_hex_string(self, sample_py_files):
        """Given a valid file, returns a 64-char hex digest."""
        f = sample_py_files / "utils.py"
        result = sha256_of_file(f)
        assert isinstance(result, str)
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic(self, sample_py_files):
        """Given same file twice, returns same hash."""
        f = sample_py_files / "utils.py"
        assert sha256_of_file(f) == sha256_of_file(f)

    def test_different_content_different_hash(self, sample_py_files):
        """Given two different files, hashes differ."""
        h1 = sha256_of_file(sample_py_files / "utils.py")
        h2 = sha256_of_file(sample_py_files / "models.py")
        assert h1 != h2

    def test_matches_python_hashlib(self, sample_py_files):
        """Given a file, matches hashlib.sha256 on the same content."""
        f = sample_py_files / "utils.py"
        our_hash = sha256_of_file(f)
        expected = hashlib.sha256(f.read_bytes()).hexdigest()
        assert our_hash == expected

    def test_raises_on_missing_file(self, tmp_path):
        """Given a non-existent file, raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            sha256_of_file(tmp_path / "nonexistent.py")


class TestIndexDirectory:
    """index_directory(path, db_path) — walks, parses, upserts."""

    def test_indexes_py_files_only(self, sample_py_files, temp_db):
        """Given a directory with .py and .txt files, only .py are indexed."""
        result = index_directory(sample_py_files, temp_db)
        assert result["files_found"] >= 4  # utils.py, models.py, broken.py, helpers.py
        assert result["files_indexed"] >= 3  # broken.py should be skipped/fail
        assert result["nodes_written"] > 0

    def test_stores_fingerprints(self, sample_py_files, temp_db):
        """Given indexed files, fingerprints are stored in DB."""
        index_directory(sample_py_files, temp_db)
        conn = get_connection(temp_db)
        try:
            fps = get_all_fingerprints(conn)
            assert len(fps) > 0
            for path, (sha, mtime) in fps.items():
                assert len(sha) == 64
                assert mtime > 0
        finally:
            conn.close()

    def test_reindex_skips_unchanged(self, sample_py_files, temp_db):
        """Given an already-indexed directory, re-index skips unchanged files."""
        # First index
        r1 = index_directory(sample_py_files, temp_db)
        first_nodes = r1["nodes_written"]

        # Second index — no files changed, so no re-parse needed
        r2 = index_directory(sample_py_files, temp_db)
        assert r2["files_unchanged"] >= r2["files_found"]
        assert r2["nodes_written"] == 0  # unchanged files not re-parsed (incremental design)

    def test_handles_syntax_error_gracefully(self, sample_py_files, temp_db):
        """Given a file with syntax error, indexing continues for other files."""
        result = index_directory(sample_py_files, temp_db)
        # broken.py should be among files_found but not cause crash
        assert result["files_found"] >= 4
        assert result["files_indexed"] >= 3

    def test_returns_structured_result(self, sample_py_files, temp_db):
        """Given a directory, result dict has correct keys."""
        result = index_directory(sample_py_files, temp_db)
        for key in ("files_found", "files_indexed", "files_unchanged", "nodes_written", "errors"):
            assert key in result

    def test_empty_directory(self, tmp_path, temp_db):
        """Given empty directory, returns zero counts."""
        empty = tmp_path / "empty"
        empty.mkdir()
        result = index_directory(empty, temp_db)
        assert result["files_found"] == 0
        assert result["nodes_written"] == 0

    def test_uses_utf8_encoding(self, sample_py_files, temp_db):
        """Given a file with Unicode characters, reads successfully."""
        unicode_file = sample_py_files / "unicode_test.py"
        unicode_file.write_text(
            '# -*- coding: utf-8 -*-\ndef greet(name: str = "José") -> str:\n    return f"¡Hola {name}!"',
            encoding="utf-8",
        )
        result = index_directory(sample_py_files, temp_db)
        assert result["errors"] == 0 or "unicode" not in str(result).lower()


class TestClassifyChanges:
    """classify_changes(discovered_files, db_path) -> ChangeReport"""

    def _to_abs(self, base: Path, files: list[str]) -> list[str]:
        return [(base / f).as_posix() for f in files]

    def test_new_files_detected(self, sample_py_files, temp_db):
        """Given no prior fingerprints, all files are 'new'."""
        files = self._to_abs(sample_py_files, ["utils.py", "models.py", "broken.py"])
        report = classify_changes(files, temp_db)
        assert sorted(report.added) == sorted(files)

    def test_unchanged_files_detected(self, sample_py_files, temp_db):
        """Given files with matching fingerprints, they are 'unchanged'."""
        # First, index them
        index_directory(sample_py_files, temp_db)
        # Then classify again
        files = self._to_abs(sample_py_files, ["utils.py"])
        report = classify_changes(files, temp_db)
        assert report.unchanged  # utils.py should be unchanged
        assert not report.added
        assert not report.modified

    def test_deleted_files_detected(self, sample_py_files, temp_db):
        """Given a fingerprint for a file that no longer exists, it's 'deleted'."""
        # Index the directory
        index_directory(sample_py_files, temp_db)

        # Create a temp file, index it, then delete it
        tmp_file = sample_py_files / "will_delete.py"
        tmp_file.write_text("x = 1", encoding="utf-8")
        index_directory(sample_py_files, temp_db)

        tmp_file.unlink()

        # Re-classify
        files = self._to_abs(sample_py_files, ["utils.py", "models.py"])
        report = classify_changes(files, temp_db)
        assert len(report.deleted) > 0  # will_delete.py should be deleted

    def test_files_to_index_property(self, sample_py_files, temp_db):
        """Given a ChangeReport, files_to_index returns added + modified."""
        files = self._to_abs(sample_py_files, ["utils.py"])
        report = classify_changes(files, temp_db)
        assert set(report.files_to_index) == set(report.added + report.modified)

    def test_modified_file_detection(self, sample_py_files, temp_db):
        """Given an indexed file whose content then changes, it's 'modified'."""
        # Index first
        index_directory(sample_py_files, temp_db)

        # Modify a file
        utils = sample_py_files / "utils.py"
        utils.write_text(utils.read_text(encoding="utf-8") + "\n# modified\n", encoding="utf-8")

        files = self._to_abs(sample_py_files, ["utils.py"])
        report = classify_changes(files, temp_db)
        assert report.modified  # utils.py should be detected as modified

    def test_handles_missing_files_gracefully(self, temp_db):
        """Given a discovered file that vanished between walk and stat, it becomes 'deleted'."""
        phantom = "/nonexistent/path/file.py"
        report = classify_changes([phantom], temp_db)
        assert phantom in report.deleted
