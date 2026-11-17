"""Small, explicit descriptive statistics used by R15 read-only analyses."""
from __future__ import annotations

import math
from collections.abc import Sequence


def paired_mean_se(differences: Sequence[float]) -> dict[str, float | int]:
    """Mean and sample SE of paired per-context differences.

    This is the appropriate cross-check summary when integrated and sampled
    estimates share X,Z,J contexts.  Only downstream noise is independent;
    the two standard errors must not be added as though contexts were unpaired.
    """
    values = tuple(float(v) for v in differences)
    n = len(values)
    if n < 2:
        raise ValueError("paired SE requires at least two differences")
    if not all(math.isfinite(v) for v in values):
        raise ValueError("paired differences must be finite")
    mean = sum(values) / n
    se = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1)) / math.sqrt(n)
    return {"n": n, "mean_difference": mean, "abs_mean_difference": abs(mean),
            "paired_se": se, "normal_95_halfwidth": 1.96 * se}


def kendall_tau_b(xs: Sequence[float], ys: Sequence[float]) -> dict[str, float | int]:
    """Kendall tau-b with explicit tie accounting (O(n^2), audit-sized series).

    Returns counts as well as the coefficient so a summary cannot silently
    turn tied or constant columns into perfect agreement.  If the tau-b
    denominator is zero, the coefficient is NaN and the result is not a valid
    ordering-stability claim.
    """
    if len(xs) != len(ys):
        raise ValueError("tau-b inputs must have equal length")
    n = len(xs)
    if n < 2:
        return {"tau_b": float("nan"), "n": n, "concordant": 0, "discordant": 0,
                "ties_x_only": 0, "ties_y_only": 0, "ties_both": 0}
    c = d = tx_only = ty_only = t_both = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = float(xs[i]) - float(xs[j])
            dy = float(ys[i]) - float(ys[j])
            if dx == 0.0 and dy == 0.0:
                t_both += 1
            elif dx == 0.0:
                tx_only += 1
            elif dy == 0.0:
                ty_only += 1
            elif dx * dy > 0.0:
                c += 1
            else:
                d += 1
    n0 = n * (n - 1) // 2
    denominator = math.sqrt((c + d + tx_only) * (c + d + ty_only))
    return {"tau_b": (c - d) / denominator if denominator else float("nan"),
            "n": n, "concordant": c, "discordant": d,
            "ties_x_only": tx_only, "ties_y_only": ty_only,
            "ties_both": t_both, "pairs": n0}
