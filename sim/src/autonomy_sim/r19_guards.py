"""R19 layer-aware full-profile audit certificate schema.

R18 remains a compatibility layer (point-valued L2 native example).  R19
closes the generality gaps identified in the R18 review:

* **Layer-aware attribution.**  L0 certificates carry an independent
  ``L0_INTERNAL_CAUSAL`` report (F_int, F_ext and the internal-causal share
  only); the L1-style RNI/NRI/order-average decomposition is *not* imposed on
  L0.  L1/L2 carry the registered partition, alternative semantic partitions,
  and the three order conventions.
* **Four channel states.**  ``DEFINED``, ``INTERVAL``, ``UNKNOWN``,
  ``NOT_APPLICABLE``.  Point certificates (all channels DEFINED) and interval
  certificates are separate modes; insufficient information may never be
  forced into a point value.  IRL goal intervals, approximate-fixed-point
  intervals, thin-log and zero-entropy reflection degradation, and zero-total-
  flow share unidentifiability all have explicit interval semantics with
  composite interval propagation (the geometric composite is coordinatewise
  monotone, so endpoint propagation is exact).
* **Decomposed sensitivity.**  ``order_spread`` is the spread across order
  conventions under the registered semantic partition;
  ``semantic_partition_spread`` is the maximum, over fixed order conventions,
  of the spread across semantic partitions; ``overall_composite_range`` is an
  overview only.  ORDER_SENSITIVE and MODEL_SENSITIVE are triggered by their
  own spreads, not by a shared total span.
* **Honest threshold provenance.**  The 0.05 composite-scale thresholds were
  frozen *after* the R17-native results were observed: they are POST HOC
  FROZEN internal engineering thresholds, not preregistered before outcomes.
  Preregistration language is reserved for future audits frozen before their
  outcomes are seen.  They are not a domain SESOI and not a power calculation.
* **Separated evidence binding.**  Certificate evidence hashes bind immutable
  registered inputs (raw logs, config); non-unique iterative-optimizer
  auxiliary coordinates are analysis outputs with declared field-level replay
  tolerances, never the sole bearer of byte-level evidence binding.

This module is an internal audit-schema guard, not external construct
validation.  Historical R11--R18 artifacts are read-only.
"""
from __future__ import annotations

import json
import math

from .aggregate import composite_A
from .formation_audit import formation_status, validate_lambda_time_origin
from .r17_guards import (COMPOSITE_SCALE, CURRENT_STRUCTURAL_SCOPE,
                         HISTORICAL_FORMATION_SCOPE, R17_CHANNEL_SCHEMA_VERSION,
                         validate_r17_certificate)

R19_CHANNEL_SCHEMA_VERSION = "R19_CHANNEL_SCHEMA_V1"

# Post hoc frozen internal engineering thresholds (composite-scale spread).
# Frozen 2026-11-21 after observing the R17-native convention composites;
# NOT preregistered before outcomes, NOT a domain SESOI, NOT a power analysis.
ORDER_SENSITIVITY_THRESHOLD = 0.05
SEMANTIC_SENSITIVITY_THRESHOLD = 0.05
THRESHOLD_PROVENANCE = (
    "POST_HOC_FROZEN_INTERNAL_ENGINEERING_THRESHOLD_AFTER_R17_NATIVE_RESULTS_"
    "NOT_PREREGISTERED_BEFORE_OUTCOMES_NOT_DOMAIN_SESOI")

CHANNEL_ORDER_L2 = ("a_org", "a_goal", "a_exec", "a_epi", "a_ref")
LAYER_CHANNELS = {
    "L0": ("a_org", "a_exec"),
    "L1": ("a_org", "a_goal", "a_exec", "a_epi"),
    "L2": CHANNEL_ORDER_L2,
}
ORDER_CONVENTIONS = ("RNI", "NRI", "order_average")
SHARE_KEYS = ("normative_share_RNI", "normative_share_NRI",
              "normative_share_order_average")
FLOW_KEYS = ("flows_bits_RNI", "flows_bits_NRI", "joint_di_bits")
CHANNEL_STATES = frozenset({"DEFINED", "INTERVAL", "UNKNOWN", "NOT_APPLICABLE"})
CERTIFICATE_MODES = frozenset({"POINT", "INTERVAL"})
SENSITIVITY_FLAG_VALUES = frozenset({"ORDER_SENSITIVE", "MODEL_SENSITIVE"})
REFLECTION_DEGRADATION_REASONS = frozenset({
    "THIN_LOG", "ZERO_ENTROPY_ENSEMBLE", "NO_LOG_CARRIERS", "MIXED_DEGRADATION"})
GOAL_DEGRADATION_REASONS = frozenset({
    "APPROXIMATE_FIXED_POINT_SET", "ENDORSEMENT_BLIND_DC_ZERO"})
GRADE_POINT = "POINT_READING_UNDER_REGISTERED_CONVENTION_ONLY"
GRADE_SENSITIVE = "SENSITIVITY_QUALIFIED_NOT_A_ROBUST_POINT_READING"
GRADE_L0 = "L0_INTERNAL_CAUSAL_POINT_READING"
GRADE_INTERVAL = "INTERVAL_VALUED_NOT_A_POINT_READING"
GRADE_INTERVAL_SENSITIVE = "INTERVAL_VALUED_SENSITIVITY_QUALIFIED"
GRADE_ZERO_FLOW = "INTERVAL_ZERO_TOTAL_FLOW_SHARE_UNIDENTIFIED"
TOL = 1e-9

R19_EXTRA_FIELDS = (
    "certificate_mode", "channel_profile", "sensitivity_flags",
    "composite_scalar_grade", "scalar_export_warning", "state_autonomy_interval",
    "threshold_provenance", "degradation_reasons", "unknown_channels",
)
# attribution_report (L0) / attribution_sensitivity (L1/L2) is layer-conditional.


def _unit(value, label: str) -> float:
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{label} must be finite and in [0,1], got {value!r}")
    return value


