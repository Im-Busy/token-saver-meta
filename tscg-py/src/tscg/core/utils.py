"""Token estimation and diff utilities."""

from __future__ import annotations

import math

try:
    import tiktoken

    _HAS_TIKTOKEN = True
except ImportError:
    _HAS_TIKTOKEN = False


def estimate_tokens(text: str) -> int:
    """Estimate token count for a text string.

    Uses tiktoken with cl100k_base encoding if available,
    otherwise falls back to a chars/4 heuristic with ceil rounding.

    Args:
        text: The text to estimate tokens for.

    Returns:
        Estimated token count (always >= 0).
    """
    if not text:
        return 0

    if _HAS_TIKTOKEN:
        try:
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except Exception:
            pass  # Fall through to heuristic on any tiktoken error.

    return math.ceil(len(text) / 4)


def estimate_diff(
    before: int | str,
    after: int | str,
) -> float:
    """Calculate percentage token savings from before to after.

    Args:
        before: Token count (int) or text (str) before compression.
        after: Token count (int) or text (str) after compression.

    Returns:
        Savings percentage: positive = savings, negative = expansion.
        0.0 if before is 0 to avoid division by zero.
    """
    before_tokens = before if isinstance(before, int) else estimate_tokens(before)
    after_tokens = after if isinstance(after, int) else estimate_tokens(after)

    if before_tokens == 0:
        return 0.0

    return (before_tokens - after_tokens) / before_tokens * 100.0
