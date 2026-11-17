"""Optional probability post-processing for Metaculus binary forecasts.

OFF by default. A different probability is not automatically a better forecast:
enable only after a reproducible, chronological, real-data holdout comparison.
No API tokens, network access, or external dependencies are required.
"""
from __future__ import annotations

import math


def guard_binary_probability(
    p: float, *, shrink: float = 0.0, anchor: float = 0.5
) -> float:
    """Geometrically shrink binary odds toward an anchor when explicitly enabled."""
    values = (p, shrink, anchor)
    if not all(math.isfinite(float(x)) for x in values):
        raise ValueError("All values must be finite")
    if not all(0.0 <= x <= 1.0 for x in values):
        raise ValueError("Probabilities and shrink must be within [0,1]")
    if shrink == 0.0:
        return p

    def logit(x: float) -> float:
        x = min(1.0 - 1e-6, max(1e-6, x))
        return math.log(x / (1.0 - x))

    z = (1.0 - shrink) * logit(p) + shrink * logit(anchor)
    return 1.0 / (1.0 + math.exp(-z))
