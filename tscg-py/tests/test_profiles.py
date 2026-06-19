"""Tests for tscg.core.profiles."""

import pytest
from tscg.core.profiles import (
    ModelFamily,
    detect_model_family,
    is_thinking_model,
    Profile,
    get_profile,
)


class TestModelFamilyEnum:
    """ModelFamily enum has all 15 values."""

    def test_all_families_present(self):
        """Given: ModelFamily enum
        When: checking all members
        Then: all 15 families are present"""
        families = {m.name for m in ModelFamily}
        expected = {
            "CLAUDE", "GPT", "GEMINI", "LLAMA", "MISTRAL",
            "QWEN", "DEEPSEEK", "COHERE", "COMMAND", "YI",
            "GROK", "PHI", "GRANITE", "DBRX", "UNKNOWN",
        }
        assert families == expected


class TestDetectModelFamily:
    """detect_model_family maps model name substring → ModelFamily."""

    @pytest.mark.parametrize("model,expected", [
        # Anthropic Claude
        ("claude-3.5-sonnet", ModelFamily.CLAUDE),
        ("claude-3-opus", ModelFamily.CLAUDE),
        ("anthropic.claude-3-haiku", ModelFamily.CLAUDE),
        # OpenAI GPT
        ("gpt-4o", ModelFamily.GPT),
        ("gpt-4-turbo", ModelFamily.GPT),
        ("gpt-3.5-turbo", ModelFamily.GPT),
        ("o1", ModelFamily.GPT),
        ("o3", ModelFamily.GPT),
        ("o1-mini", ModelFamily.GPT),
        ("o1-pro", ModelFamily.GPT),
        # Google Gemini
        ("gemini-2.0-flash", ModelFamily.GEMINI),
        ("gemini-1.5-pro", ModelFamily.GEMINI),
        ("gemini-ultra", ModelFamily.GEMINI),
        # Meta Llama
        ("llama-3.1-70b", ModelFamily.LLAMA),
        ("llama-2-13b", ModelFamily.LLAMA),
        ("meta-llama-3-8b", ModelFamily.LLAMA),
        # Mistral
        ("mistral-large", ModelFamily.MISTRAL),
        ("mistral-small", ModelFamily.MISTRAL),
        ("codestral", ModelFamily.MISTRAL),
        # Qwen
        ("qwen-2.5", ModelFamily.QWEN),
        ("qwen-max", ModelFamily.QWEN),
        ("qwen2.5-coder", ModelFamily.QWEN),
        # DeepSeek
        ("deepseek-v3", ModelFamily.DEEPSEEK),
        ("deepseek-r1", ModelFamily.DEEPSEEK),
        ("deepseek-coder", ModelFamily.DEEPSEEK),
        # Cohere
        ("cohere-command-r", ModelFamily.COHERE),
        ("command-r-plus", ModelFamily.COHERE),
        # Command (distinct from Cohere)
        ("command-nightly", ModelFamily.COMMAND),
        # Yi
        ("yi-34b", ModelFamily.YI),
        ("yi-large", ModelFamily.YI),
        # Grok
        ("grok-2", ModelFamily.GROK),
        ("grok-beta", ModelFamily.GROK),
        # Phi
        ("phi-3-mini", ModelFamily.PHI),
        ("phi-3.5", ModelFamily.PHI),
        # Granite
        ("granite-3.0", ModelFamily.GRANITE),
        ("granite-code", ModelFamily.GRANITE),
        # DBRX
        ("dbrx-instruct", ModelFamily.DBRX),
    ])
    def test_known_model_detected(self, model: str, expected: ModelFamily):
        """Given: a known model name substring
        When: detect_model_family is called
        Then: returns the correct ModelFamily"""
        assert detect_model_family(model) == expected

    def test_unknown_model_returns_unknown(self):
        """Given: a model name with no known substring
        When: detect_model_family is called
        Then: returns UNKNOWN"""
        assert detect_model_family("some-random-model") == ModelFamily.UNKNOWN

    def test_empty_string_returns_unknown(self):
        """Given: an empty model name
        When: detect_model_family is called
        Then: returns UNKNOWN"""
        assert detect_model_family("") == ModelFamily.UNKNOWN

    def test_case_insensitive_match(self):
        """Given: mixed-case model name
        When: detect_model_family is called
        Then: match is case-insensitive"""
        assert detect_model_family("Claude-3.5-Sonnet") == ModelFamily.CLAUDE
        assert detect_model_family("GPT-4O") == ModelFamily.GPT
        assert detect_model_family("DeepSeek-V3") == ModelFamily.DEEPSEEK


