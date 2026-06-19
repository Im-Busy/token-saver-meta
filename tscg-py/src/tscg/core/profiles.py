"""Model profiles and family detection for tool schema compression."""

from __future__ import annotations

import enum
from dataclasses import dataclass


class ModelFamily(enum.Enum):
    """Model family for compression profile selection."""

    CLAUDE = "claude"
    GPT = "gpt"
    GEMINI = "gemini"
    LLAMA = "llama"
    MISTRAL = "mistral"
    QWEN = "qwen"
    DEEPSEEK = "deepseek"
    COHERE = "cohere"
    COMMAND = "command"
    YI = "yi"
    GROK = "grok"
    PHI = "phi"
    GRANITE = "granite"
    DBRX = "dbrx"
    UNKNOWN = "unknown"


_MATCH_ORDER: list[tuple[str, ModelFamily]] = [
    # Order matters: more specific patterns first to avoid false matches.
    ("command-r", ModelFamily.COHERE),   # Cohere Command-R family
    ("claude", ModelFamily.CLAUDE),
    ("gpt", ModelFamily.GPT),
    ("o1", ModelFamily.GPT),             # OpenAI o-series
    ("o3", ModelFamily.GPT),
    ("gemini", ModelFamily.GEMINI),
    ("llama", ModelFamily.LLAMA),
    ("mistral", ModelFamily.MISTRAL),
    ("codestral", ModelFamily.MISTRAL),
    ("qwen", ModelFamily.QWEN),
    ("deepseek", ModelFamily.DEEPSEEK),
    ("cohere", ModelFamily.COHERE),
    ("command", ModelFamily.COMMAND),
    ("yi", ModelFamily.YI),
    ("grok", ModelFamily.GROK),
    ("phi", ModelFamily.PHI),
    ("granite", ModelFamily.GRANITE),
    ("dbrx", ModelFamily.DBRX),
]


_THINKING_MODELS: tuple[str, ...] = (
    "o1",
    "o3",
    "r1",
)


def detect_model_family(model_name: str) -> ModelFamily:
    """Detect the model family from a model name substring.

    Args:
        model_name: The model identifier string (e.g. "claude-3.5-sonnet").

    Returns:
        The matching ModelFamily, or UNKNOWN if no match.
    """
    lower = model_name.lower()
    for pattern, family in _MATCH_ORDER:
        if pattern in lower:
            return family
    return ModelFamily.UNKNOWN


def is_thinking_model(model_name: str) -> bool:
    """Check if a model is a thinking/reasoning model.

    Thinking models (o1, o3, R1) require different compression handling
    because their reasoning tokens inflate schema output differently.

    Args:
        model_name: The model identifier string.

    Returns:
        True if the model is a thinking model.
    """
    lower = model_name.lower()
    for pattern in _THINKING_MODELS:
        if pattern in lower:
            return True
    return False


@dataclass(frozen=True)
class Profile:
    """Per-family compression profile.

    Attributes:
        family: The model family this profile applies to.
        chars_per_token: Estimated characters per token for cost estimation.
        supports_cfl: Whether Compressed Function Listing is supported.
        supports_sad: Whether Schema-Aware Deduplication is supported.
    """

    family: ModelFamily
    chars_per_token: float
    supports_cfl: bool
    supports_sad: bool


# Canonical profiles keyed by ModelFamily.
_PROFILES: dict[ModelFamily, Profile] = {
    ModelFamily.CLAUDE: Profile(
        family=ModelFamily.CLAUDE,
        chars_per_token=3.5,
        supports_cfl=True,
        supports_sad=True,
    ),
    ModelFamily.GPT: Profile(
        family=ModelFamily.GPT,
        chars_per_token=3.0,
        supports_cfl=True,
        supports_sad=True,
    ),
    ModelFamily.GEMINI: Profile(
        family=ModelFamily.GEMINI,
        chars_per_token=3.5,
        supports_cfl=False,
        supports_sad=False,
    ),
    ModelFamily.LLAMA: Profile(
        family=ModelFamily.LLAMA,
        chars_per_token=3.5,
        supports_cfl=False,
        supports_sad=False,
    ),
    ModelFamily.MISTRAL: Profile(
        family=ModelFamily.MISTRAL,
        chars_per_token=3.5,
        supports_cfl=False,
        supports_sad=False,
    ),
    ModelFamily.QWEN: Profile(
        family=ModelFamily.QWEN,
        chars_per_token=3.5,
        supports_cfl=False,
        supports_sad=False,
    ),
    ModelFamily.DEEPSEEK: Profile(
        family=ModelFamily.DEEPSEEK,
        chars_per_token=3.5,
        supports_cfl=False,
        supports_sad=False,
    ),
    ModelFamily.COHERE: Profile(
        family=ModelFamily.COHERE,
        chars_per_token=3.5,
        supports_cfl=False,
        supports_sad=False,
    ),
    ModelFamily.COMMAND: Profile(
        family=ModelFamily.COMMAND,
        chars_per_token=3.5,
        supports_cfl=False,
        supports_sad=False,
    ),
    ModelFamily.YI: Profile(
        family=ModelFamily.YI,
        chars_per_token=3.5,
        supports_cfl=False,
        supports_sad=False,
    ),
    ModelFamily.GROK: Profile(
        family=ModelFamily.GROK,
        chars_per_token=3.5,
        supports_cfl=False,
        supports_sad=False,
    ),
    ModelFamily.PHI: Profile(
        family=ModelFamily.PHI,
        chars_per_token=3.5,
        supports_cfl=False,
        supports_sad=False,
    ),
    ModelFamily.GRANITE: Profile(
        family=ModelFamily.GRANITE,
        chars_per_token=3.5,
        supports_cfl=False,
        supports_sad=False,
    ),
    ModelFamily.DBRX: Profile(
        family=ModelFamily.DBRX,
        chars_per_token=3.5,
        supports_cfl=False,
        supports_sad=False,
    ),
    ModelFamily.UNKNOWN: Profile(
        family=ModelFamily.UNKNOWN,
        chars_per_token=4.0,
        supports_cfl=False,
        supports_sad=False,
    ),
}


def get_profile(model_name: str) -> Profile:
    """Get the compression profile for a given model name.

    Args:
        model_name: The model identifier string.

    Returns:
        The Profile for the detected model family.
    """
    family = detect_model_family(model_name)
    return _PROFILES[family]
