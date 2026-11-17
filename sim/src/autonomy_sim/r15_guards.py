"""R15 mathematical guards with the R16 certificate schema.

These helpers implement the revised definitions; they do not recompute or
rewrite historical R11--R14 result bundles.  Historical ``a_org`` values use
the old internal-state flow split and historical ``a_via`` values combine
present resources with defense readiness.  They remain legacy markers unless
the richer R15 inputs are available.

The compatibility-named certificate producers emit the R16 schema.  Channel,
goal, state-readiness, and artifact-binding metadata are mandatory so a legacy
bundle cannot be promoted merely by supplying plausible channel numbers.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from .aggregate import composite_A
from .numerics import clip_unit_value


R16_CHANNEL_SCHEMA_VERSION = "R16_CHANNEL_SCHEMA_V1"
CHANNEL_SCHEMA_VERSION = R16_CHANNEL_SCHEMA_VERSION
STATE_READINESS_VERSION = "R15_SPLIT"
ORG_MODES = frozenset({"L0_INTERNAL", "L1_NORMATIVE_NR"})
GOAL_MODES = frozenset({"STRUCTURAL_POINT", "IRL_INTERVAL"})
REGISTRATION_COMPLETENESS_VALUES = frozenset({"COMPLETE", "INCOMPLETE", "UNKNOWN"})
MECHANISM_EVIDENCE_VALUES = frozenset({"NONE", "SCM_AUDITED"})


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
    """RNI ordered-residual share, not an order-free causal source fraction.

    The registered primary chain order is R, then N=(G,B,M), then I:
      F_rand = I(R^T -> A^T),
      F_norm = I(N^T -> A^T || R^T),
      F_ext  = I(I^T -> A^T || N^T,R^T).
    A pure independent-register policy therefore has value zero whenever its
    random flow is positive.  With nondegenerate R/N interactions, callers must
    additionally report NRI and the I-last two-order Shapley-style sensitivity
    descriptor in :mod:`autonomy_sim.source_attribution`; chain additivity does
    not make this share unique.  The N/R semantic partition is preregistered.
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


def _ordered_unit_interval(values: Sequence[float], label: str) -> tuple[float, float]:
    try:
        endpoints = tuple(float(value) for value in values)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a numeric (lower, upper) interval") from exc
    if len(endpoints) != 2:
        raise ValueError(f"{label} must contain exactly two endpoints")
    lower, upper = endpoints
    if not math.isfinite(lower) or not math.isfinite(upper):
        raise ValueError(f"{label} endpoints must be finite")
    if not (0.0 <= lower <= 1.0 and 0.0 <= upper <= 1.0):
        raise ValueError(f"{label} endpoints must lie in [0,1]")
    if lower > upper:
        raise ValueError(f"{label} must be ordered as lower <= upper")
    return lower, upper


