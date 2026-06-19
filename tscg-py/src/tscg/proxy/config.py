"""
Proxy configuration from environment variables.

Maps to the TS @tscg/mcp-proxy src/config.ts semantics,
adapted for Python + simplified downstream URL model.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

_VALID_PROFILES = frozenset({"conservative", "balanced", "aggressive", "auto"})


@dataclass(frozen=True)
class ProxyConfig:
    """Configuration for the TSCG MCP Proxy.

    Attributes:
        model: Target model name for tokenizer alignment (default "auto").
        profile: Compression profile name (conservative/balanced/aggressive/auto) or None.
        downstream_url: URL of the downstream MCP server, or None.
        max_tools: Maximum number of tools to proxy.
    """

    model: str = "auto"
    profile: str | None = None
    downstream_url: str | None = None
    max_tools: int = 200


def get_config() -> ProxyConfig:
    """Parse proxy configuration from environment variables.

    ENV variables:
        TSCG_MODEL          — Model target (default "auto")
        TSCG_PROFILE        — Compression profile (None = use auto-resolve)
        TSCG_DOWNSTREAM_URL — Downstream MCP server URL (default None)
        TSCG_MAX_TOOLS      — Max tools to proxy (default 200)

    Returns:
        Frozen ProxyConfig dataclass.

    Raises:
        ValueError: If TSCG_PROFILE is set to an invalid value.
    """
    model = os.environ.get("TSCG_MODEL", "auto")

    profile_raw = os.environ.get("TSCG_PROFILE")
    profile: str | None = None
    if profile_raw is not None:
        profile_raw = profile_raw.strip()
        if profile_raw.lower() not in _VALID_PROFILES:
            raise ValueError(
                f"Invalid TSCG_PROFILE: '{profile_raw}'. "
                f"Must be one of: {', '.join(sorted(_VALID_PROFILES))}."
            )
        profile = profile_raw.lower()

    downstream_url = os.environ.get("TSCG_DOWNSTREAM_URL") or None

    max_tools_raw = os.environ.get("TSCG_MAX_TOOLS", "200")
    try:
        max_tools = int(max_tools_raw)
    except (ValueError, TypeError):
        max_tools = 200

    return ProxyConfig(
        model=model,
        profile=profile,
        downstream_url=downstream_url,
        max_tools=max_tools,
    )
