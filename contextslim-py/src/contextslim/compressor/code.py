"""Code compression utilities using regex-based signature and import extraction."""

from __future__ import annotations

import re

# Regex patterns for signature extraction
SIGNATURE_PATTERNS: list[str] = [
    r"^(?:export\s+)?(?:async\s+)?function\s+\w+",
    r"^(?:export\s+)?class\s+\w+",
    r"^(?:export\s+)?(?:const|let|var)\s+\w+\s*=",
    r"^(?:export\s+)?interface\s+\w+",
    r"^(?:export\s+)?type\s+\w+(?:<[^>]+>)?\s*=",
    r"^(?:export\s+)?enum\s+\w+",
]

IMPORT_PATTERNS: list[str] = [
    r"^import\s+.*from\s+[\"']",
    r"^const\s+.*=\s*require\(",
    r"import\s*\(\s*[\"']",
    r"^export\s+.*from\s+[\"']",
    r"=\s*require\(",
]

TYPE_PATTERNS: list[str] = [
    r"^(?:export\s+)?interface\s+\w+",
    r"^(?:export\s+)?type\s+\w+(?:<[^>]+>)?\s*=",
    r"^(?:export\s+)?enum\s+\w+",
]


def _match_any(line: str, patterns: list[str]) -> bool:
    """Return True if *line* matches any compiled pattern.

    Uses ``re.search`` so patterns without ``^`` can match mid-line
    (e.g. ``= require(...)``, ``import(...)``).
    """
    return any(re.search(pat, line) for pat in patterns)


def extract_signatures(lines: list[str]) -> list[str]:
    """Extract lines that match function/class/const/interface/type/enum declarations.

    Args:
        lines: Source code lines (with or without leading whitespace).

    Returns:
        Matching signature lines, with leading whitespace preserved.
    """
    return [ln for ln in lines if _match_any(ln.rstrip(), SIGNATURE_PATTERNS)]


def extract_imports(lines: list[str]) -> list[str]:
    """Extract lines that match import/require statements.

    Args:
        lines: Source code lines.

    Returns:
        Matching import/require lines.
    """
    return [ln for ln in lines if _match_any(ln.rstrip(), IMPORT_PATTERNS)]


def extract_types(lines: list[str]) -> list[str]:
    """Extract lines that match interface/type/enum declarations.

    Args:
        lines: Source code lines.

    Returns:
        Matching type declaration lines.
    """
    return [ln for ln in lines if _match_any(ln.rstrip(), TYPE_PATTERNS)]


# ---------------------------------------------------------------------------
# Comment stripping
# ---------------------------------------------------------------------------

# Match "//" comments — the "//" plus everything after it on the line.
_INLINE_C_STYLE = re.compile(r"//.*$", re.MULTILINE)

# Match /* ... */ block comments (lazy, spans lines).
_BLOCK_C_STYLE = re.compile(r"/\*.*?\*/", re.DOTALL)

# Match lines that are pure hash comments (Python, Ruby, Shell, etc.).
_HASH_COMMENT_LINE = re.compile(r"^[ \t]*#.*$", re.MULTILINE)

# Match inline "# ..." that comes after code (simplistic — does not
# handle # inside strings).
_HASH_COMMENT_INLINE = re.compile(r"[ \t]#[^\n]*$", re.MULTILINE)

# Match triple-quoted docstrings: """ ... """ or ''' ... ''' (lazy, spans lines).
_TRIPLE_DOUBLE = re.compile(r'""".*?"""', re.DOTALL)
_TRIPLE_SINGLE = re.compile(r"'''.*?'''", re.DOTALL)


def strip_comments(content: str, language: str = "auto") -> str:
    """Remove comments from source code.

    Supported *language* values:

    * ``"auto"`` — strip all comment forms (C-style + hash + triple-quote)
    * ``"js"``, ``"ts"``, ``"c"``, ``"cpp"``, ``"go"``, ``"rust"``, ``"java"``,
      ``"cs"`` — strip ``//`` and ``/* */``
    * ``"python"``, ``"ruby"``, ``"shell"``, ``"yaml"`` — strip ``#``
    * ``"python-docstrings"`` — strip ``#``, ``\"\"\"...\"\"\"``, ``'''...'''``

    Note:
        Heuristic only. Does not handle comments inside strings perfectly.
    """
    if language in ("auto",):
        # Strip everything.
        result = _BLOCK_C_STYLE.sub("", content)
        result = _INLINE_C_STYLE.sub("", result)
        result = _TRIPLE_DOUBLE.sub("", result)
        result = _TRIPLE_SINGLE.sub("", result)
        result = _HASH_COMMENT_LINE.sub("", result)
        result = _HASH_COMMENT_INLINE.sub("", result)
        return result

    if language in ("js", "ts", "c", "cpp", "go", "rust", "java", "cs"):
        result = _BLOCK_C_STYLE.sub("", content)
        result = _INLINE_C_STYLE.sub("", result)
        return result

    if language in ("python", "ruby", "shell", "yaml"):
        result = _HASH_COMMENT_LINE.sub("", content)
        result = _HASH_COMMENT_INLINE.sub("", result)
        return result

    if language in ("python-docstrings",):
        result = _TRIPLE_DOUBLE.sub("", content)
        result = _TRIPLE_SINGLE.sub("", result)
        result = _HASH_COMMENT_LINE.sub("", result)
        result = _HASH_COMMENT_INLINE.sub("", result)
        return result

    # Unknown language — fall back to auto.
    return strip_comments(content, "auto")
