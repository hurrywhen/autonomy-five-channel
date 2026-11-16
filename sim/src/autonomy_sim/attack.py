"""Attack/defense optimization certificates used by the R14 revision.

The linear-fraction attacker *minimizes* the logarithmic composite.  Concavity
of that objective does not justify an interior minimum: on the registered
budget polytope a minimum is attained at an extreme point.  This module keeps
that optimization separate from T4(i)'s log-linear damage model.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class VertexAttack:
    channel: int
    x: tuple
    retention: float
    objective: float


def _parameters(w, c, s, B):
    w = np.asarray(w, dtype=float)
    c = np.asarray(c, dtype=float)
    s = np.asarray(s, dtype=float)
    B = float(B)
    if not (w.ndim == c.ndim == s.ndim == 1 and len(w) == len(c) == len(s) and len(w)):
        raise ValueError("w,c,s must be non-empty vectors of equal length")
    if np.any(~np.isfinite(w)) or np.any(w <= 0) or abs(float(w.sum()) - 1.0) > 1e-9:
        raise ValueError("w must be finite, strictly positive, and sum to one")
    if np.any(~np.isfinite(c)) or np.any(c <= 0) or np.any(~np.isfinite(s)) or np.any(s <= 0):
        raise ValueError("c and s must be finite and strictly positive")
    if not math.isfinite(B) or B <= 0:
        raise ValueError("B must be finite and strictly positive")
    return w, c, s, B


def linear_fraction_objective(x, w, s) -> float:
    """Extended-real J(x)=sum_i w_i log(1-s_i x_i), excluding constant baselines."""
    x = np.asarray(x, dtype=float)
    w = np.asarray(w, dtype=float)
    s = np.asarray(s, dtype=float)
    if not (x.ndim == w.ndim == s.ndim == 1 and len(x) == len(w) == len(s)):
        raise ValueError("x,w,s must be vectors of equal length")
    retention = 1.0 - s * x
    if np.any(x < -1e-12) or np.any(retention < -1e-12):
        raise ValueError("infeasible linear-fraction attack point")
    if np.any(retention <= 1e-15):
        return -math.inf
    return float(np.dot(w, np.log(retention)))


def linear_fraction_vertices(w, c, s, B) -> list[VertexAttack]:
    """Enumerate budget-extreme candidate witnesses, including zero-retention arms."""
    w, c, s, B = _parameters(w, c, s, B)
    result = []
    for i in range(len(w)):
        saturation_effort = B / c[i]
        retention = 1.0 - s[i] * saturation_effort
        x = np.zeros(len(w))
        if retention < 0.0:
            # Zero retention is feasible before the budget is exhausted; the
            # residual budget cannot improve an already -inf extended objective.
            x[i] = 1.0 / s[i]
        else:
            x[i] = saturation_effort
        retention = max(0.0, retention)
        objective = -math.inf if retention <= 1e-15 else float(w[i] * math.log(retention))
        result.append(VertexAttack(i, tuple(float(v) for v in x), retention, objective))
    return result


def solve_linear_fraction_attack(w, c, s, B) -> dict:
    """Return a global minimizer and an auditable symbolic certificate.

    First handle zero-retention arms separately: the extended minimum -inf is
    then attained at a zero boundary, and non-extreme minimizers can also exist.
    On the strictly positive-retention feasible domain, strict concavity gives
    J(x)>sum_k alpha_k J(v_k) for every non-extreme convex combination, so a
    global minimum is attained at an extreme point. With no zero-retention arm,
    every minimum uses the full budget and is one of the displayed vertices.
    """
    w, c, s, B = _parameters(w, c, s, B)
    vertices = linear_fraction_vertices(w, c, s, B)
    best_value = min(v.objective for v in vertices)
    best = [v for v in vertices if v.objective == best_value]
    return {
        "x": best[0].x,
        "objective": best_value,
        "optimal_channels": [v.channel for v in best],
        "vertices": vertices,
        "proof": {
            "decision": "minimize",
            "gradient_i": "-w_i*s_i/(1-s_i*x_i)",
            "hessian_ii": "-w_i*s_i**2/(1-s_i*x_i)**2",
            "extreme_point_argument": (
                "on the strictly positive-retention domain, strict concavity "
                "gives J(sum alpha*v)>sum alpha*J(v), hence an extreme minimizer; "
                "zero-retention is handled separately and can have non-extreme minima"
            ),
            "vertex_objective_i": "w_i*log(max(0,1-s_i*B/c_i)); zero gives -infinity",
        },
    }


def symbolic_symmetric_kkt_certificate() -> dict:
    """Independent symbolic boundary check for the review's two-channel example.

    At x=(1/4,1/4), the equality-budget KKT gradient condition is
    -w_i*s_i/(1-s_i*x_i)+lambda*c_i=0 with lambda=2/3.  The Hessian is -8/9 I,
    hence the stationary point is the concave objective's maximum, not its
    minimum.  The two budget vertices supply the actual minimum candidates.
    """
    w = (0.5, 0.5)
    c = s = (1.0, 1.0)
    B = 0.5
    x = (0.25, 0.25)
    gradient = tuple(-w[i] * s[i] / (1.0 - s[i] * x[i]) for i in range(2))
    multiplier = -gradient[0] / c[0]
    hessian_diagonal = tuple(-w[i] * s[i] ** 2 / (1.0 - s[i] * x[i]) ** 2
                             for i in range(2))
    stationary_value = linear_fraction_objective(x, w, s)
    solution = solve_linear_fraction_attack(w, c, s, B)
    return {
        "stationary_x": x,
        "gradient": gradient,
        "budget_multiplier": multiplier,
        "hessian_diagonal": hessian_diagonal,
        "stationary_objective": stationary_value,
        "stationary_is_local_maximum": all(h < 0 for h in hessian_diagonal),
        "minimum": solution,
    }


def grid_search_2d(w, c, s, B, n: int = 501) -> dict:
    """Independent feasible-grid lower bound for two channels (not a proof)."""
    w, c, s, B = _parameters(w, c, s, B)
    if len(w) != 2 or n < 2:
        raise ValueError("grid_search_2d requires two channels and n>=2")
    best_x, best_value = None, math.inf
    # x0 ranges over its budget/zero-retention feasible upper endpoint.
    x0_max = min(B / c[0], 1.0 / s[0])
    for x0 in np.linspace(0.0, x0_max, n):
        remaining = B - c[0] * x0
        x1_max = min(max(0.0, remaining) / c[1], 1.0 / s[1])
        for x1 in np.linspace(0.0, x1_max, n):
            value = linear_fraction_objective((x0, x1), w, s)
            if value < best_value:
                best_x, best_value = (float(x0), float(x1)), value
    return {"x": best_x, "objective": best_value, "n_per_axis": n}


def loglinear_damage_comparison(w, s, c, budget: float) -> dict:
    """T4(i) concentrated/spread comparison with channel-correct weight indexing."""
    w, c, s, B = _parameters(w, c, s, budget)
    ratios = w * s / c
    best = float(ratios.max())
    channels = [int(i) for i in np.flatnonzero(ratios >= best - 1e-12)]
    pick = channels[0]
    concentrated = float(B * w[pick] * s[pick] / c[pick])
    spread = float(sum(B / len(w) * w[i] * s[i] / c[i] for i in range(len(w))))
    return {"pick": pick, "optimal_channels": channels, "ratios": ratios,
            "concentrated": concentrated, "spread": spread}


def defense_equalization_necessary(rho, e, total_budget=None, responsive=True) -> bool:
    """Check T4(ii)'s necessary condition with an explicit responsiveness premise.

    If the unique maximal response is locally strictly decreasing
    (``responsive=True``), a unique strict maximum is incompatible with
    optimality whenever its defense can be increased using unused budget or a
    donor. Otherwise full-budget single funding is the only remaining case.
    Flat responses (``responsive=False``) block that inference: a unique strict
    maximum can be optimal at any allocation. These conditions are necessary,
    not sufficient, and ``rho_i(0)<=R`` merely restates the maximum definition.
    """
    rho = np.asarray(rho, dtype=float)
    e = np.asarray(e, dtype=float)
    if rho.ndim != 1 or e.shape != rho.shape or np.any(e < 0):
        raise ValueError("rho and e must be equal-length vectors with e>=0")
    if total_budget is not None and float(total_budget) < 0:
        raise ValueError("total_budget must be nonnegative")
    maximum = float(rho.max())
    maxima = np.flatnonzero(rho >= maximum - 1e-12)
    if len(maxima) != 1:
        return True
    if not responsive:
        return True  # flat maximal response: no strict equalization inference
    i = int(maxima[0])
    funded = np.flatnonzero(e > 1e-12)
    full_budget_on_i = (len(funded) == 1 and int(funded[0]) == i
                        and (total_budget is None
                             or abs(float(e.sum()) - float(total_budget)) <= 1e-12))
    return bool(full_budget_on_i)
