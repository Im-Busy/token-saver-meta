"""config — read config file, strip comments, redact secrets."""

from __future__ import annotations

import re
from pathlib import Path

from rich.console import Console
from rich.text import Text

from contextslim.compressor.code import (
    _BLOCK_C_STYLE,
    _HASH_COMMENT_INLINE,
    _HASH_COMMENT_LINE,
    _INLINE_C_STYLE,
)
from contextslim.compressor.text import cap_line_width

console = Console(highlight=False)

# Keys whose values should be redacted (case-insensitive substring match).
# Match any of these keyword substrings in a key name, followed by : or =.
# \w* after the keyword consumes remaining key chars (e.g. _key in secret_key).
_SECRET_KEYS: list[str] = ["api_key", "token", "secret", "password", "key"]
_SECRET_KEYS_RE = re.compile(
    r"(?:^|[^a-zA-Z0-9])("
    + "|".join(re.escape(k) for k in _SECRET_KEYS)
    + r')\w*["\']?\s*[:=]\s*',
    re.IGNORECASE,
)

# Format → comment language for compressor.code.strip_comments
_FORMAT_COMMENT_LANG: dict[str, str] = {
    ".json": "js",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "yaml",  # #-style comments
    ".ini": "yaml",   # ; and # style, treat like yaml shell
    ".env": "yaml",
    ".cfg": "yaml",
}

# Format → display name
_FORMAT_NAMES: dict[str, str] = {
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".ini": "INI",
    ".env": "ENV",
    ".cfg": "CFG",
}

REDACTED = "***REDACTED***"
MAX_LINES = 200
MAX_WIDTH = 120


def _detect_format(path: Path) -> str:
    name = path.name.lower()
    suffix = path.suffix.lower()
    # Heuristic: check filename first (env files, dotfiles)
    if name == ".env" or name.startswith(".env"):
        return ".env"
    if suffix in _FORMAT_COMMENT_LANG:
        return suffix
    if name.endswith(".cfg") or name.endswith(".ini"):
        return suffix if suffix in _FORMAT_COMMENT_LANG else ".ini"
    return suffix


def _redact_line(line: str) -> str:
    """Replace secret values for sensitive keys."""
    m = _SECRET_KEYS_RE.search(line)
    if not m:
        return line
    # Find the key span and replace everything after it
    start = m.start()
    after_key = m.end()

    # Keep the line up to the key + delimiter, append REDACTED
    prefix = line[: m.end()]
    # Look for a closing quote, bracket, or end-of-line
    remainder = line[m.end() :]
    if remainder.strip().startswith(('"', "'", "[")):
        # Quoted or bracketed value — try to find closing delimiter
        quote = remainder.lstrip()[0]
        if quote in ('"', "'"):
            # String: find closing unescaped quote
            idx = 1
            while idx < len(remainder):
                if remainder[idx] == "\\":
                    idx += 2
                    continue
                if remainder[idx] == quote:
                    return prefix + remainder[: idx + 1].replace(
                        remainder[1:idx], REDACTED
                    )
                idx += 1
            return prefix + '"' + REDACTED + '"'
        if quote == "[":
            # Array: redact entire array
            closing = remainder.find("]")
            if closing != -1:
                return prefix + f"[{REDACTED}]"
            return prefix + f"[{REDACTED}]"
        # Plain value: redact to end of line or comment
        comment_idx = remainder.find("#")
        if comment_idx != -1:
            return prefix + REDACTED + remainder[comment_idx:]
        return prefix + REDACTED
    # No quote: assume value runs to end of line or comment
    comment_idx = remainder.find("#")
    if comment_idx != -1:
        return prefix + REDACTED + remainder[comment_idx:]
    return prefix + REDACTED


def config_command(file: str) -> None:
    """Read config file, strip comments, redact secrets.

    Detects format by extension (.json, .yaml/.yml, .toml, .ini, .env).
    Strips line and block comments. Redacts values for sensitive keys.
    Caps output to *MAX_LINES* lines and *MAX_WIDTH* characters per line.
    """
    path = Path(file)
    if not path.is_file():
        console.print(f"[red]Error:[/red] File not found: {file}")
        return

    raw = path.read_text(encoding="utf-8", errors="replace")
    fmt = _detect_format(path)
    lang = _FORMAT_COMMENT_LANG.get(fmt, "auto")
    fmt_name = _FORMAT_NAMES.get(fmt, fmt.lstrip(".").upper())

    # Strip comments
    cleaned = _strip_comments_for_config(raw, lang)

    original_lines = raw.splitlines()
    cleaned_lines = cleaned.splitlines()
    comments_removed = len([ln for ln in original_lines if ln.strip()]) - len(
        [ln for ln in cleaned_lines if ln.strip()]
    )

    # Redact secrets
    redacted_lines: list[str] = []
    redacted_count = 0
    for line in cleaned_lines:
        new_line = _redact_line(line)
        if new_line != line:
            redacted_count += 1
        redacted_lines.append(new_line)

    # Cap width
    capped_lines = [cap_line_width(ln, MAX_WIDTH) for ln in redacted_lines]

    # Cap total lines
    if len(capped_lines) > MAX_LINES:
        capped_lines = capped_lines[:MAX_LINES]
        capped_lines.append(f"… [{len(capped_lines) - MAX_LINES} lines truncated]")

    # Header
    header = Text()
    header.append(path.name, style="bold cyan")
    header.append("  ", style="")
    header.append(f"({fmt_name})", style="dim")
    console.print(header)
    console.print("─" * 60, style="dim")

    # Body
    for i, ln in enumerate(capped_lines, start=1):
        console.print(f"{i:>4} │ {ln}")

    # Stats
    console.print("─" * 60, style="dim")
    parts: list[str] = [
        f"Shown {len(capped_lines)} lines.",
        f"Stripped {comments_removed} comment lines.",
    ]
    if redacted_count:
        parts.append(f"Redacted {redacted_count} secret values.")
    original_chars = sum(len(ln) for ln in original_lines)
    shown_chars = sum(len(ln) for ln in capped_lines)
    if original_chars > 0:
        save_pct = (1 - shown_chars / original_chars) * 100
        parts.append(f"Saved ~{save_pct:.0f}% tokens.")

    console.print(" ".join(parts), style="dim")


def _strip_comments_for_config(content: str, lang: str) -> str:
    """Strip comments appropriate for config file format."""
    if lang in ("js",):
        # JSON/JSONC: /* */ and //
        result = _BLOCK_C_STYLE.sub("", content)
        result = _INLINE_C_STYLE.sub("", result)
        return result
    if lang in ("yaml",):
        # YAML/TOML/INI/ENV: # comments (line and inline)
        result = _HASH_COMMENT_LINE.sub("", content)
        result = _HASH_COMMENT_INLINE.sub("", result)
        return result
    return content