def _optional_unit(value, label: str):
    if value is None:
        return None
    return _unit(value, label)


def _interval(interval, label: str, *, required: bool = False):
    if interval is None:
        if required:
            raise ValueError(f"{label} interval is required")
        return None
    if not isinstance(interval, (list, tuple)) or len(interval) != 2:
        raise ValueError(f"{label} interval must be [lower, upper]")
    lower = _unit(interval[0], f"{label} interval lower")
    upper = _unit(interval[1], f"{label} interval upper")
    if lower > upper:
        raise ValueError(f"{label} interval must be ordered lower <= upper")
    return [lower, upper]


def _nonnegative_int(value, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer")
    return value


def _reason(entry: dict, label: str) -> str:
    reason = entry.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError(f"{label} requires a nonempty reason")
    return reason


def _validate_partition_report(report, label: str, *, mode: str) -> None:
    if not isinstance(report, dict):
        raise ValueError(f"{label} must be an object")
    for key in FLOW_KEYS:
        if key not in report:
            raise ValueError(f"{label} missing {key}")
    flows_rni = report["flows_bits_RNI"]
    flows_nri = report["flows_bits_NRI"]
    for flows, name in ((flows_rni, "flows_bits_RNI"), (flows_nri, "flows_bits_NRI")):
        if not isinstance(flows, (list, tuple)) or len(flows) != 3:
            raise ValueError(f"{label}.{name} must list three flow terms")
        for value in flows:
            if not math.isfinite(float(value)) or float(value) < -TOL:
                raise ValueError(f"{label}.{name} entries must be finite and nonnegative")
    total = float(report["joint_di_bits"])
    if not math.isfinite(total) or total < -TOL:
        raise ValueError(f"{label}.joint_di_bits must be finite and nonnegative")
    for flows, name in ((flows_rni, "RNI"), (flows_nri, "NRI")):
        if abs(math.fsum(float(v) for v in flows) - total) > 1e-6:
            raise ValueError(f"{label} {name} flows do not sum to joint_di_bits")
    for key in SHARE_KEYS:
        if key not in report:
            raise ValueError(f"{label} missing {key}")
        value = report[key]
        if value is None:
            if total > TOL:
                raise ValueError(f"{label}.{key} is None but total flow is positive")
        else:
            _unit(value, f"{label}.{key}")
    if total > TOL:
        expected_rni = float(flows_rni[1]) / total
        expected_nri = float(flows_nri[0]) / total
        if abs(report["normative_share_RNI"] - expected_rni) > 1e-6:
            raise ValueError(f"{label} RNI share disagrees with its flow term")
        if abs(report["normative_share_NRI"] - expected_nri) > 1e-6:
            raise ValueError(f"{label} NRI share disagrees with its flow term")
        if abs(report["normative_share_order_average"]
               - 0.5 * (expected_rni + expected_nri)) > 1e-6:
            raise ValueError(f"{label} order average must be the two-order mean")
    if mode == "INTERVAL":
        intervals = report.get("share_intervals")
        if not isinstance(intervals, dict):
            raise ValueError(f"{label}.share_intervals is required in INTERVAL mode")
        for convention, key in zip(ORDER_CONVENTIONS, SHARE_KEYS):
            share_interval = _interval(intervals.get(convention),
                                       f"{label}.share_intervals.{convention}")
            if total <= TOL:
                if share_interval is not None:
                    raise ValueError(f"{label}.{convention} share interval must be null "
                                     "when total flow is zero (share unidentifiable)")
            else:
                if share_interval is None:
                    raise ValueError(f"{label}.{convention} share interval required "
                                     "for positive total flow in INTERVAL mode")
                point = report[key]
                if not share_interval[0] - TOL <= point <= share_interval[1] + TOL:
                    raise ValueError(f"{label}.{convention} point share outside its interval")


def _validate_l0_report(report) -> None:
    if not isinstance(report, dict):
        raise ValueError("L0 attribution_report must be an object")
    if report.get("mode") != "L0_INTERNAL_CAUSAL":
        raise ValueError("L0 attribution_report.mode must be L0_INTERNAL_CAUSAL "
                         "(RNI/NRI decomposition is an L1+ estimand, not L0)")
    f_int = float(report.get("f_int_bits"))
    f_ext = float(report.get("f_ext_bits"))
    if not math.isfinite(f_int) or f_int < -TOL or not math.isfinite(f_ext) or f_ext < -TOL:
        raise ValueError("L0 flows must be finite and nonnegative")
    total = f_int + f_ext
    share = report.get("internal_causal_share")
    if total <= TOL:
        if share is not None:
            raise ValueError("L0 internal-causal share must be null for zero total flow")
    else:
        if share is None or abs(float(share) - f_int / total) > 1e-6:
            raise ValueError("L0 internal_causal_share must equal f_int/(f_int+f_ext)")
        _unit(share, "L0 internal_causal_share")
    for forbidden in ("normative_share_RNI", "normative_share_NRI",
                      "normative_share_order_average", "registered_partition"):
        if forbidden in report:
            raise ValueError(f"L0 report must not carry L1+ attribution field {forbidden}")


def _validate_channel_entry(entry, name: str, *, layer: str, goal_mode: str,
                            lambda_status: str, mode: str) -> None:
    if not isinstance(entry, dict):
        raise ValueError(f"channel_profile.{name} must be an object")
    state = entry.get("state")
    if state not in CHANNEL_STATES:
        raise ValueError(f"channel_profile.{name}.state must be one of {sorted(CHANNEL_STATES)}")
    protocol = entry.get("protocol_version")
    if not isinstance(protocol, str) or not protocol:
        raise ValueError(f"channel_profile.{name}.protocol_version is required")
    if state == "DEFINED":
        _unit(entry.get("value"), f"channel_profile.{name}.value")
        interval = _interval(entry.get("interval"), name)
        if interval is not None:
            value = float(entry["value"])
            if not interval[0] - TOL <= value <= interval[1] + TOL:
                raise ValueError(f"channel_profile.{name}.interval must contain its value")
    elif state == "INTERVAL":
        if entry.get("value") is not None:
            raise ValueError(f"channel_profile.{name} INTERVAL state must not force a point value")
        _interval(entry.get("interval"), name, required=True)
        if mode != "INTERVAL":
            raise ValueError("INTERVAL channels require INTERVAL certificate mode")
    elif state == "UNKNOWN":
        if entry.get("value") is not None or entry.get("interval") is not None:
            raise ValueError(f"channel_profile.{name} UNKNOWN must carry no value or interval")
        _reason(entry, f"channel_profile.{name}")
    else:  # NOT_APPLICABLE
        if entry.get("value") is not None or entry.get("interval") is not None:
            raise ValueError(f"channel_profile.{name} NOT_APPLICABLE must carry no value/interval")
        _reason(entry, f"channel_profile.{name}")

    if name == "a_exec" and state in {"DEFINED", "INTERVAL"}:
        horizon = entry.get("horizon_actions")
        if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon < 1:
            raise ValueError("a_exec.horizon_actions must be a positive integer")
        if entry.get("uses_intermediate_observations") is not False:
            raise ValueError("a_exec must be a precommitted open-loop audit object")
    if name == "a_goal" and state in {"DEFINED", "INTERVAL"}:
        irl = _interval(entry.get("irl_interval"), "a_goal.irl", required=True)
        structural = _optional_unit(entry.get("structural_point"), "a_goal.structural_point")
        if state == "DEFINED":
            if structural is None:
                raise ValueError("a_goal DEFINED requires the structural point")
            if abs(float(entry["value"]) - structural) > TOL:
                raise ValueError("a_goal.value must equal its structural point")
        else:
            if goal_mode == "IRL_INTERVAL":
                if structural is not None:
                    raise ValueError("IRL_INTERVAL mode must not force a structural point; "
                                     "the IRL interval is the primary output")
                if any(abs(a - b) > TOL for a, b in zip(entry["interval"], irl)):
                    raise ValueError("IRL_INTERVAL a_goal interval must equal the registered IRL interval")
            else:
                reason = entry.get("degradation_reason")
                if reason not in GOAL_DEGRADATION_REASONS:
                    raise ValueError("STRUCTURAL_POINT a_goal INTERVAL requires a registered "
                                     "degradation reason (approximate fixed point / dc=0)")
                if structural is not None:
                    raise ValueError("degraded structural goal must not force a point")
    if name == "a_ref":
        _validate_ref_entry(entry, state, lambda_status=lambda_status, layer=layer)


def _validate_ref_entry(entry, state: str, *, lambda_status: str, layer: str) -> None:
    if state == "NOT_APPLICABLE":
        if lambda_status != "NOT_APPLICABLE":
            raise ValueError("a_ref NOT_APPLICABLE requires lambda_status NOT_APPLICABLE "
                             "(L2 Lambda cannot be N/A)")
        return
    if state == "UNKNOWN":
        if lambda_status != "UNKNOWN":
            raise ValueError("a_ref UNKNOWN requires lambda_status UNKNOWN")
        return
    fidelity = _optional_unit(entry.get("fidelity"), "a_ref.fidelity")
    consistency = _optional_unit(entry.get("endorsement_consistency"),
                                 "a_ref.endorsement_consistency")
    lambda_value = _optional_unit(entry.get("Lambda"), "a_ref.Lambda")
    counts = entry.get("event_counts")
    if not isinstance(counts, dict):
        raise ValueError("a_ref.event_counts is required (logged carriers, not asserted constants)")
    updates = _nonnegative_int(counts.get("normative_update_events"), "normative_update_events")
    endorsements = _nonnegative_int(counts.get("endorsement_events"), "endorsement_events")
    contexts = _nonnegative_int(counts.get("surgery_contexts"), "surgery_contexts")
    if endorsements > updates:
        raise ValueError("endorsement_events cannot exceed normative_update_events")
    if consistency is not None:
        if updates < 1:
            raise ValueError("numeric endorsement consistency requires logged update events")
        if abs(consistency - endorsements / updates) > TOL:
            raise ValueError("endorsement_consistency must equal the logged event ratio")
    if lambda_value is not None and contexts < 1:
        raise ValueError("numeric Lambda requires logged surgery contexts")
    if state == "DEFINED":
        if fidelity is None or consistency is None or lambda_value is None:
            raise ValueError("a_ref DEFINED requires all three factors")
        if updates < 1 or contexts < 1:
            raise ValueError("a_ref DEFINED requires logged normative-update and surgery-context carriers")
        if abs(fidelity * consistency * lambda_value - float(entry["value"])) > TOL:
            raise ValueError("a_ref.value must equal fidelity * consistency * Lambda")
    else:  # INTERVAL
        reason = entry.get("degradation_reason")
        if reason not in REFLECTION_DEGRADATION_REASONS:
            raise ValueError("a_ref INTERVAL requires a registered degradation reason "
                             "(thin log / zero-entropy ensemble / no carriers)")
        if fidelity is not None and consistency is not None and lambda_value is not None:
            raise ValueError("a_ref INTERVAL requires at least one undefined factor")
        defined = [v for v in (fidelity, consistency, lambda_value) if v is not None]
        upper = 1.0
        for value in defined:
            upper *= value
        interval = entry["interval"]
        if abs(interval[0]) > TOL or abs(interval[1] - upper) > TOL:
            raise ValueError("a_ref INTERVAL must be [0, product of defined factors] "
                             "(paper D-ref degradation rule)")


def _validate_channel_profile(profile: dict, *, layer: str, goal_mode: str,
                              lambda_status: str, mode: str) -> tuple[str, ...]:
    if not isinstance(profile, dict):
        raise ValueError("channel_profile must be an object")
    applicable = LAYER_CHANNELS[layer]
    if set(profile) != set(applicable):
        raise ValueError(f"channel_profile must contain exactly the {layer} channels {applicable}")
    for name in applicable:
        _validate_channel_entry(profile[name], name, layer=layer, goal_mode=goal_mode,
                                lambda_status=lambda_status, mode=mode)
    return applicable


def _channel_bounds(entry) -> tuple[float, float]:
    state = entry["state"]
    if state == "DEFINED":
        value = float(entry["value"])
        return value, value
    if state == "INTERVAL":
        return float(entry["interval"][0]), float(entry["interval"][1])
    # UNKNOWN contributes the worst-case unit interval; NOT_APPLICABLE is
    # excluded from aggregation by the layer/lambda rules before this point.
    return 0.0, 1.0


def _composite_bounds(viability: float, bounds: list[tuple[float, float]],
                      weights, sigma: float) -> list[float]:
    lower = composite_A(viability, [lo for lo, _ in bounds], weights, sigma=sigma)
    upper = composite_A(viability, [hi for _, hi in bounds], weights, sigma=sigma)
    return [float(lower), float(upper)]


def _convention_share_bounds(report, convention: str, *, mode: str) -> tuple[float, float]:
    key = SHARE_KEYS[ORDER_CONVENTIONS.index(convention)]
    total = float(report["joint_di_bits"])
    if total <= TOL:
        return 0.0, 1.0  # share unidentifiable: any value in [0,1] is admissible
    if mode == "INTERVAL":
        interval = report["share_intervals"][convention]
        return float(interval[0]), float(interval[1])
    value = float(report[key])
    return value, value


def _compute_conventions(*, channel_profile: dict, applicable: tuple[str, ...],
                         attribution: dict, layer: str, mode: str,
                         viability: float) -> dict:
    """Per-partition/per-convention composite points (POINT) or intervals (INTERVAL)."""
    weights = attribution["weights"]
    sigma = float(attribution.get("sigma", 1.0))
    if layer == "L0":
        report = attribution["attribution_report"]
        share = report.get("internal_causal_share")
        bounds = []
        for name in applicable:
            if name == "a_org":
                if share is None:
                    bounds.append((0.0, 1.0))
                else:
                    bounds.append((float(share), float(share)))
            else:
                bounds.append(_channel_bounds(channel_profile[name]))
        result = _composite_bounds(viability, bounds, weights, sigma)
        return {"L0_INTERNAL_CAUSAL": result if mode == "INTERVAL" else result[0]}
    partitions = {"registered": attribution["registered_partition"]}
    partitions.update(attribution.get("alternative_partitions", {}))
    composites = {}
    for partition_name, report in partitions.items():
        composites[partition_name] = {}
        for convention in ORDER_CONVENTIONS:
            share_bounds = _convention_share_bounds(report, convention, mode=mode)
            bounds = []
            for name in applicable:
                if name == "a_org":
                    bounds.append(share_bounds)
                else:
                    bounds.append(_channel_bounds(channel_profile[name]))
            interval = _composite_bounds(viability, bounds, weights, sigma)
            composites[partition_name][convention] = (
                interval if mode == "INTERVAL" else interval[0])
    return composites


def _spread(values: list) -> float:
    return float(max(values) - min(values))


def _sensitivity_summary(composites: dict, *, layer: str, mode: str) -> dict:
    if layer == "L0":
        value = composites["L0_INTERNAL_CAUSAL"]
        if mode == "INTERVAL":
            return {"overall_composite_range": list(value), "order_spread": 0.0,
                    "semantic_partition_spread": 0.0, "flags": [],
                    "grade": GRADE_INTERVAL}
        return {"overall_composite_range": [value, value], "order_spread": 0.0,
                "semantic_partition_spread": 0.0, "flags": [], "grade": GRADE_L0}
    if mode == "POINT":
        registered = [composites["registered"][c] for c in ORDER_CONVENTIONS]
        numeric = [v for partition in composites.values() for v in partition.values()]
        order_spread = _spread(registered)
        semantic_spread = max(
            _spread([composites[p][c] for p in composites]) for c in ORDER_CONVENTIONS)
        overall = [min(numeric), max(numeric)]
    else:
        # INTERVAL mode: spreads are computed on convention interval MIDPOINTS
        # (declared summary).  Identical convention intervals mean the
        # conventions agree despite uncertainty; the full uncertainty hull is
        # reported separately as overall_composite_range and never doubles as
        # the sensitivity definition.
        registered = [composites["registered"][c] for c in ORDER_CONVENTIONS]
        registered_mids = [0.5 * (lo + hi) for lo, hi in registered]
        order_spread = _spread(registered_mids)
        semantic_spread = max(
            _spread([0.5 * (composites[p][c][0] + composites[p][c][1])
                     for p in composites])
            for c in ORDER_CONVENTIONS)
        overall = [min(lo for p in composites.values() for lo, _ in p.values()),
                   max(hi for p in composites.values() for _, hi in p.values())]
    flags = []
    if order_spread > ORDER_SENSITIVITY_THRESHOLD:
        flags.append("ORDER_SENSITIVE")
    if semantic_spread > SEMANTIC_SENSITIVITY_THRESHOLD:
        flags.append("MODEL_SENSITIVE")
    if mode == "POINT":
        grade = GRADE_SENSITIVE if flags else GRADE_POINT
    else:
        grade = GRADE_INTERVAL_SENSITIVE if flags else GRADE_INTERVAL
    return {"overall_composite_range": [float(overall[0]), float(overall[1])],
            "order_spread": float(order_spread),
            "semantic_partition_spread": float(semantic_spread),
            "flags": flags, "grade": grade}


def _zero_total_flow(attribution: dict, layer: str) -> bool:
    if layer == "L0":
        report = attribution["attribution_report"]
        return float(report["f_int_bits"]) + float(report["f_ext_bits"]) <= TOL
    return float(attribution["registered_partition"]["joint_di_bits"]) <= TOL


def _validate_attribution(attribution: dict, *, layer: str, mode: str,
                          channel_profile: dict, applicable: tuple[str, ...],
                          viability: float) -> dict:
    if not isinstance(attribution, dict):
        raise ValueError("attribution block must be an object")
    weights = attribution.get("weights")
    if not isinstance(weights, (list, tuple)) or len(weights) != len(applicable):
        raise ValueError("attribution weights must match the applicable channel count")
    weights = tuple(float(w) for w in weights)
    if any(not math.isfinite(w) or w <= 0.0 for w in weights):
        raise ValueError("certificate weights must be strictly positive (interior simplex)")
    if abs(math.fsum(weights) - 1.0) > 1e-9:
        raise ValueError("certificate weights must sum to one")
    sigma = float(attribution.get("sigma", 1.0))
    if not math.isfinite(sigma) or sigma <= 0.0:
        raise ValueError("sigma must be positive")
    if layer == "L0":
        if "attribution_report" not in attribution:
            raise ValueError("L0 requires attribution_report (L0_INTERNAL_CAUSAL)")
        if "registered_partition" in attribution or "alternative_partitions" in attribution:
            raise ValueError("L0 must not carry L1+ RNI/NRI partition structure")
        _validate_l0_report(attribution["attribution_report"])
    else:
        if "registered_partition" not in attribution:
            raise ValueError("L1/L2 requires registered_partition")
        _validate_partition_report(attribution["registered_partition"],
                                   "registered_partition", mode=mode)
        alternatives = attribution.get("alternative_partitions", {})
        if not isinstance(alternatives, dict):
            raise ValueError("alternative_partitions must be an object")
        for name, report in alternatives.items():
            _validate_partition_report(report, f"alternative_partitions.{name}", mode=mode)
    composites = _compute_conventions(
        channel_profile=channel_profile, applicable=applicable,
        attribution=attribution, layer=layer, mode=mode, viability=viability)
    summary = _sensitivity_summary(composites, layer=layer, mode=mode)
    if _zero_total_flow(attribution, layer) and mode == "INTERVAL":
        summary["grade"] = GRADE_ZERO_FLOW
    # a_org consistency with the registered primary share.
    org_entry = channel_profile["a_org"]
    if layer == "L0":
        share = attribution["attribution_report"].get("internal_causal_share")
        if org_entry["state"] == "DEFINED":
            if share is None or abs(float(org_entry["value"]) - float(share)) > TOL:
                raise ValueError("L0 a_org.value must equal the internal-causal share")
        elif org_entry["state"] == "INTERVAL":
            if share is not None:
                raise ValueError("L0 a_org INTERVAL is only for zero-total-flow unidentifiability")
            if any(abs(a - b) > TOL for a, b in zip(org_entry["interval"], [0.0, 1.0])):
                raise ValueError("L0 zero-flow a_org interval must be [0,1]")
    else:
        registered = attribution["registered_partition"]
        if org_entry["state"] == "DEFINED":
            share = registered["normative_share_RNI"]
            if share is None or abs(float(org_entry["value"]) - float(share)) > TOL:
                raise ValueError("a_org.value must equal the registered RNI share")
        elif org_entry["state"] == "INTERVAL":
            if float(registered["joint_di_bits"]) <= TOL:
                if any(abs(a - b) > TOL for a, b in zip(org_entry["interval"], [0.0, 1.0])):
                    raise ValueError("zero-total-flow a_org interval must be [0,1]")
            else:
                expected = registered["share_intervals"]["RNI"]
                if any(abs(a - b) > TOL for a, b in zip(org_entry["interval"], expected)):
                    raise ValueError("a_org interval must equal the registered RNI share interval")
    return {"composites": composites, "summary": summary}


def _expected_ceiling(cert: dict) -> str:
    unknown = (cert["surgery_history"] is None
               or cert["source_registration"] != "COMPLETE"
               or cert["registration_completeness"] != "COMPLETE"
               or cert["lambda_status"] == "UNKNOWN"
               or (cert["layer"] == "L2" and cert["lambda_status"] != "DEFINED"))
    if unknown:
        return "LIMITED"
    if cert["mechanism_evidence"] == "SCM_AUDITED":
        return "SCM_AUDITED"
    return "REGISTERED_COMPLETE"


def _r19_ceiling(cert: dict) -> str:
    base = _expected_ceiling(cert)
    if base == "LIMITED":
        return "LIMITED"
    if cert.get("unknown_channels"):
        return "LIMITED"
    for reason in cert.get("degradation_reasons", []):
        if reason in REFLECTION_DEGRADATION_REASONS:
            return "LIMITED"
    return base


def _degradation_inventory(profile: dict) -> tuple[list[str], list[str]]:
    reasons, unknown = [], []
    for name, entry in profile.items():
        if entry["state"] == "UNKNOWN":
            unknown.append(name)
        if entry["state"] == "INTERVAL" and name == "a_ref":
            reasons.append(entry["degradation_reason"])
        if entry["state"] == "INTERVAL" and name == "a_goal":
            reason = entry.get("degradation_reason")
            if reason:
                reasons.append(reason)
    return sorted(set(reasons)), sorted(unknown)


def _historical_profile(cert: dict) -> dict:
    return {
        "scope": HISTORICAL_FORMATION_SCOPE,
        "formation_status": formation_status(cert["surgery_history"]),
        "surgery_history": cert["surgery_history"],
        "source_registration": cert["source_registration"],
        "lambda_status": cert["lambda_status"],
        "Lambda": cert["Lambda"],
        "time_origin": cert["lambda_time_origin"],
        "counterfactual_scope": cert["lambda_counterfactual_scope"],
        "evidence_only_not_scalar": True,
    }


def make_r19_audit_certificate(*, layer: str, channel_profile: dict, attribution: dict,
                               viability_state: float, defense_readiness: float,
                               surgery_history, lambda_value, lambda_status: str,
                               source_registration: str, mechanism_evidence: str,
                               goal_mode: str, lambda_time_origin: str,
                               lambda_counterfactual_scope: str,
                               model_hash=None, evidence_hash=None,
                               weights=None, sigma: float = 1.0) -> dict:
    """Produce an R19 certificate; mode is inferred from the channel states.

    POINT mode requires every applicable channel DEFINED and exports the
    registered primary-convention scalar.  INTERVAL mode forbids forced point
    values, propagates composite intervals exactly by coordinatewise
    monotonicity, and exports no scalar.  Sensitivity flags, spreads, grades,
    degradation inventories, and the evidence ceiling are recomputed here;
    callers cannot suppress them.
    """
    if layer not in LAYER_CHANNELS:
        raise ValueError("layer must be L0, L1, or L2")
    if lambda_status not in {"DEFINED", "NOT_APPLICABLE", "UNKNOWN"}:
        raise ValueError("invalid lambda_status")
    if lambda_status == "DEFINED":
        lambda_value = _unit(lambda_value, "Lambda")
    elif lambda_value is not None:
        raise ValueError("N/A or UNKNOWN Lambda must be null")
    if layer == "L2" and lambda_status == "NOT_APPLICABLE":
        raise ValueError("L2 requires DEFINED or UNKNOWN Lambda, not N/A")
    if layer == "L0" and lambda_status == "DEFINED":
        raise ValueError("L0 has no reflection channel; Lambda must be N/A or UNKNOWN")
    validate_lambda_time_origin(lambda_time_origin, lambda_counterfactual_scope)
    if lambda_status == "DEFINED" and lambda_time_origin not in {
            "AUDIT_CURRENT_REMOVAL", "ORIGINAL_IMPLANT_PREVENTION"}:
        raise ValueError("DEFINED Lambda requires an explicit counterfactual time origin")
    if lambda_status == "NOT_APPLICABLE" and lambda_time_origin != "NOT_APPLICABLE":
        raise ValueError("NOT_APPLICABLE Lambda requires NOT_APPLICABLE time origin")
    if lambda_status == "UNKNOWN" and lambda_time_origin != "UNKNOWN":
        raise ValueError("UNKNOWN Lambda requires UNKNOWN time origin")
    org_mode = "L0_INTERNAL" if layer == "L0" else "L1_NORMATIVE_NR"
    viability_state = _unit(viability_state, "viability_state")
    defense_readiness = _unit(defense_readiness, "defense_readiness")
    applicable = LAYER_CHANNELS[layer]
    states = {channel_profile[name]["state"] for name in applicable}
    if states <= {"DEFINED"}:
        mode = "POINT"
    else:
        mode = "INTERVAL"
    profile = json.loads(json.dumps(channel_profile))
    _validate_channel_profile(profile, layer=layer, goal_mode=goal_mode,
                              lambda_status=lambda_status, mode=mode)
    attribution = json.loads(json.dumps(attribution))
    if weights is not None:
        attribution["weights"] = [float(w) for w in weights]
    attribution.setdefault("sigma", float(sigma))
    computed = _validate_attribution(attribution, layer=layer, mode=mode,
                                     channel_profile=profile, applicable=applicable,
                                     viability=viability_state)
    composites, summary = computed["composites"], computed["summary"]
    attribution["composite_by_convention"] = composites
    attribution["overall_composite_range"] = summary["overall_composite_range"]
    attribution["order_spread"] = summary["order_spread"]
    attribution["semantic_partition_spread"] = summary["semantic_partition_spread"]
    reasons, unknown = _degradation_inventory(profile)
    flags = summary["flags"]
    grade = summary["grade"]
    if mode == "POINT":
        if layer == "L0":
            primary = composites["L0_INTERNAL_CAUSAL"]
        else:
            primary = composites["registered"]["RNI"]
        state_autonomy = float(primary)
        state_autonomy_interval = None
        warning = ""
        if flags:
            warning = (
                "Registered attribution conventions disagree beyond the post hoc "
                "frozen internal engineering threshold(s); the scalar composite is "
                "sensitivity-qualified and must be read together with channel_profile "
                "and the attribution block. A near-one RNI share with a near-zero NRI "
                "share is an ordering convention, not an order-free causal fraction.")
    else:
        state_autonomy = None
        state_autonomy_interval = list(summary["overall_composite_range"])
        warning = (
            "INTERVAL certificate: insufficient information for a point export "
            "(interval/unknown channel states or unidentifiable shares). The composite "
            "is reported as an interval propagated by coordinatewise monotonicity; no "
            "scalar may be exported. Degradation reasons and unknown channels are "
            "listed explicitly.")
        if flags:
            warning += (" Registered conventions additionally disagree beyond the post "
                        "hoc frozen internal threshold(s); the interval is "
                        "sensitivity-qualified.")
    cert = {
        "layer": layer,
        "construct_scope": ("internal_causal_only" if layer == "L0"
                            else "normative_structure_required"),
        "channel_schema_version": R19_CHANNEL_SCHEMA_VERSION,
        "certificate_mode": mode,
        "org_mode": org_mode,
        "goal_mode": goal_mode,
        "state_readiness_version": "R15_SPLIT",
        "model_hash": model_hash,
        "evidence_hash": evidence_hash,
        "state_autonomy": state_autonomy,
        "state_autonomy_interval": state_autonomy_interval,
        "viability_state": viability_state,
        "defense_readiness": defense_readiness,
        "surgery_history": surgery_history,
        "Lambda": lambda_value,
        "lambda_status": lambda_status,
        "source_registration": source_registration,
        "registration_completeness": source_registration,
        "mechanism_evidence": mechanism_evidence,
        "evidence_ceiling": None,
        "external_construct_validation": False,
        "integrity_certificate": False,
        "lambda_time_origin": lambda_time_origin,
        "lambda_counterfactual_scope": lambda_counterfactual_scope,
        "channel_profile": profile,
        "sensitivity_flags": list(flags),
        "composite_scalar_grade": grade,
        "scalar_export_warning": warning,
        "threshold_provenance": THRESHOLD_PROVENANCE,
        "degradation_reasons": reasons,
        "unknown_channels": unknown,
    }
    if layer == "L0":
        cert["attribution_report"] = attribution["attribution_report"]
        cert["attribution_sensitivity"] = {
            "weights": attribution["weights"], "sigma": attribution["sigma"],
            "composite_by_convention": composites,
            "overall_composite_range": attribution["overall_composite_range"],
            "order_spread": attribution["order_spread"],
            "semantic_partition_spread": attribution["semantic_partition_spread"],
            "note": "L0 internal-causal only; no RNI/NRI/order conventions at L0.",
        }
    else:
        cert["attribution_sensitivity"] = attribution
    cert["evidence_ceiling"] = _r19_ceiling(cert)
    cert["current_structural_profile"] = {
        "scope": CURRENT_STRUCTURAL_SCOPE,
        "state_autonomy": state_autonomy,
        "state_autonomy_interval": state_autonomy_interval,
        "viability_state": viability_state,
        "defense_readiness": defense_readiness,
        "composite_scale": COMPOSITE_SCALE,
        "composite_range_across_conventions": summary["overall_composite_range"],
        "sensitivity_flags": list(flags),
        "composite_scalar_grade": grade,
        "full_channel_profile_field": "channel_profile",
    }
    cert["historical_formation_profile"] = _historical_profile(cert)
    errors = validate_r19_certificate(cert)
    if errors:
        raise ValueError("invalid R19 certificate: " + "; ".join(errors))
    return cert


def _validate_base_point(cert: dict) -> list[str]:
    """POINT mode: full reuse of the R17 validator on the stripped base."""
    base = dict(cert)
    for field in R19_EXTRA_FIELDS:
        base.pop(field, None)
    base.pop("attribution_report", None)
    base.pop("attribution_sensitivity", None)
    base["channel_schema_version"] = R17_CHANNEL_SCHEMA_VERSION
    current = dict(base.get("current_structural_profile", {}))
    for field in ("composite_range_across_conventions", "sensitivity_flags",
                  "composite_scalar_grade", "full_channel_profile_field",
                  "state_autonomy_interval"):
        current.pop(field, None)
    base["current_structural_profile"] = current
    return validate_r17_certificate(base)


def _validate_base_interval(cert: dict) -> list[str]:
    """INTERVAL mode: R17 rules on the upper-bound point projection.

    The projection (state_autonomy := interval upper bound) is a proof device
    solely to reuse the registration/lambda/hash/profile rules; the actual
    interval semantics (null point export, ordered bounds, upper <= viability)
    are checked explicitly below and in validate_r19_certificate.
    """
    interval = cert.get("state_autonomy_interval")
    if not isinstance(interval, (list, tuple)) or len(interval) != 2:
        return ["INTERVAL certificate requires state_autonomy_interval [lower, upper]"]
    try:
        lower = _unit(interval[0], "state_autonomy_interval lower")
        upper = _unit(interval[1], "state_autonomy_interval upper")
    except ValueError as exc:
        return [str(exc)]
    if lower > upper:
        return ["state_autonomy_interval must be ordered"]
    errors = []
    if cert.get("state_autonomy") is not None:
        errors.append("INTERVAL certificate must not export a point state_autonomy")
    if upper > float(cert["viability_state"]) + 1e-12:
        errors.append("state_autonomy_interval upper bound must not exceed viability_state")
    base = dict(cert)
    for field in R19_EXTRA_FIELDS:
        base.pop(field, None)
    base.pop("attribution_report", None)
    base.pop("attribution_sensitivity", None)
    base["channel_schema_version"] = R17_CHANNEL_SCHEMA_VERSION
    base["state_autonomy"] = upper
    base["evidence_ceiling"] = _expected_ceiling(cert)
    current = dict(base.get("current_structural_profile", {}))
    for field in ("composite_range_across_conventions", "sensitivity_flags",
                  "composite_scalar_grade", "full_channel_profile_field",
                  "state_autonomy_interval"):
        current.pop(field, None)
    current["state_autonomy"] = upper
    base["current_structural_profile"] = current
    errors.extend(validate_r17_certificate(base))
    actual_current = cert.get("current_structural_profile", {})
    if actual_current.get("state_autonomy") is not None:
        errors.append("current profile must not export a point in INTERVAL mode")
    if actual_current.get("state_autonomy_interval") != list(interval):
        errors.append("current profile state_autonomy_interval drift")
    return errors


def validate_r19_certificate(cert: dict) -> list[str]:
    errors = []
    if not isinstance(cert, dict):
        return ["certificate must be an object"]
    for field in R19_EXTRA_FIELDS:
        if field not in cert:
            errors.append(f"missing R19 field {field}")
    if cert.get("channel_schema_version") != R19_CHANNEL_SCHEMA_VERSION:
        errors.append("channel_schema_version must be R19_CHANNEL_SCHEMA_V1")
    if errors:
        return errors
    mode = cert.get("certificate_mode")
    if mode not in CERTIFICATE_MODES:
        return errors + ["certificate_mode must be POINT or INTERVAL"]
    layer = cert.get("layer")
    if layer not in LAYER_CHANNELS:
        return errors + ["invalid layer"]
    if mode == "POINT":
        errors.extend(_validate_base_point(cert))
    else:
        errors.extend(_validate_base_interval(cert))
    if errors:
        return errors
    try:
        applicable = _validate_channel_profile(
            cert["channel_profile"], layer=layer, goal_mode=cert["goal_mode"],
            lambda_status=cert["lambda_status"], mode=mode)
    except ValueError as exc:
        return errors + [str(exc)]
    profile = cert["channel_profile"]
    if "a_ref" in profile and cert["lambda_status"] == "DEFINED":
        ref_lambda = profile["a_ref"].get("Lambda")
        if ref_lambda is None or abs(float(ref_lambda) - float(cert["Lambda"])) > TOL:
            errors.append("a_ref.Lambda drift from certificate Lambda")
    attribution = cert.get("attribution_sensitivity")
    if layer == "L0":
        if "attribution_report" not in cert:
            return errors + ["L0 certificate requires attribution_report"]
        attribution = dict(attribution or {})
        attribution["attribution_report"] = cert["attribution_report"]
    if not isinstance(attribution, dict):
        return errors + ["attribution_sensitivity must be an object"]
    try:
        computed = _validate_attribution(
            attribution, layer=layer, mode=mode, channel_profile=profile,
            applicable=applicable, viability=float(cert["viability_state"]))
    except ValueError as exc:
        return errors + [str(exc)]
    summary = computed["summary"]
    composites = computed["composites"]
    recorded = attribution.get("composite_by_convention")
    if not isinstance(recorded, dict) or set(recorded) != set(composites):
        errors.append("composite_by_convention drift")
    else:
        for partition_name, partition in composites.items():
            if isinstance(partition, dict):
                for convention, value in partition.items():
                    other = recorded[partition_name].get(convention)
                    if mode == "POINT":
                        if other is None or abs(float(other) - float(value)) > TOL:
                            errors.append("composite_by_convention drift")
                    else:
                        if (not isinstance(other, (list, tuple)) or len(other) != 2
                                or any(abs(float(a) - float(b)) > TOL
                                       for a, b in zip(other, value))):
                            errors.append("composite_by_convention interval drift")
            else:
                other = recorded[partition_name]
                if mode == "POINT":
                    if abs(float(other) - float(partition)) > TOL:
                        errors.append("composite_by_convention drift")
                elif (not isinstance(other, (list, tuple))
                        or any(abs(float(a) - float(b)) > TOL
                               for a, b in zip(other, partition))):
                    errors.append("composite_by_convention interval drift")
    for key in ("overall_composite_range", "order_spread", "semantic_partition_spread"):
        expected, actual = summary[key], attribution.get(key)
        if key == "overall_composite_range":
            if (not isinstance(actual, (list, tuple)) or len(actual) != 2
                    or any(abs(float(a) - float(b)) > TOL
                           for a, b in zip(actual, expected))):
                errors.append(f"attribution {key} drift")
        elif actual is None or abs(float(actual) - float(expected)) > TOL:
            errors.append(f"attribution {key} drift")
    flags = cert.get("sensitivity_flags")
    if not isinstance(flags, list) or set(flags) - SENSITIVITY_FLAG_VALUES:
        errors.append("sensitivity_flags must be a list of registered flag values")
    elif sorted(flags) != sorted(summary["flags"]):
        errors.append("sensitivity_flags must match the recomputed decomposed spreads "
                      "(required flags cannot be suppressed)")
    if cert.get("composite_scalar_grade") != summary["grade"]:
        errors.append("composite_scalar_grade drift")
    warning = cert.get("scalar_export_warning")
    if not isinstance(warning, str):
        errors.append("scalar_export_warning must be a string")
    elif (mode == "INTERVAL" or summary["flags"]) and not warning.strip():
        errors.append("flagged or interval certificates must carry a scalar-export warning")
    if cert.get("threshold_provenance") != THRESHOLD_PROVENANCE:
        errors.append("threshold_provenance must declare the post hoc frozen status")
    reasons, unknown = _degradation_inventory(profile)
    if cert.get("degradation_reasons") != reasons:
        errors.append("degradation_reasons drift")
    if cert.get("unknown_channels") != unknown:
        errors.append("unknown_channels drift")
    if cert.get("evidence_ceiling") != _r19_ceiling(cert):
        errors.append("evidence_ceiling must respect unknown/degraded channels")
    if mode == "POINT":
        if cert.get("state_autonomy_interval") is not None:
            errors.append("POINT certificate must not carry state_autonomy_interval")
        primary = (composites["L0_INTERNAL_CAUSAL"] if layer == "L0"
                   else composites["registered"]["RNI"])
        if abs(float(cert["state_autonomy"]) - float(primary)) > TOL:
            errors.append("state_autonomy must equal the registered primary-convention composite")
    else:
        expected_interval = summary["overall_composite_range"]
        actual = cert.get("state_autonomy_interval")
        if (not isinstance(actual, (list, tuple))
                or any(abs(float(a) - float(b)) > TOL
                       for a, b in zip(actual, expected_interval))):
            errors.append("state_autonomy_interval must equal the overall composite hull")
    current = cert.get("current_structural_profile", {})
    if current.get("composite_range_across_conventions") != summary["overall_composite_range"]:
        errors.append("current profile composite range drift")
    if current.get("sensitivity_flags") != flags:
        errors.append("current profile sensitivity flags drift")
    if current.get("composite_scalar_grade") != summary["grade"]:
        errors.append("current profile scalar grade drift")
    if current.get("full_channel_profile_field") != "channel_profile":
        errors.append("current profile must reference the full channel profile")
    if current.get("composite_scale") != COMPOSITE_SCALE:
        errors.append("current composite must remain marked protocol-normalized")
    return errors


def write_r19_certificate(path: str, cert: dict) -> None:
    errors = validate_r19_certificate(cert)
    if errors:
        raise ValueError("invalid R19 certificate: " + "; ".join(errors))
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(cert, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def produce_r19_certificate(*, channel_profile: dict, attribution: dict,
                            lambda_time_origin: str, lambda_counterfactual_scope: str,
                            **kwargs) -> dict:
    """R19 producer.  POINT-mode L1/L2 certificates may also be built through
    the R17 base chain for compatibility; this direct producer covers every
    layer and both modes with one contract."""
    return make_r19_audit_certificate(
        channel_profile=channel_profile, attribution=attribution,
        lambda_time_origin=lambda_time_origin,
        lambda_counterfactual_scope=lambda_counterfactual_scope, **kwargs)
