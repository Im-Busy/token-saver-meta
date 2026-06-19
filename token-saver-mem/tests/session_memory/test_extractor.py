"""Tests for session_memory.extractor — pluggable observation extraction."""

from __future__ import annotations

import pytest

from token_saver_mem.session_memory.extractor import (
    ExtractionProvider,
    KeywordExtractionProvider,
    Observation,
    ObservationType,
    extract_observations,
)

# ── dummy session texts ──────────────────────────────────────────

SESSION_WITH_ALL_TYPES = """
Objective: Implement user authentication with JWT tokens.

I decided to use bcrypt for password hashing. The database schema will store hashed passwords only.

BLOCKER: Waiting for the security team to approve the JWT key rotation policy. Cannot proceed without this.

TODO: Add rate limiting to login endpoint. TODO: Write integration tests for the auth flow.

Finding: The existing user table has 3M rows so migration will take ~20 minutes during off-peak.

Convention: All API endpoints must return JSON with {status, data, error} envelope.

Pattern: Whenever we add a new model, we also need to update the admin panel — this has happened 5 times now.

Assuming the load balancer health checks will remain at /health — this could change.

Risk: If the JWT secret leaks, all sessions are compromised immediately — need key rotation infrastructure.

This module depends on the crypto-service for token generation and the email-service for password resets.

Decision: We'll deploy to staging on Friday, monitor for 48h, then to production on Monday.
"""

SESSION_EMPTY = ""

SESSION_SIMPLE = "TODO: fix the login bug. It seems to be related to session expiry."

SESSION_LOW_CONFIDENCE = "TODO: maybe we should think about adding some kind of caching layer? not sure yet. Possibly we could add rate limiting too but unsure."


# ── tests ────────────────────────────────────────────────────────

class TestExtractObservations:
    """extract_observations() integration tests."""

    def test_extracts_all_10_observation_types(self) -> None:
        """Given a session with all 10 observation types, When extracted, Then all types detected."""
        observations = extract_observations(SESSION_WITH_ALL_TYPES)
        types_found = {obs.obs_type for obs in observations}
        expected = set(ObservationType)
        missing = expected - types_found
        assert not missing, f"Missing types: {missing}"
        assert len(observations) >= 10  # at least one per type

    def test_handles_empty_text(self) -> None:
        """Given empty text, When extracted, Then returns empty list."""
        observations = extract_observations(SESSION_EMPTY)
        assert observations == []

    def test_handles_whitespace_only(self) -> None:
        """Given whitespace-only text, When extracted, Then returns empty list."""
        observations = extract_observations("   \n\t  \n  ")
        assert observations == []

    def test_confidence_in_range(self) -> None:
        """Given any session text, When observations extracted, Then all confidences are 0.0-1.0."""
        observations = extract_observations(SESSION_WITH_ALL_TYPES)
        for obs in observations:
            assert 0.0 <= obs.confidence <= 1.0, f"Confidence out of range: {obs.confidence} for {obs}"

    def test_confidence_lower_for_uncertain_text(self) -> None:
        """Given uncertain/heuristic text, When extracted, Then confidence is lower than for definitive text."""
        strong = extract_observations(SESSION_WITH_ALL_TYPES)
        weak = extract_observations(SESSION_LOW_CONFIDENCE)
        strong_avg = sum(o.confidence for o in strong) / len(strong) if strong else 0.0
        weak_avg = sum(o.confidence for o in weak) / len(weak) if weak else 0.0
        assert strong_avg > weak_avg > 0.0, f"strong={strong_avg}, weak={weak_avg}"

    def test_observation_dataclass_fields(self) -> None:
        """Given an Observation, When created, Then has entity_name, obs_type, content, confidence."""
        obs = Observation(
            entity_name="auth-module",
            obs_type=ObservationType.DECISION,
            content="Use bcrypt for hashing",
            confidence=0.9,
        )
        assert obs.entity_name == "auth-module"
        assert obs.obs_type == ObservationType.DECISION
        assert obs.content == "Use bcrypt for hashing"
        assert obs.confidence == 0.9

    def test_detects_decisions(self) -> None:
        """Given text with decision patterns, When extracted, Then DECISION type found."""
        observations = extract_observations("We decided to use PostgreSQL instead of MySQL.")
        types = {obs.obs_type for obs in observations}
        assert ObservationType.DECISION in types

    def test_detects_blockers(self) -> None:
        """Given text with blocker patterns, When extracted, Then BLOCKER type found."""
        observations = extract_observations("BLOCKER: Cannot deploy until QA signs off.")
        types = {obs.obs_type for obs in observations}
        assert ObservationType.BLOCKER in types

    def test_detects_todos(self) -> None:
        """Given text with TODO patterns, When extracted, Then TODO type found."""
        observations = extract_observations("TODO: Add error handling for timeout cases.")
        types = {obs.obs_type for obs in observations}
        assert ObservationType.TODO in types

    def test_detects_all_ten_types_individually(self) -> None:
        """Given targeted text for each type, When extracted, Then each type is detected."""
        test_cases: list[tuple[str, ObservationType]] = [
            ("We decided to go with Redis for caching.", ObservationType.DECISION),
            ("BLOCKER: The API gateway is down.", ObservationType.BLOCKER),
            ("Objective: Reduce page load time to under 2 seconds.", ObservationType.OBJECTIVE),
            ("Finding: The database query takes 500ms on average.", ObservationType.FINDING),
            ("TODO: Write unit tests for the payment module.", ObservationType.TODO),
            ("Convention: Use snake_case for all Python files.", ObservationType.CONVENTION),
            ("Pattern: Every sprint, the same integration issues recur.", ObservationType.PATTERN),
            ("Assumption: The upstream service will respond within 100ms.", ObservationType.ASSUMPTION),
            ("Risk: Single point of failure in the auth service.", ObservationType.RISK),
            ("This feature depends on the notification-service being deployed first.", ObservationType.DEPENDENCY),
        ]
        for text, expected_type in test_cases:
            observations = extract_observations(text)
            types_found = {obs.obs_type for obs in observations}
            assert expected_type in types_found, (
                f"Expected {expected_type.value} in text: {text!r}, got {types_found}"
            )


class TestKeywordExtractionProvider:
    """Unit tests for the keyword-based provider."""

    def test_provider_is_instance_of_extraction_provider(self) -> None:
        """Given KeywordExtractionProvider, When checked, Then it is an ExtractionProvider."""
        provider = KeywordExtractionProvider()
        assert isinstance(provider, ExtractionProvider)

    def test_custom_provider_passed_to_extract(self) -> None:
        """Given a custom provider, When passed to extract_observations, Then it is used."""

        class FakeProvider(ExtractionProvider):
            def extract(self, session_text: str) -> list[Observation]:
                return [
                    Observation(
                        entity_name="test",
                        obs_type=ObservationType.DECISION,
                        content=session_text[:20],
                        confidence=1.0,
                    )
                ]

        observations = extract_observations("hello world", provider=FakeProvider())
        assert len(observations) == 1
        assert observations[0].content == "hello world"

    def test_content_preserves_original_text(self) -> None:
        """Given session text, When extracted, Then content is from original text (not normalized)."""
        observations = extract_observations("TODO: Fix the LoginPage component.")
        todos = [obs for obs in observations if obs.obs_type == ObservationType.TODO]
        assert len(todos) >= 1
        # Content should preserve original casing, not be lowercased
        assert "LoginPage" in todos[0].content
