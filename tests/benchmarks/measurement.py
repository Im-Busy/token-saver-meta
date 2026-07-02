"""Token-counting measurement library for benchmarking token-saver-meta."""

from __future__ import annotations

try:
    import tiktoken

    _ENCODER = tiktoken.get_encoding("cl100k_base")
    _HAS_TIKTOKEN = True
except ImportError:
    _ENCODER = None
    _HAS_TIKTOKEN = False


class TokenCounter:
    """Counts tokens (tikToken cl100k_base) and raw UTF-8 bytes."""

    def count_tokens(self, text: str) -> int:
        """Count tokens using tikToken cl100k_base encoding."""
        if not _HAS_TIKTOKEN:
            raise RuntimeError(
                "tikToken is not installed. Install with: pip install tiktoken"
            )
        if not text:
            return 0
        return len(_ENCODER.encode(text))

    def count_delta(self, with_text: str, without_text: str) -> dict:
        """Count token delta between two texts.

        Returns dict with keys: with_tokens, without_tokens, delta, delta_pct.
        """
        with_tokens = self.count_tokens(with_text)
        without_tokens = self.count_tokens(without_text)
        delta = with_tokens - without_tokens
        delta_pct = (delta / without_tokens * 100) if without_tokens > 0 else 0.0
        return {
            "with_tokens": with_tokens,
            "without_tokens": without_tokens,
            "delta": delta,
            "delta_pct": round(delta_pct, 2),
        }

    def count_bytes(self, text: str) -> int:
        """Count raw UTF-8 bytes."""
        return len(text.encode("utf-8"))
