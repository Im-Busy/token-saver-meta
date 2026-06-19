"""Repository collection — RepoSet dataclass holding all three repos."""

from __future__ import annotations

from dataclasses import dataclass

from .node_repo import NodeRepo
from .obs_repo import ObsRepo
from .session_repo import SessionRepo


@dataclass(frozen=True, slots=True)
class RepoSet:
    """All three repositories sharing a single connection."""
    node: NodeRepo
    obs: ObsRepo
    session: SessionRepo