def goal_interval_compatible(before: Sequence[float], after: Sequence[float], *,
                             tol: float = 1e-12) -> bool:
    """Compare IRL alignment intervals by endpoint order.

    ``[l0,u0] <= [l1,u1]`` means exactly ``l1 >= l0 - tol`` and
    ``u1 >= u0 - tol``.  Both inputs must be ordered, finite intervals in
    ``[0,1]``; ``tol`` itself must be finite and non-negative.  This is an
    endpoint order on identified-set summaries, **not** an elementwise ordering
    of paired utilities across admissible worlds, and a rising lower endpoint
    alone is not a compatibility guarantee.
    """
    tol = _nonnegative_finite(tol, "goal interval tol")
    old_lower, old_upper = _ordered_unit_interval(before, "before goal interval")
    new_lower, new_upper = _ordered_unit_interval(after, "after goal interval")
    return new_lower >= old_lower - tol and new_upper >= old_upper - tol


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

    ``None`` is the only N/A marker: N/A -> N/A is compatible and changing
    N/A status is incompatible.  Every numeric value and ``tol`` is validated
    as finite before any comparison, so NaN (including NaN -> NaN) and either
    infinity fail closed rather than being hidden by IEEE comparison rules.

    This function deliberately does not infer compatibility from no-surgery,
    mediation, honesty, Lambda=1, or any other short-cut conjunction.
    """
    tol = _nonnegative_finite(tol, "compatibility tol")
    if set(before) != set(after):
        raise ValueError("before/after component schemas differ")

    validated: dict[str, dict[str, float | None]] = {"before": {}, "after": {}}
    for side, components in (("before", before), ("after", after)):
        for key, value in components.items():
            if value is None:
                validated[side][key] = None
                continue
            numeric = float(value)
            if not math.isfinite(numeric):
                raise ValueError(f"{side}[{key!r}] must be finite or None, got {numeric}")
            validated[side][key] = numeric

    for key, old in validated["before"].items():
        new = validated["after"][key]
        if (old is None) != (new is None):
            return False
        if old is not None and new < old - tol:
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
                           lambda_status: str, source_registration: str | None = None,
                           registration_completeness: str | None = None,
                           mechanism_evidence: str = "NONE",
                           channel_schema_version: str | None = None,
                           org_mode: str | None = None, goal_mode: str | None = None,
                           state_readiness_version: str | None = None,
                           model_hash: str | None = None,
                           evidence_hash: str | None = None) -> dict[str, object]:
    """Build a fail-closed R16 audit sidecar, retaining the R15 API name.

    Registration completeness and mechanism evidence are separate axes.
    ``mechanism_evidence="NONE"`` can reach only ``REGISTERED_COMPLETE`` when
    all registration fields are complete; ``SCM_AUDITED`` requires the explicit
    audited-SCM evidence value and is never inferred from complete fields.
    Unknown history/source/registration/Lambda caps the ceiling at ``LIMITED``.
    Lambda ``NOT_APPLICABLE`` at L0/L1 is not unknown.

    The required schema/mode fields prevent legacy bundles from being promoted
    implicitly.  Model and evidence hashes identify registered artifacts and
    bind this certificate to their declared values; they do **not** verify the
    artifacts, provenance, external truth, or external construct validity.
    ``integrity_certificate`` is always false as well.

    ``source_registration`` remains as a compatibility field and must agree
    with ``registration_completeness``.  Supplying either one populates both.
    """
    if layer not in {"L0", "L1", "L2"}:
        raise ValueError("layer must be L0, L1, or L2")
    if surgery_history not in {0, 1, None}:
        raise ValueError("surgery_history must be 0, 1, or None")
    if source_registration is None:
        source_registration = registration_completeness
    elif registration_completeness is None:
        registration_completeness = source_registration
    elif source_registration != registration_completeness:
        raise ValueError("source_registration and registration_completeness must agree")
    if source_registration not in REGISTRATION_COMPLETENESS_VALUES:
        raise ValueError("invalid source_registration")
    if registration_completeness not in REGISTRATION_COMPLETENESS_VALUES:
        raise ValueError("invalid registration_completeness")
    if mechanism_evidence not in MECHANISM_EVIDENCE_VALUES:
        raise ValueError("mechanism_evidence must be NONE or SCM_AUDITED")

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
               or registration_completeness != "COMPLETE"
               or lambda_status == "UNKNOWN"
               or (layer == "L2" and lambda_status != "DEFINED"))
    if unknown:
        evidence_ceiling = "LIMITED"
    elif mechanism_evidence == "SCM_AUDITED":
        evidence_ceiling = "SCM_AUDITED"
    else:
        evidence_ceiling = "REGISTERED_COMPLETE"
    cert = {
        "layer": layer,
        "construct_scope": ("internal_causal_only" if layer == "L0"
                            else "normative_structure_required"),
        "channel_schema_version": channel_schema_version,
        "org_mode": org_mode,
        "goal_mode": goal_mode,
        "state_readiness_version": state_readiness_version,
        "model_hash": model_hash,
        "evidence_hash": evidence_hash,
        "state_autonomy": state_autonomy,
        "viability_state": viability_state,
        "defense_readiness": defense_readiness,
        "surgery_history": surgery_history,
        "Lambda": lambda_value,
        "lambda_status": lambda_status,
        "source_registration": source_registration,
        "registration_completeness": registration_completeness,
        "mechanism_evidence": mechanism_evidence,
        "evidence_ceiling": evidence_ceiling,
        "external_construct_validation": False,
        "integrity_certificate": False,
    }

    # Use the exact writer contract at production time too; a producer/writer
    # drift therefore fails closed instead of creating an unwritable sidecar.
    from .logschema import validate_r15_certificate
    errors = validate_r15_certificate(cert)
    if errors:
        raise ValueError("invalid R16 certificate: " + "; ".join(errors))
    return cert


def produce_r15_certificate(*, layer: str, channels: Sequence[float],
                            weights: Sequence[float], resource_ratios: Sequence[float],
                            defense_margins: Sequence[float], surgery_history: int | None,
                            lambda_value: float | None, lambda_status: str,
                            source_registration: str | None = None, sigma: float = 1.0,
                            registration_completeness: str | None = None,
                            mechanism_evidence: str = "NONE",
                            channel_schema_version: str | None = None,
                            org_mode: str | None = None, goal_mode: str | None = None,
                            state_readiness_version: str | None = None,
                            model_hash: str | None = None,
                            evidence_hash: str | None = None) -> dict[str, object]:
    """Produce an R16 certificate from explicit R15/R16 channel semantics.

    ``channels`` must already use the layer-appropriate estimands.  Callers
    must explicitly supply ``channel_schema_version``, ``org_mode``,
    ``goal_mode``, and ``state_readiness_version``; none is inferred from a
    legacy Bundle or from plausible channel values.  L1/L2 additionally require
    lowercase SHA-256-sized model/evidence hashes and ``L1_NORMATIVE_NR``.
    The hashes bind registered artifacts but are not proof of external truth.
    The historical function name is retained for API compatibility.
    """
    if len(channels) != len(weights) or not channels:
        raise ValueError("channels and weights must be nonempty and have equal length")
    expected = {"L0": 2, "L1": 4, "L2": 5}.get(layer)
    if expected is None or len(channels) != expected:
        raise ValueError(f"{layer} requires {expected} applicable channel values")
    values = tuple(clip_unit_value(v, label="channel") for v in channels)
    raw_weights = tuple(_nonnegative_finite(w, "weight") for w in weights)
    weight_sum = math.fsum(raw_weights)
    if not math.isfinite(weight_sum) or weight_sum <= 0.0:
        raise ValueError("weights must be non-negative with finite positive sum")
    normalized_weights = tuple(w / weight_sum for w in raw_weights)
    channel_composite = composite_A(1.0, values, normalized_weights, sigma=float(sigma))
    split = state_defense_split(channel_composite, resource_ratios, defense_margins)
    return make_audit_certificate(
        layer=layer, state_autonomy=split["state_autonomy"],
        viability_state=split["viability_state"],
        defense_readiness=split["defense_readiness"],
        surgery_history=surgery_history, lambda_value=lambda_value,
        lambda_status=lambda_status, source_registration=source_registration,
        registration_completeness=registration_completeness,
        mechanism_evidence=mechanism_evidence,
        channel_schema_version=channel_schema_version, org_mode=org_mode,
        goal_mode=goal_mode, state_readiness_version=state_readiness_version,
        model_hash=model_hash, evidence_hash=evidence_hash)


# Current-schema name; the R15 symbol above remains for backward API compatibility.
produce_r16_certificate = produce_r15_certificate
