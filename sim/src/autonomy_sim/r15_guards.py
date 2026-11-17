"""R15 mathematical guards and audit-output separation.

These helpers implement the revised definitions; they do not recompute or
rewrite historical R11--R14 result bundles.  Historical ``a_org`` values use
the old internal-state flow split and historical ``a_via`` values combine
present resources with defense readiness.  They remain legacy markers unless
the richer R15 inputs are available.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from .aggregate import composite_A
from .numerics import clip_unit_value


def _nonnegative_finite(value: float, label: str) -> float:
    value = float(value)
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{label} must be finite and non-negative, got {value}")
    return value


def _flow_ratio(numerator: float, *other_flows: float, label: str) -> float:
    numerator = _nonnegative_finite(numerator, f"{label} numerator")
    others = tuple(_nonnegative_finite(v, f"{label} other flow") for v in other_flows)
    denominator = numerator + sum(others)
    if denominator <= 0.0:
        raise ValueError(f"{label} is undefined for a 0/0 flow decomposition")
    return clip_unit_value(numerator / denominator, label=label)


def internal_causal_org(f_int: float, f_ext: float) -> float:
    """R14/L0 internal-causal share, not full normative-source autonomy."""
    return _flow_ratio(f_int, f_ext, label="internal_causal_org")


def normative_org(f_norm: float, f_rand: float, f_ext: float) -> float:
    """L1+ normative-source share with innovation noise explicitly separated.

    The registered chain order is R, then N=(G,B,M), then I:
      F_rand = I(R^T -> A^T),
      F_norm = I(N^T -> A^T || R^T),
      F_ext  = I(I^T -> A^T || N^T,R^T).
    A pure independent-register policy therefore has value zero whenever its
    random flow is positive, rather than receiving the L0 internal-causal 1.
    """
    return _flow_ratio(f_norm, f_rand, f_ext, label="normative_org")


def goal_from_distance(distance: float, d_c: float) -> float:
    """Point-valued structural-read goal alignment for a nondegenerate d_c."""
    distance = _nonnegative_finite(distance, "goal distance")
    d_c = _nonnegative_finite(d_c, "d_c")
    if d_c <= 0.0:
        raise ValueError("point goal alignment is undefined for d_c=0")
    if distance > d_c + 1e-12:
        raise ValueError("goal distance exceeds the registered maximum d_c")
    return clip_unit_value(1.0 - distance / d_c, label="A_goal")


def goal_interval_from_distances(distances: Sequence[float], d_c: float) -> tuple[float, float]:
    """Set-valued IRL mode: return the induced alignment interval.

    ``distances`` are the distances of every observationally admissible U_eff
    to the fixed endorsed set under one protocol metric.  A nonempty set is
    required; no point-identification claim is made.
    """
    values = tuple(goal_from_distance(d, d_c) for d in distances)
    if not values:
        raise ValueError("IRL goal interval requires a nonempty admissible set")
    return min(values), max(values)


def state_defense_split(channel_composite: float,
                        resource_ratios: Sequence[float],
                        defense_margins: Sequence[float]) -> dict[str, float]:
    """Separate current state autonomy, survival, and defense readiness.

    Defense margins never reduce ``state_autonomy`` directly.  The optional
    ``defense_adjusted_autonomy`` is a resilience descriptor, not a claim about
    who determines current behavior.
    """
    base = clip_unit_value(channel_composite, label="channel_composite")
    resources = tuple(clip_unit_value(v, label="resource_ratio") for v in resource_ratios)
    defenses = tuple(clip_unit_value(v, label="defense_margin") for v in defense_margins)
    if not resources:
        raise ValueError("at least one current-resource ratio is required")
    if not defenses:
        raise ValueError("defense margins are required; use an explicit N/A protocol, not default 1")
    viability_state = min(resources)
    defense_readiness = min(defenses)
    state_autonomy = clip_unit_value(viability_state * base, label="state_autonomy")
    return {
        "viability_state": viability_state,
        "defense_readiness": defense_readiness,
        "state_autonomy": state_autonomy,
        "defense_adjusted_autonomy": clip_unit_value(
            defense_readiness * state_autonomy, label="defense_adjusted_autonomy"),
    }


def componentwise_compatible(before: Mapping[str, float | None],
                             after: Mapping[str, float | None],
                             *, tol: float = 1e-12) -> bool:
    """Definition-level comparison; N/A components must remain N/A.

    This function deliberately does not infer compatibility from no-surgery,
    mediation, honesty, Lambda=1, or any other short-cut conjunction.
    """
    if set(before) != set(after):
        raise ValueError("before/after component schemas differ")
    for key, old in before.items():
        new = after[key]
        if (old is None) != (new is None):
            return False
        if old is not None and float(new) < float(old) - tol:
            return False
    return True


def c2_recovery_threshold(delta: float, s_c: float) -> float:
    """Strict-descent threshold s > delta + s_c (delta=0 gives s > s_c)."""
    delta = _nonnegative_finite(delta, "delta")
    s_c = _nonnegative_finite(s_c, "s_c")
    return delta + s_c


def make_audit_certificate(*, layer: str, state_autonomy: float,
                           viability_state: float, defense_readiness: float,
                           surgery_history: int | None, lambda_value: float | None,
                           lambda_status: str, source_registration: str) -> dict[str, object]:
    """Mandatory output fields preventing a high score becoming a history seal.

    Unknown history or source registration caps the evidence ceiling at
    ``LIMITED``.  ``SCM_AUDITED`` denotes mechanism-level audit only, never
    external construct validation.  ``integrity_certificate`` is always false:
    the score and these fields together still do not certify absence of all
    manipulation.
    """
    if layer not in {"L0", "L1", "L2"}:
        raise ValueError("layer must be L0, L1, or L2")
    if surgery_history not in {0, 1, None}:
        raise ValueError("surgery_history must be 0, 1, or None")
    if source_registration not in {"COMPLETE", "INCOMPLETE", "UNKNOWN"}:
        raise ValueError("invalid source_registration")
    state_autonomy = clip_unit_value(state_autonomy, label="state_autonomy")
    viability_state = clip_unit_value(viability_state, label="viability_state")
    defense_readiness = clip_unit_value(defense_readiness, label="defense_readiness")
    if lambda_status not in {"DEFINED", "NOT_APPLICABLE", "UNKNOWN"}:
        raise ValueError("lambda_status must be DEFINED, NOT_APPLICABLE, or UNKNOWN")
    if lambda_status == "DEFINED":
        if lambda_value is None:
            raise ValueError("DEFINED Lambda requires a numeric value")
        lambda_value = clip_unit_value(lambda_value, label="Lambda")
    else:
        if lambda_value is not None:
            raise ValueError("N/A or UNKNOWN Lambda cannot carry a numeric value")
    if layer == "L2" and lambda_status == "NOT_APPLICABLE":
        raise ValueError("L2 requires DEFINED or UNKNOWN Lambda, not N/A")
    unknown = (surgery_history is None or source_registration != "COMPLETE"
               or lambda_status == "UNKNOWN" or (layer == "L2" and lambda_status != "DEFINED"))
    return {
        "layer": layer,
        "construct_scope": ("internal_causal_only" if layer == "L0"
                            else "normative_structure_required"),
        "state_autonomy": state_autonomy,
        "viability_state": viability_state,
        "defense_readiness": defense_readiness,
        "surgery_history": surgery_history,
        "Lambda": lambda_value,
        "lambda_status": lambda_status,
        "source_registration": source_registration,
        "evidence_ceiling": "LIMITED" if unknown else "SCM_AUDITED",
        "external_construct_validation": False,
        "integrity_certificate": False,
    }


def produce_r15_certificate(*, layer: str, channels: Sequence[float],
                            weights: Sequence[float], resource_ratios: Sequence[float],
                            defense_margins: Sequence[float], surgery_history: int | None,
                            lambda_value: float | None, lambda_status: str,
                            source_registration: str, sigma: float = 1.0) -> dict[str, object]:
    """Actual R15 producer: channel aggregate -> state/defense -> certificate.

    ``channels`` must already use the layer-appropriate R15 estimands.  Legacy
    Bundle values cannot be passed silently as an L1+ normative-source read:
    callers must compute ``normative_org`` from an explicit N/R/I model first.
    """
    if len(channels) != len(weights) or not channels:
        raise ValueError("channels and weights must be nonempty and have equal length")
    expected = {"L0": 2, "L1": 4, "L2": 5}.get(layer)
    if expected is None or len(channels) != expected:
        raise ValueError(f"{layer} requires {expected} applicable channel values")
    values = tuple(clip_unit_value(v, label="channel") for v in channels)
    weight_sum = math.fsum(float(w) for w in weights)
    if weight_sum <= 0.0 or any(float(w) < 0.0 for w in weights):
        raise ValueError("weights must be non-negative with positive sum")
    normalized_weights = tuple(float(w) / weight_sum for w in weights)
    channel_composite = composite_A(1.0, values, normalized_weights, sigma=float(sigma))
    split = state_defense_split(channel_composite, resource_ratios, defense_margins)
    return make_audit_certificate(
        layer=layer, state_autonomy=split["state_autonomy"],
        viability_state=split["viability_state"],
        defense_readiness=split["defense_readiness"],
        surgery_history=surgery_history, lambda_value=lambda_value,
        lambda_status=lambda_status, source_registration=source_registration)
