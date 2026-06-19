"""Pluggable observation extraction from agent session text.

Architecture:
  - Observation: frozen dataclass for a single extracted observation.
  - ExtractionProvider: ABC for pluggable extractors (v1: keyword, future: LLM).
  - KeywordExtractionProvider: v1 implementation using keyword patterns.
  - extract_observations(): convenience entry point.

Design: provider pattern allows swapping in LLM-based extraction without
changing callers. v1 uses keyword heuristics with confidence scoring.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar


class ObservationType(str, Enum):
    """The 10 observation categories extracted from session text."""

    DECISION = "DECISION"
    BLOCKER = "BLOCKER"
    OBJECTIVE = "OBJECTIVE"
    FINDING = "FINDING"
    TODO = "TODO"
    CONVENTION = "CONVENTION"
    PATTERN = "PATTERN"
    ASSUMPTION = "ASSUMPTION"
    RISK = "RISK"
    DEPENDENCY = "DEPENDENCY"


@dataclass(frozen=True, slots=True)
class Observation:
    """A single observation extracted from agent session text.

    Attributes:
        entity_name: The entity/module/component this observation relates to.
        obs_type: Category of observation (DECISION, BLOCKER, etc.).
        content: The original text snippet from the session.
        confidence: 0.0-1.0 confidence score for the extraction quality.
    """

    entity_name: str
    obs_type: ObservationType
    content: str
    confidence: float = 1.0

    def __post_init__(self) -> None:
        """Clamp confidence to [0.0, 1.0]."""
        if self.confidence < 0.0 or self.confidence > 1.0:
            object.__setattr__(self, "confidence", max(0.0, min(1.0, self.confidence)))


# ── Extraction provider ABC ──────────────────────────────────────


class ExtractionProvider(ABC):
    """Abstract base for observation extraction providers.

    v1: KeywordExtractionProvider (heuristic patterns).
    Future: LLMExtractionProvider (prompt-based).
    """

    @abstractmethod
    def extract(self, session_text: str) -> list[Observation]:
        """Extract observations from raw session text."""
        ...


# ── Keyword-based v1 provider ────────────────────────────────────

# Pattern definitions: (regex, ObservationType, base_confidence, entity_group)
# regex: pattern to match, with named groups for content and optional entity
# base_confidence: default confidence for this pattern type
_PATTERNS: list[tuple[str, ObservationType, float, str | None]] = [
    # DECISION patterns — definitive language
    (
        r"(?:^|\n)\s*(?:Decision|decided|chose|will use|going with|going to use|settled on)[:\-]\s*(?P<content>.+?)(?:\n|$)",
        ObservationType.DECISION,
        0.9,
        None,
    ),
    (
        r"(?:we|i)\s+(?:decided|chose|settled)\s+(?:to|on)\s+(?P<content>.+?)(?:[.!]\s|\n|$)",
        ObservationType.DECISION,
        0.85,
        None,
    ),
    (
        r"(?:Decision|decided)[:\-]\s*(?P<content>.+?)(?:\n|$)",
        ObservationType.DECISION,
        0.85,
        None,
    ),
    # BLOCKER patterns
    (
        r"(?:^|\n)\s*BLOCKER[:\-]\s*(?P<content>.+?)(?:\n|$)",
        ObservationType.BLOCKER,
        0.95,
        None,
    ),
    (
        r"(?:blocked|cannot proceed|can't proceed|waiting for|stuck on)\s+(?:by\s+)?(?P<content>.+?)(?:[.!]\s|\n|$)",
        ObservationType.BLOCKER,
        0.85,
        None,
    ),
    (
        r"(?:cannot|can't)\s+(?:deploy|release|continue|move forward|proceed)\s+(?:until|without|before)\s+(?P<content>.+?)(?:[.!]\s|\n|$)",
        ObservationType.BLOCKER,
        0.9,
        None,
    ),
    # OBJECTIVE patterns
    (
        r"(?:^|\n)\s*(?:Objective|Goal|Task|Mission)[:\-]\s*(?P<content>.+?)(?:\n|$)",
        ObservationType.OBJECTIVE,
        0.9,
        None,
    ),
    (
        r"(?:need to|must|should|have to)\s+(?P<content>(?:implement|build|create|add|fix|deploy|migrate|refactor|update)\s+.+?)(?:[.!]\s|\n|$)",
        ObservationType.OBJECTIVE,
        0.7,
        None,
    ),
    # FINDING patterns
    (
        r"(?:^|\n)\s*(?:Finding|Found|Discovered|Note|Result)[:\-]\s*(?P<content>.+?)(?:\n|$)",
        ObservationType.FINDING,
        0.9,
        None,
    ),
    (
        r"(?:found that|discovered that|noted that|observed that)\s+(?P<content>.+?)(?:[.!]\s|\n|$)",
        ObservationType.FINDING,
        0.8,
        None,
    ),
    # TODO patterns
    (
        r"(?:^|\n)\s*TODO[:\-]\s*(?P<content>.+?)(?:\n|$)",
        ObservationType.TODO,
        0.95,
        None,
    ),
    (
        r"(?:pending|remaining|still need to|need to do|left to do)[:\-]?\s*(?P<content>.+?)(?:[.!]\s|\n|$)",
        ObservationType.TODO,
        0.8,
        None,
    ),
    # CONVENTION patterns
    (
        r"(?:^|\n)\s*(?:Convention|Standard|Best practice)[:\-]\s*(?P<content>.+?)(?:\n|$)",
        ObservationType.CONVENTION,
        0.9,
        None,
    ),
    (
        r"(?:always|must always|should always|we always|standard practice is to)\s+(?P<content>.+?)(?:[.!]\s|\n|$)",
        ObservationType.CONVENTION,
        0.75,
        None,
    ),
    # PATTERN patterns
    (
        r"(?:^|\n)\s*(?:Pattern|Recurring)[:\-]\s*(?P<content>.+?)(?:\n|$)",
        ObservationType.PATTERN,
        0.9,
        None,
    ),
    (
        r"(?:has happened|keeps happening|recurring|whenever|every time)\s+(?P<content>.+?)(?:[.!]\s|\n|$)",
        ObservationType.PATTERN,
        0.75,
        None,
    ),
    # ASSUMPTION patterns
    (
        r"(?:^|\n)\s*(?:Assumption|Assuming|Presume|Presuming)[:\-]\s*(?P<content>.+?)(?:\n|$)",
        ObservationType.ASSUMPTION,
        0.9,
        None,
    ),
    (
        r"(?:assuming|presuming|it's likely|probably|we assume|i assume)\s+(?:that\s+)?(?P<content>.+?)(?:[.!]\s|\n|$)",
        ObservationType.ASSUMPTION,
        0.65,
        None,
    ),
    # RISK patterns
    (
        r"(?:^|\n)\s*(?:Risk|Danger|Warning|Threat|Concern)[:\-]\s*(?P<content>.+?)(?:\n|$)",
        ObservationType.RISK,
        0.9,
        None,
    ),
    (
        r"(?:risk of|danger of|watch out for|concern is|vulnerability|single point of failure)\s+(?P<content>.+?)(?:[.!]\s|\n|$)",
        ObservationType.RISK,
        0.8,
        None,
    ),
    # DEPENDENCY patterns
    (
        r"(?:^|\n)\s*(?:Dependency|Depends on|Requires|Prerequisite|Needs)[:\-]\s*(?P<content>.+?)(?:\n|$)",
        ObservationType.DEPENDENCY,
        0.9,
        None,
    ),
    (
        r"(?:depends on|requires|needs|relies on|prerequisite for)\s+(?P<content>.+?)(?:[.!]\s|\n|$)",
        ObservationType.DEPENDENCY,
        0.8,
        None,
    ),
]

# Uncertainty-lowering words — reduce confidence when present in content
_HEDGE_WORDS: set[str] = {
    "maybe", "perhaps", "possibly", "might", "could", "not sure",
    "unsure", "tentatively", "potentially", "consider",
}

# Confidence boosters — increase confidence when present
_BOOST_WORDS: set[str] = {
    "definitively", "confirmed", "agreed", "decided", "must",
    "certain", "will", "shall", "absolutely",
}


def _detect_entity(content: str) -> str:
    """Detect a likely entity name from content using capitalization patterns.

    Returns lowercase entity name or 'unknown'.
    """
    # Find capitalized multi-word phrases (likely entity/module names)
    caps = re.findall(r"\b([A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*)\b", content)
    if caps:
        return caps[0].lower().replace(" ", "-")

    # Look for module/service patterns
    svc = re.findall(r"\b(\w+(?:-\w+)*(?:-service|-module|-layer))\b", content, re.IGNORECASE)
    if svc:
        return svc[0].lower()

    return "unknown"


def _adjust_confidence(content: str, base: float) -> float:
    """Adjust confidence based on hedge/boost words in content."""
    words = set(re.findall(r"\w+", content.lower()))
    hedges = words & _HEDGE_WORDS
    boosts = words & _BOOST_WORDS

    adjusted = base
    adjusted -= 0.15 * len(hedges)
    adjusted += 0.1 * len(boosts)

    return max(0.1, min(1.0, adjusted))


class KeywordExtractionProvider(ExtractionProvider):
    """v1: Keyword-pattern-based observation extraction.

    Uses compiled regex patterns to detect observation types in session text.
    Designed as the first pluggable provider; an LLM-based provider can
    implement the same ExtractionProvider interface for higher accuracy.
    """

    _compiled: ClassVar[list[tuple[re.Pattern[str], ObservationType, float]]] = []

    def __init__(self) -> None:
        """Compile patterns on first instantiation."""
        if not KeywordExtractionProvider._compiled:
            KeywordExtractionProvider._compiled = [
                (re.compile(pat, re.IGNORECASE | re.MULTILINE), obs_type, base_conf)
                for pat, obs_type, base_conf, _ in _PATTERNS
            ]

    def extract(self, session_text: str) -> list[Observation]:
        """Extract observations from session text using keyword patterns.

        Args:
            session_text: Raw agent conversation text.

        Returns:
            List of Observation objects, deduplicated by content.
        """
        if not session_text or not session_text.strip():
            return []

        observations: list[Observation] = []
        seen_content: set[str] = set()

        for pattern, obs_type, base_confidence in self._compiled:
            for match in pattern.finditer(session_text):
                content = match.group("content").strip()
                if not content or len(content) < 3:
                    continue

                # Deduplicate by normalized content
                norm = " ".join(content.lower().split())
                if norm in seen_content:
                    continue
                seen_content.add(norm)

                confidence = _adjust_confidence(content, base_confidence)
                entity = _detect_entity(content)

                observations.append(
                    Observation(
                        entity_name=entity,
                        obs_type=obs_type,
                        content=content,
                        confidence=round(confidence, 2),
                    )
                )

        return observations


# ── Convenience entry point ──────────────────────────────────────

_DEFAULT_PROVIDER: KeywordExtractionProvider | None = None


def extract_observations(
    session_text: str,
    *,
    provider: ExtractionProvider | None = None,
) -> list[Observation]:
    """Extract observations from agent session text.

    Uses KeywordExtractionProvider by default. Pass a custom provider
    (e.g., LLMExtractionProvider in the future) for alternative extraction.

    Args:
        session_text: Raw agent conversation text.
        provider: Optional custom extraction provider.

    Returns:
        List of Observation objects.
    """
    global _DEFAULT_PROVIDER
    if provider is not None:
        return provider.extract(session_text)
    if _DEFAULT_PROVIDER is None:
        _DEFAULT_PROVIDER = KeywordExtractionProvider()
    return _DEFAULT_PROVIDER.extract(session_text)
