"""Token-optimized compression utilities for code and database output."""

from contextslim.compressor.code import (
    SIGNATURE_PATTERNS,
    IMPORT_PATTERNS,
    TYPE_PATTERNS,
    extract_signatures,
    extract_imports,
    extract_types,
    strip_comments,
)
from contextslim.compressor.db import (
    truncate_columns,
    limit_rows,
    format_table,
)

__all__ = [
    "SIGNATURE_PATTERNS",
    "IMPORT_PATTERNS",
    "TYPE_PATTERNS",
    "extract_signatures",
    "extract_imports",
    "extract_types",
    "strip_comments",
    "truncate_columns",
    "limit_rows",
    "format_table",
]