class TestIsThinkingModel:
    """is_thinking_model identifies reasoning/thinking models."""

    @pytest.mark.parametrize("model,expected", [
        ("o1", True),
        ("o3", True),
        ("o1-mini", True),
        ("o1-pro", True),
        ("deepseek-r1", True),
        ("gpt-4o", False),
        ("claude-3.5-sonnet", False),
        ("gemini-2.0-flash", False),
        ("llama-3-70b", False),
    ])
    def test_thinking_model_detection(self, model: str, expected: bool):
        """Given: a model name
        When: is_thinking_model is called
        Then: returns True for thinking models, False otherwise"""
        assert is_thinking_model(model) == expected

    def test_thinking_match_case_insensitive(self):
        """Given: mixed-case thinking model name
        When: is_thinking_model is called
        Then: match is case-insensitive"""
        assert is_thinking_model("O1-Mini") is True
        assert is_thinking_model("DeepSeek-R1") is True


class TestProfile:
    """Profile dataclass holds per-model-family compression config."""

    def test_profile_fields(self):
        """Given: a Profile instance
        When: checking its fields
        Then: has family, chars_per_token, supports_cfl, supports_sad"""
        p = Profile(
            family=ModelFamily.CLAUDE,
            chars_per_token=3.5,
            supports_cfl=True,
            supports_sad=True,
        )
        assert p.family == ModelFamily.CLAUDE
        assert p.chars_per_token == 3.5
        assert p.supports_cfl is True
        assert p.supports_sad is True

    def test_profile_immutable(self):
        """Given: a Profile instance
        When: attempting to mutate a field
        Then: FrozenInstanceError is raised"""
        p = Profile(family=ModelFamily.GPT, chars_per_token=3.0, supports_cfl=True, supports_sad=True)
        with pytest.raises(Exception):  # FrozenInstanceError or TypeError
            p.chars_per_token = 4.0  # type: ignore[misc]


class TestGetProfile:
    """get_profile returns the correct Profile for a model name."""

    def test_claude_profile(self):
        """Given: a Claude model name
        When: get_profile is called
        Then: CFL+SAD are both supported"""
        p = get_profile("claude-3.5-sonnet")
        assert p.family == ModelFamily.CLAUDE
        assert p.supports_cfl is True
        assert p.supports_sad is True

    def test_gpt_profile(self):
        """Given: a GPT model name
        When: get_profile is called
        Then: CFL+SAD are both supported"""
        p = get_profile("gpt-4o")
        assert p.family == ModelFamily.GPT
        assert p.supports_cfl is True
        assert p.supports_sad is True

    def test_other_families_no_cfl_sad(self):
        """Given: a non-Claude, non-GPT model
        When: get_profile is called
        Then: CFL+SAD are both False"""
        for model in ["gemini-2.0-flash", "llama-3-70b", "mistral-large", "qwen-2.5"]:
            p = get_profile(model)
            assert p.supports_cfl is False, f"{model} should not support CFL"
            assert p.supports_sad is False, f"{model} should not support SAD"

    def test_chars_per_token_positive(self):
        """Given: any known model
        When: get_profile is called
        Then: chars_per_token is a positive number"""
        models = ["claude-3.5-sonnet", "gpt-4o", "gemini-2.0-flash", "llama-3-70b", "mistral-large"]
        for model in models:
            p = get_profile(model)
            assert p.chars_per_token > 0, f"{model} chars_per_token should be positive"

    def test_unknown_model_profile(self):
        """Given: an unknown model name
        When: get_profile is called
        Then: returns UNKNOWN family with conservative defaults"""
        p = get_profile("some-random-model")
        assert p.family == ModelFamily.UNKNOWN
        assert p.supports_cfl is False
        assert p.supports_sad is False
        assert p.chars_per_token > 0
