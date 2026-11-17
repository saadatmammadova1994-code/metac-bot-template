"""Offline-only binary aggregation and proper scoring.

NOT wired into the live Metaculus tournament bot. No model superiority claim.
"""
from __future__ import annotations

import math


def check_probability(p: float) -> float:
    p = float(p)
    if not math.isfinite(p) or not 0 <= p <= 1:
        raise ValueError("Expected finite probability in [0,1]")
    return p


def brier(p: float, outcome: int) -> float:
    if outcome not in (0, 1):
        raise ValueError("Binary outcome must be 0 or 1")
    return (check_probability(p) - outcome) ** 2


def log_loss(p: float, outcome: int) -> float:
    if outcome not in (0, 1):
        raise ValueError("Binary outcome must be 0 or 1")
    p = min(1 - 1e-12, max(1e-12, check_probability(p)))
    return -(outcome * math.log(p) + (1-outcome) * math.log1p(-p))


def aggregate_binary(
    probabilities: list[float], *, weights: list[float] | None = None,
    anchor: float = 0.5, shrink: float = 0.0
) -> float:
    """Unvalidated weighted logit pooling; do not treat correlated models as independent."""
    if not probabilities:
        raise ValueError("Empty probability collection")
    if not 0 <= shrink <= 1:
        raise ValueError("Invalid shrink")
    check_probability(anchor)
    if weights is None:
        weights = [1.0] * len(probabilities)
    if len(weights) != len(probabilities):
        raise ValueError("Weight count differs")
    if any(not math.isfinite(float(w)) or w < 0 for w in weights) or sum(weights) <= 0:
        raise ValueError("Weights must be finite, nonnegative, and not all zero")

    def logit(p: float) -> float:
        p = min(1.0-1e-6, max(1e-6, check_probability(p)))
        return math.log(p / (1.0-p))

    mean = sum(float(w) * logit(p) for p, w in zip(probabilities, weights))/sum(weights)
    total = (1.0-shrink)*mean + shrink*logit(anchor)
    return 1.0/(1.0+math.exp(-total))
