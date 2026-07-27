"""Agent-agnostic Verified Save protocol and local acceleration state."""

from .engine import AccelerationEngine, DeterministicAdapter
from .model import (
    DecisionType,
    ScopeError,
    decision_key,
    normalize_scope,
    rule_hash,
)
from .store import AccelerationStore, StateIntegrityError

__all__ = [
    "AccelerationEngine",
    "AccelerationStore",
    "DecisionType",
    "DeterministicAdapter",
    "ScopeError",
    "StateIntegrityError",
    "decision_key",
    "normalize_scope",
    "rule_hash",
]
