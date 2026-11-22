"""R20 detection-complete, interval-honest audit certificate schema.

R19 remains a compatibility layer (read-only replay of R19 artifacts).  R20
closes the four gaps identified in the R19 review:

1. **Data-driven near-zero detection inside the formal certificate.**  Every
   L1/L2 attribution convention carries a ``convention_report`` with
   ``convention_status`` (DATA_BELOW_LIMIT / DATA_ABOVE_LIMIT /
   INDETERMINATE_NEAR_ZERO, or POINT_EXACT / NOT_EVALUABLE), a
   ``share_interval``, a ``composite_interval``, the detection limit and its
   rule/value provenance, and the diagnostic plug-in outputs.  The decision
   uses ONLY estimable inputs (plug-in share + bootstrap percentile interval
   -> basic bias-corrected interval -> three-state classification); the exact
   truth never enters a deployable decision.  POINT certificates (exact
   white-box enumerations) label their near-zero classification
   ORACLE_ASSISTED_VALIDATION_FIXTURE_ONLY_NOT_DEPLOYABLE.
2. **Interval sensitivity is a status system, not midpoint agreement.**
   CONFIRMED_SENSITIVE (minimum possible convention separation exceeds the
   threshold), NO_CONFIRMED_SENSITIVITY (worst-case spread within threshold),
   INDETERMINATE (overlapping intervals cannot decide), NOT_EVALUABLE (zero
   total flow / unknown inputs).  Identical wide intervals are NEVER read as
   agreement.  ``midpoint_spread_descriptive`` is retained as a descriptive
   statistic only.  Flags fire only on CONFIRMED_SENSITIVE.
3. **Real interval propagation with declared kinds.**  Sampling certificates
   propagate the actual bias-corrected bootstrap share intervals, not
   degenerate [s,s] points.  Every interval carries a kind:
   POINT_EXACT / LOGICAL_ENVELOPE / SAMPLING_BASIC_BOOTSTRAP /
   SAMPLING_PERCENTILE / SAMPLING_NORMAL_APPROX / SENSITIVITY /
   MODEL_SELECTION.  Monotone endpoint propagation is an envelope guarantee
   for the GIVEN input intervals; logical envelopes are explicitly NOT
   statistical confidence intervals.  ``overall_composite_range`` is
   recomputed from the reported convention composite intervals, so the
   certificate and any external summary agree by construction.
4. **Diagnostic plug-in separation.**  The plug-in composite (e.g. the
   sampled NRI value) is stored only as ``diagnostic_plugin_composite``; it
   may lie outside the reported interval and is never exported as the
   certificate's point or interval semantics.

Thresholds remain POST HOC FROZEN internal engineering thresholds (R19
provenance).  The detection RULE is declared before R20 study outcomes; the
limit VALUE is the inherited R19 post hoc frozen constant.  This module is
internal audit machinery, not external construct validation.
"""
from __future__ import annotations

import json
import math

from .aggregate import composite_A
from .formation_audit import formation_status, validate_lambda_time_origin
from .r17_guards import (COMPOSITE_SCALE, CURRENT_STRUCTURAL_SCOPE,
                         HISTORICAL_FORMATION_SCOPE, R17_CHANNEL_SCHEMA_VERSION,
                         validate_r17_certificate)
from . import r19_guards as _r19
from .r19_guards import (CHANNEL_STATES, FLOW_KEYS, LAYER_CHANNELS,
                         ORDER_CONVENTIONS, ORDER_SENSITIVITY_THRESHOLD,
                         SEMANTIC_SENSITIVITY_THRESHOLD, SHARE_KEYS,
                         THRESHOLD_PROVENANCE, TOL,
                         REFLECTION_DEGRADATION_REASONS,
                         _degradation_inventory, _expected_ceiling,
                         _historical_profile, _interval, _nonnegative_int,
                         _optional_unit, _reason, _unit,
                         _validate_l0_report, _validate_ref_entry)
from .r20_detection import (DETECTION_LIMIT, DETECTION_LIMIT_PROVENANCE,
                            DETECTION_RULE_PROVENANCE, DETECTION_RULE_VERSION,
                            ORACLE_RULE_LABEL, basic_bootstrap_bias_corrected_interval,
                            classify_share_interval,
                            oracle_assisted_fixture_classification)

R20_CHANNEL_SCHEMA_VERSION = "R20_CHANNEL_SCHEMA_V1"

INTERVAL_KINDS = frozenset({
    "POINT_EXACT", "LOGICAL_ENVELOPE", "SAMPLING_BASIC_BOOTSTRAP",
    "SAMPLING_PERCENTILE", "SAMPLING_NORMAL_APPROX", "SENSITIVITY",
    "MODEL_SELECTION"})
SAMPLING_KINDS = frozenset({"SAMPLING_BASIC_BOOTSTRAP", "SAMPLING_PERCENTILE",
                            "SAMPLING_NORMAL_APPROX"})
SENSITIVITY_STATUSES = frozenset({
    "CONFIRMED_SENSITIVE", "NO_CONFIRMED_SENSITIVITY", "INDETERMINATE",
    "NOT_EVALUABLE", "NOT_APPLICABLE"})
CONVENTION_STATUSES = frozenset({
    "DATA_BELOW_LIMIT", "DATA_ABOVE_LIMIT", "INDETERMINATE_NEAR_ZERO",
    "POINT_EXACT", "NOT_EVALUABLE"})

GRADE_POINT = "POINT_READING_UNDER_REGISTERED_CONVENTION_ONLY"
GRADE_SENSITIVE = "SENSITIVITY_QUALIFIED_NOT_A_ROBUST_POINT_READING"
GRADE_L0 = "L0_INTERNAL_CAUSAL_POINT_READING"
GRADE_INTERVAL = "INTERVAL_VALUED_NOT_A_POINT_READING"
GRADE_INTERVAL_SENSITIVE = "INTERVAL_VALUED_SENSITIVITY_QUALIFIED"
GRADE_INTERVAL_INDETERMINATE = "INTERVAL_VALUED_SENSITIVITY_INDETERMINATE"
GRADE_ZERO_FLOW = "INTERVAL_ZERO_TOTAL_FLOW_SHARE_UNIDENTIFIED"

R20_EXTRA_FIELDS = (
    "certificate_mode", "channel_profile", "sensitivity_flags",
    "composite_scalar_grade", "scalar_export_warning", "state_autonomy_interval",
    "threshold_provenance", "degradation_reasons", "unknown_channels",
    "sensitivity_status", "detection_policy",
)

DETECTION_POLICY = {
    "detection_limit": DETECTION_LIMIT,
    "rule_version": DETECTION_RULE_VERSION,
    "rule_provenance": DETECTION_RULE_PROVENANCE,
    "limit_provenance": DETECTION_LIMIT_PROVENANCE,
    "oracle_rule_label": ORACLE_RULE_LABEL,
    "deployable_decision_uses_exact_truth": False,
}


def _bounds_of(interval_obj, label: str) -> list[float]:
    if not isinstance(interval_obj, dict):
        raise ValueError(f"{label} must be an interval object {{bounds, kind}}")
    bounds = _interval(interval_obj.get("bounds"), label, required=True)
    kind = interval_obj.get("kind")
    if kind not in INTERVAL_KINDS:
        raise ValueError(f"{label}.kind must be one of {sorted(INTERVAL_KINDS)}")
    return bounds


def _validate_channel_entry_r20(entry, name: str, *, layer: str, goal_mode: str,
                                lambda_status: str, mode: str) -> None:
    # R19 structural rules (states, goal/ref/exec carriers) are unchanged.
    _r19._validate_channel_entry(entry, name, layer=layer, goal_mode=goal_mode,
                                 lambda_status=lambda_status, mode=mode)
    if entry.get("interval") is not None:
        kind = entry.get("interval_kind")
        if kind not in INTERVAL_KINDS:
            raise ValueError(f"channel_profile.{name}.interval_kind is required "
                             f"and must be a registered kind")
        if entry["state"] == "INTERVAL":
            if name == "a_org" and kind not in (
                    "SAMPLING_BASIC_BOOTSTRAP", "SAMPLING_PERCENTILE",
                    "LOGICAL_ENVELOPE"):
                raise ValueError("a_org INTERVAL kind must be sampling or the "
                                 "zero-flow logical envelope")
            if name == "a_goal":
                if goal_mode == "IRL_INTERVAL" and kind != "MODEL_SELECTION":
                    raise ValueError("IRL goal interval kind must be MODEL_SELECTION")
                if goal_mode != "IRL_INTERVAL" and kind != "LOGICAL_ENVELOPE":
                    raise ValueError("degraded structural goal interval kind must "
                                     "be LOGICAL_ENVELOPE")
            if name == "a_ref" and kind != "LOGICAL_ENVELOPE":
                raise ValueError("degraded reflection interval kind must be "
                                 "LOGICAL_ENVELOPE (not a confidence interval)")
    elif entry["state"] == "INTERVAL":
        raise ValueError(f"channel_profile.{name} INTERVAL requires an interval")
    if name == "a_goal" and entry["state"] in {"DEFINED", "INTERVAL"}:
        if entry.get("irl_interval_kind") != "MODEL_SELECTION":
            raise ValueError("a_goal.irl_interval_kind must be MODEL_SELECTION "
                             "(registered identified set)")


def _validate_channel_profile_r20(profile: dict, *, layer: str, goal_mode: str,
                                  lambda_status: str, mode: str) -> tuple[str, ...]:
    if not isinstance(profile, dict):
        raise ValueError("channel_profile must be an object")
    applicable = LAYER_CHANNELS[layer]
    if set(profile) != set(applicable):
        raise ValueError(f"channel_profile must contain exactly the {layer} channels {applicable}")
    for name in applicable:
        _validate_channel_entry_r20(profile[name], name, layer=layer,
                                    goal_mode=goal_mode, lambda_status=lambda_status,
                                    mode=mode)
    return applicable


def _channel_bounds(entry) -> tuple[float, float]:
    state = entry["state"]
    if state == "DEFINED":
        value = float(entry["value"])
        return value, value
    if state == "INTERVAL":
        return float(entry["interval"][0]), float(entry["interval"][1])
    return 0.0, 1.0  # UNKNOWN worst case


def _composite_bounds(viability: float, bounds: list[tuple[float, float]],
                      weights, sigma: float) -> list[float]:
    lower = composite_A(viability, [lo for lo, _ in bounds], weights, sigma=sigma)
    upper = composite_A(viability, [hi for _, hi in bounds], weights, sigma=sigma)
    return [float(lower), float(upper)]


def _validate_partition_report_r20(report, label: str, *, mode: str) -> None:
    # Flow/share consistency is the R19 contract (checked in POINT style so
    # the R19 share_intervals requirement does not apply; R20 replaces it).
    _r19._validate_partition_report(report, label, mode="POINT")
    if mode != "INTERVAL":
        return
    total = float(report["joint_di_bits"])
    percentiles = report.get("share_bootstrap_percentile_95")
    if not isinstance(percentiles, dict):
        raise ValueError(f"{label}.share_bootstrap_percentile_95 is required "
                         "in INTERVAL mode (estimable inputs of the detection rule)")
    for convention, key in zip(ORDER_CONVENTIONS, SHARE_KEYS):
        perc = percentiles.get(convention)
        if total <= TOL:
            if perc is not None:
                raise ValueError(f"{label}.{convention} percentile interval must be "
                                 "null when total flow is zero")
        else:
            if perc is None:
                raise ValueError(f"{label}.{convention} percentile interval required "
                                 "for positive total flow")
            _interval(perc, f"{label}.percentile.{convention}", required=True)


def _zero_total_flow(attribution: dict, layer: str) -> bool:
    if layer == "L0":
        report = attribution["attribution_report"]
        return float(report["f_int_bits"]) + float(report["f_ext_bits"]) <= TOL
    return float(attribution["registered_partition"]["joint_di_bits"]) <= TOL


def _partition_zero_flow(report) -> bool:
    return float(report["joint_di_bits"]) <= TOL


def _compute_convention_reports(*, attribution: dict, channel_profile: dict,
                                applicable: tuple[str, ...], layer: str,
                                mode: str, viability: float) -> dict:
    """Recompute every per-convention detection report from estimable inputs.

    Shared by producer and validator: callers cannot supply statuses.
    """
    weights = attribution["weights"]
    sigma = float(attribution.get("sigma", 1.0))
    other_bounds = {name: _channel_bounds(channel_profile[name])
                    for name in applicable if name != "a_org"}
    others_defined = all(channel_profile[name]["state"] == "DEFINED"
                         for name in applicable if name != "a_org")

    def box(share_bounds):
        return [share_bounds if name == "a_org" else other_bounds[name]
                for name in applicable]

    def comp(share_bounds):
        return _composite_bounds(viability, box(share_bounds), weights, sigma)

    if layer == "L0":
        report = attribution["attribution_report"]
        share = report.get("internal_causal_share")
        share_bounds = (0.0, 1.0) if share is None else (float(share), float(share))
        interval = comp(share_bounds)
        kind = ("LOGICAL_ENVELOPE" if share is None
                else ("POINT_EXACT" if mode == "POINT" else "SAMPLING_BASIC_BOOTSTRAP"))
        return {"L0_INTERNAL_CAUSAL": {
            "convention_status": ("NOT_EVALUABLE" if share is None else
                                  ("POINT_EXACT" if mode == "POINT" else "DATA_ABOVE_LIMIT")),
            "share_interval": (None if share is None else
                               {"bounds": [float(share), float(share)] if mode == "POINT"
                                else list(channel_profile["a_org"]["interval"]),
                                "kind": "POINT_EXACT" if mode == "POINT"
                                else channel_profile["a_org"]["interval_kind"]}),
            "composite_interval": {"bounds": interval, "kind": kind},
            "detection_limit": DETECTION_LIMIT,
            "detection_rule_version": DETECTION_RULE_VERSION,
            "detection_provenance": DETECTION_RULE_PROVENANCE,
            "note": "L0 internal-causal share; no RNI/NRI/order conventions at L0.",
        }}

    partitions = {"registered": attribution["registered_partition"]}
    partitions.update(attribution.get("alternative_partitions", {}))
    reports = {}
    for partition_name, report in partitions.items():
        reports[partition_name] = {}
        zero_flow = _partition_zero_flow(report)
        for convention, key in zip(ORDER_CONVENTIONS, SHARE_KEYS):
            share = report[key]
            base = {"detection_limit": DETECTION_LIMIT,
                    "detection_rule_version": DETECTION_RULE_VERSION,
                    "detection_provenance": DETECTION_RULE_PROVENANCE}
            if zero_flow:
                reports[partition_name][convention] = dict(
                    base, convention_status="NOT_EVALUABLE",
                    share_interval=None, share_bootstrap_percentile_95=None,
                    composite_interval={"bounds": comp((0.0, 1.0)),
                                        "kind": "LOGICAL_ENVELOPE"},
                    composite_interval_sampling=None,
                    diagnostic_plugin_share=None, diagnostic_plugin_composite=None,
                    reason="ZERO_TOTAL_FLOW_SHARE_UNIDENTIFIABLE")
                continue
            share = float(share)
            if mode == "POINT":
                value = comp((share, share))[0]
                reports[partition_name][convention] = dict(
                    base, convention_status="POINT_EXACT",
                    share_interval={"bounds": [share, share], "kind": "POINT_EXACT"},
                    share_bootstrap_percentile_95=None,
                    composite_interval={"bounds": [value, value], "kind": "POINT_EXACT"},
                    composite_interval_sampling=None,
                    diagnostic_plugin_share=None, diagnostic_plugin_composite=None,
                    oracle_detection=oracle_assisted_fixture_classification(share))
                continue
            perc = report["share_bootstrap_percentile_95"][convention]
            decision = basic_bootstrap_bias_corrected_interval(share, perc[0], perc[1])
            status = classify_share_interval(decision)
            sampling_bounds = comp((decision[0], decision[1]))
            if status == "DATA_ABOVE_LIMIT":
                reported = {"bounds": sampling_bounds, "kind": "SAMPLING_BASIC_BOOTSTRAP"}
            else:
                reported = {"bounds": comp((0.0, decision[1])),
                            "kind": "LOGICAL_ENVELOPE"}
            plugin_composite = (comp((share, share))[0] if others_defined else None)
            reports[partition_name][convention] = dict(
                base, convention_status=status,
                share_interval={"bounds": decision, "kind": "SAMPLING_BASIC_BOOTSTRAP"},
                share_bootstrap_percentile_95=[float(perc[0]), float(perc[1])],
                composite_interval=reported,
                composite_interval_sampling={"bounds": sampling_bounds,
                                             "kind": "SAMPLING_BASIC_BOOTSTRAP"},
                diagnostic_plugin_share=share,
                diagnostic_plugin_composite=plugin_composite)
    return reports


def _reported_intervals(convention_reports: dict, partition: str) -> list[list[float]]:
    return [convention_reports[partition][c]["composite_interval"]["bounds"]
            for c in ORDER_CONVENTIONS]


def _spread_stats(intervals: list[list[float]]) -> dict:
    lows = [b[0] for b in intervals]
    highs = [b[1] for b in intervals]
    mids = [0.5 * (b[0] + b[1]) for b in intervals]
    return {
        "min_possible_spread": float(max(0.0, max(lows) - min(highs))),
        "worst_case_spread": float(max(highs) - min(lows)),
        "midpoint_spread_descriptive": float(max(mids) - min(mids)),
    }


def _status_from_stats(stats: dict, threshold: float) -> str:
    if stats["min_possible_spread"] > threshold:
        return "CONFIRMED_SENSITIVE"
    if stats["worst_case_spread"] <= threshold:
        return "NO_CONFIRMED_SENSITIVITY"
    return "INDETERMINATE"


_STATUS_PRIORITY = {"CONFIRMED_SENSITIVE": 3, "INDETERMINATE": 2,
                    "NO_CONFIRMED_SENSITIVITY": 1, "NOT_EVALUABLE": 0,
                    "NOT_APPLICABLE": 0}


def _compute_sensitivity_status(convention_reports: dict, *, layer: str,
                                attribution: dict, channel_profile: dict,
                                applicable: tuple[str, ...]) -> dict:
    if layer == "L0":
        na = {"status": "NOT_APPLICABLE",
              "reason": "L0 has no order conventions or semantic partitions"}
        return {"order": dict(na), "semantic": dict(na)}
    unknown = any(channel_profile[name]["state"] == "UNKNOWN" for name in applicable)
    registered_zero = _partition_zero_flow(attribution["registered_partition"])
    order_evaluable = not unknown and not registered_zero
    if order_evaluable:
        stats = _spread_stats(_reported_intervals(convention_reports, "registered"))
        order = dict(stats, status=_status_from_stats(stats, ORDER_SENSITIVITY_THRESHOLD))
    else:
        order = {"status": "NOT_EVALUABLE",
                 "reason": ("UNKNOWN_CHANNEL_INPUT_MISSING" if unknown
                            else "ZERO_TOTAL_FLOW_SHARE_UNIDENTIFIABLE"),
                 "min_possible_spread": None, "worst_case_spread": None,
                 "midpoint_spread_descriptive": None}
    partitions = list(convention_reports)
    any_zero = any(_partition_zero_flow(attribution["registered_partition"]
                                        if p == "registered"
                                        else attribution["alternative_partitions"][p])
                   for p in partitions)
    semantic_evaluable = not unknown and not any_zero
    if semantic_evaluable:
        per_convention = {}
        for convention in ORDER_CONVENTIONS:
            intervals = [convention_reports[p][convention]["composite_interval"]["bounds"]
                         for p in partitions]
            stats = _spread_stats(intervals)
            per_convention[convention] = dict(
                stats, status=_status_from_stats(stats, SEMANTIC_SENSITIVITY_THRESHOLD))
        status = max((per_convention[c]["status"] for c in ORDER_CONVENTIONS),
                     key=lambda s: _STATUS_PRIORITY[s])
        semantic = {
            "status": status,
            "min_possible_spread": max(per_convention[c]["min_possible_spread"]
                                       for c in ORDER_CONVENTIONS),
            "worst_case_spread": max(per_convention[c]["worst_case_spread"]
                                     for c in ORDER_CONVENTIONS),
            "midpoint_spread_descriptive": max(
                per_convention[c]["midpoint_spread_descriptive"]
                for c in ORDER_CONVENTIONS),
            "per_convention": per_convention,
        }
    else:
        semantic = {"status": "NOT_EVALUABLE",
                    "reason": ("UNKNOWN_CHANNEL_INPUT_MISSING" if unknown
                               else "ZERO_TOTAL_FLOW_SHARE_UNIDENTIFIABLE"),
                    "min_possible_spread": None, "worst_case_spread": None,
                    "midpoint_spread_descriptive": None}
    return {"order": order, "semantic": semantic}


def _overall_range(convention_reports: dict, *, layer: str) -> list[float]:
    if layer == "L0":
        bounds = convention_reports["L0_INTERNAL_CAUSAL"]["composite_interval"]["bounds"]
        return [float(bounds[0]), float(bounds[1])]
    all_bounds = [rep["composite_interval"]["bounds"]
                  for partition in convention_reports.values()
                  for rep in partition.values()]
    return [float(min(b[0] for b in all_bounds)), float(max(b[1] for b in all_bounds))]


def _flags_and_grade(sensitivity: dict, *, layer: str, mode: str,
                     zero_flow: bool) -> tuple[list[str], str]:
    if layer == "L0":
        if mode == "POINT":
            return [], GRADE_L0
        return [], (GRADE_ZERO_FLOW if zero_flow else GRADE_INTERVAL)
    flags = []
    if sensitivity["order"]["status"] == "CONFIRMED_SENSITIVE":
        flags.append("ORDER_SENSITIVE")
    if sensitivity["semantic"]["status"] == "CONFIRMED_SENSITIVE":
        flags.append("MODEL_SENSITIVE")
    if mode == "POINT":
        return flags, (GRADE_SENSITIVE if flags else GRADE_POINT)
    if zero_flow:
        return flags, GRADE_ZERO_FLOW
    if flags:
        return flags, GRADE_INTERVAL_SENSITIVE
    if (sensitivity["order"]["status"] == "INDETERMINATE"
            or sensitivity["semantic"]["status"] == "INDETERMINATE"):
        return flags, GRADE_INTERVAL_INDETERMINATE
    return flags, GRADE_INTERVAL


def _validate_attribution_r20(attribution: dict, *, layer: str, mode: str,
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
        _validate_partition_report_r20(attribution["registered_partition"],
                                       "registered_partition", mode=mode)
        alternatives = attribution.get("alternative_partitions", {})
        if not isinstance(alternatives, dict):
            raise ValueError("alternative_partitions must be an object")
        for name, report in alternatives.items():
            _validate_partition_report_r20(report, f"alternative_partitions.{name}",
                                           mode=mode)
    convention_reports = _compute_convention_reports(
        attribution=attribution, channel_profile=channel_profile,
        applicable=applicable, layer=layer, mode=mode, viability=viability)
    sensitivity = _compute_sensitivity_status(
        convention_reports, layer=layer, attribution=attribution,
        channel_profile=channel_profile, applicable=applicable)
    overall = _overall_range(convention_reports, layer=layer)
    zero_flow = _zero_total_flow(attribution, layer)
    flags, grade = _flags_and_grade(sensitivity, layer=layer, mode=mode,
                                    zero_flow=zero_flow)
    # a_org consistency with the registered primary convention.
    org_entry = channel_profile["a_org"]
    if layer == "L0":
        share = attribution["attribution_report"].get("internal_causal_share")
        if org_entry["state"] == "DEFINED":
            if share is None or abs(float(org_entry["value"]) - float(share)) > TOL:
                raise ValueError("L0 a_org.value must equal the internal-causal share")
        else:
            if share is not None:
                raise ValueError("L0 a_org INTERVAL is only for zero-total-flow unidentifiability")
            if any(abs(a - b) > TOL for a, b in zip(org_entry["interval"], [0.0, 1.0])):
                raise ValueError("L0 zero-flow a_org interval must be [0,1]")
            if org_entry.get("interval_kind") != "LOGICAL_ENVELOPE":
                raise ValueError("L0 zero-flow a_org kind must be LOGICAL_ENVELOPE")
    else:
        registered = attribution["registered_partition"]
        rni_report = convention_reports["registered"]["RNI"]
        if org_entry["state"] == "DEFINED":
            share = registered["normative_share_RNI"]
            if share is None or abs(float(org_entry["value"]) - float(share)) > TOL:
                raise ValueError("a_org.value must equal the registered RNI share")
            if mode != "POINT":
                raise ValueError("sampling certificates must carry a_org as INTERVAL "
                                 "with the declared share interval, not a forced point")
        else:
            if _partition_zero_flow(registered):
                if any(abs(a - b) > TOL for a, b in zip(org_entry["interval"], [0.0, 1.0])):
                    raise ValueError("zero-total-flow a_org interval must be [0,1]")
                if org_entry.get("interval_kind") != "LOGICAL_ENVELOPE":
                    raise ValueError("zero-flow a_org kind must be LOGICAL_ENVELOPE")
            else:
                expected = rni_report["share_interval"]
                if expected is None:
                    raise ValueError("positive-flow INTERVAL a_org requires the RNI share interval")
                if any(abs(a - b) > TOL for a, b in
                       zip(org_entry["interval"], expected["bounds"])):
                    raise ValueError("a_org interval must equal the registered RNI share interval")
                if org_entry.get("interval_kind") != expected["kind"]:
                    raise ValueError("a_org interval kind must equal the RNI share interval kind")
    return {"convention_reports": convention_reports, "sensitivity": sensitivity,
            "overall": overall, "flags": flags, "grade": grade}


def _r20_ceiling(cert: dict) -> str:
    base = _expected_ceiling(cert)
    if base == "LIMITED":
        return "LIMITED"
    if cert.get("unknown_channels"):
        return "LIMITED"
    for reason in cert.get("degradation_reasons", []):
        if reason in REFLECTION_DEGRADATION_REASONS:
            return "LIMITED"
    return base


def _sensitivity_warning(sensitivity: dict) -> str:
    parts = []
    for name, block in (("order", sensitivity["order"]),
                        ("semantic", sensitivity["semantic"])):
        status = block["status"]
        if status == "CONFIRMED_SENSITIVE":
            parts.append(f"{name} sensitivity CONFIRMED (minimum possible convention "
                         "separation exceeds the post hoc frozen internal threshold)")
        elif status == "INDETERMINATE":
            parts.append(f"{name} sensitivity INDETERMINATE under interval overlap; "
                         "absence of a flag is not evidence of convention agreement")
        elif status == "NOT_EVALUABLE":
            parts.append(f"{name} sensitivity NOT EVALUABLE (unidentifiable shares or "
                         "unknown inputs); no agreement claim is made")
        elif status == "NO_CONFIRMED_SENSITIVITY":
            parts.append(f"no confirmed {name} sensitivity detected (worst-case spread "
                         "within threshold); this is not a general agreement claim")
    return "; ".join(parts)


def make_r20_audit_certificate(*, layer: str, channel_profile: dict, attribution: dict,
                               viability_state: float, defense_readiness: float,
                               surgery_history, lambda_value, lambda_status: str,
                               source_registration: str, mechanism_evidence: str,
                               goal_mode: str, lambda_time_origin: str,
                               lambda_counterfactual_scope: str,
                               model_hash=None, evidence_hash=None,
                               weights=None, sigma: float = 1.0) -> dict:
    """Produce an R20 certificate; mode is inferred from the channel states.

    POINT mode (all channels DEFINED) is reserved for exact/registered
    white-box reads and exports the registered primary-convention scalar with
    oracle-labeled detection.  INTERVAL mode propagates the declared real
    intervals, recomputes per-convention detection statuses and the
    three-state sensitivity system, and exports no scalar.  All statuses,
    intervals, flags, grades, and the overall range are recomputed here from
    estimable inputs; callers cannot suppress or forge them.
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
    mode = "POINT" if states <= {"DEFINED"} else "INTERVAL"
    profile = json.loads(json.dumps(channel_profile))
    _validate_channel_profile_r20(profile, layer=layer, goal_mode=goal_mode,
                                  lambda_status=lambda_status, mode=mode)
    attribution = json.loads(json.dumps(attribution))
    if weights is not None:
        attribution["weights"] = [float(w) for w in weights]
    attribution.setdefault("sigma", float(sigma))
    computed = _validate_attribution_r20(attribution, layer=layer, mode=mode,
                                         channel_profile=profile, applicable=applicable,
                                         viability=viability_state)
    convention_reports = computed["convention_reports"]
    sensitivity = computed["sensitivity"]
    overall = computed["overall"]
    flags, grade = computed["flags"], computed["grade"]
    attribution["convention_reports"] = convention_reports
    attribution["overall_composite_range"] = overall
    reasons, unknown = _degradation_inventory(profile)
    if mode == "POINT":
        if layer == "L0":
            primary = convention_reports["L0_INTERNAL_CAUSAL"]["composite_interval"]["bounds"][0]
        else:
            primary = convention_reports["registered"]["RNI"]["composite_interval"]["bounds"][0]
        state_autonomy = float(primary)
        state_autonomy_interval = None
        warning = ""
        if flags:
            warning = (
                "Registered attribution conventions are CONFIRMED sensitive beyond the "
                "post hoc frozen internal engineering threshold(s); the scalar composite "
                "is sensitivity-qualified and must be read together with channel_profile "
                "and the attribution block. A near-one RNI share with a near-zero NRI "
                "share is an ordering convention, not an order-free causal fraction. "
                + _sensitivity_warning(sensitivity))
    else:
        state_autonomy = None
        state_autonomy_interval = list(overall)
        warning = (
            "INTERVAL certificate: no point export. Composite intervals propagate the "
            "DECLARED input intervals by coordinatewise monotonicity (an envelope "
            "guarantee for those inputs, not automatically a full statistical "
            "uncertainty interval); each interval carries its kind. LOGICAL_ENVELOPE "
            "intervals (detection-limited reporting, degradation, unidentifiability) "
            "are NOT confidence intervals. Diagnostic plug-in outputs are stored "
            "separately and are not the reported semantics. "
            + _sensitivity_warning(sensitivity))
    cert = {
        "layer": layer,
        "construct_scope": ("internal_causal_only" if layer == "L0"
                            else "normative_structure_required"),
        "channel_schema_version": R20_CHANNEL_SCHEMA_VERSION,
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
        "sensitivity_status": sensitivity,
        "composite_scalar_grade": grade,
        "scalar_export_warning": warning,
        "threshold_provenance": THRESHOLD_PROVENANCE,
        "detection_policy": dict(DETECTION_POLICY),
        "degradation_reasons": reasons,
        "unknown_channels": unknown,
    }
    if layer == "L0":
        cert["attribution_report"] = attribution["attribution_report"]
        cert["attribution_sensitivity"] = {
            "weights": attribution["weights"], "sigma": attribution["sigma"],
            "convention_reports": convention_reports,
            "overall_composite_range": overall,
            "note": "L0 internal-causal only; no RNI/NRI/order conventions at L0.",
        }
    else:
        cert["attribution_sensitivity"] = attribution
    cert["evidence_ceiling"] = _r20_ceiling(cert)
    cert["current_structural_profile"] = {
        "scope": CURRENT_STRUCTURAL_SCOPE,
        "state_autonomy": state_autonomy,
        "state_autonomy_interval": state_autonomy_interval,
        "viability_state": viability_state,
        "defense_readiness": defense_readiness,
        "composite_scale": COMPOSITE_SCALE,
        "composite_range_across_conventions": overall,
        "sensitivity_flags": list(flags),
        "sensitivity_status": sensitivity,
        "composite_scalar_grade": grade,
        "full_channel_profile_field": "channel_profile",
    }
    cert["historical_formation_profile"] = _historical_profile(cert)
    errors = validate_r20_certificate(cert)
    if errors:
        raise ValueError("invalid R20 certificate: " + "; ".join(errors))
    return cert


def _validate_base_point(cert: dict) -> list[str]:
    base = dict(cert)
    for field in R20_EXTRA_FIELDS:
        base.pop(field, None)
    base.pop("attribution_report", None)
    base.pop("attribution_sensitivity", None)
    base["channel_schema_version"] = R17_CHANNEL_SCHEMA_VERSION
    current = dict(base.get("current_structural_profile", {}))
    for field in ("composite_range_across_conventions", "sensitivity_flags",
                  "sensitivity_status", "composite_scalar_grade",
                  "full_channel_profile_field", "state_autonomy_interval"):
        current.pop(field, None)
    base["current_structural_profile"] = current
    return validate_r17_certificate(base)


def _validate_base_interval(cert: dict) -> list[str]:
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
    for field in R20_EXTRA_FIELDS:
        base.pop(field, None)
    base.pop("attribution_report", None)
    base.pop("attribution_sensitivity", None)
    base["channel_schema_version"] = R17_CHANNEL_SCHEMA_VERSION
    base["state_autonomy"] = upper
    base["evidence_ceiling"] = _expected_ceiling(cert)
    current = dict(base.get("current_structural_profile", {}))
    for field in ("composite_range_across_conventions", "sensitivity_flags",
                  "sensitivity_status", "composite_scalar_grade",
                  "full_channel_profile_field", "state_autonomy_interval"):
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


def _reports_equal(a, b) -> bool:
    """Structural equality with float tolerance for recomputed reports."""
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        if set(a) != set(b):
            return False
        return all(_reports_equal(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)):
        if len(a) != len(b):
            return False
        return all(_reports_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, float):
        return math.isfinite(a) and math.isfinite(b) and abs(a - b) <= TOL
    return a == b


def validate_r20_certificate(cert: dict) -> list[str]:
    errors = []
    if not isinstance(cert, dict):
        return ["certificate must be an object"]
    for field in R20_EXTRA_FIELDS:
        if field not in cert:
            errors.append(f"missing R20 field {field}")
    if cert.get("channel_schema_version") != R20_CHANNEL_SCHEMA_VERSION:
        errors.append("channel_schema_version must be R20_CHANNEL_SCHEMA_V1")
    if errors:
        return errors
    mode = cert.get("certificate_mode")
    if mode not in {"POINT", "INTERVAL"}:
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
        applicable = _validate_channel_profile_r20(
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
        computed = _validate_attribution_r20(
            attribution, layer=layer, mode=mode, channel_profile=profile,
            applicable=applicable, viability=float(cert["viability_state"]))
    except ValueError as exc:
        return errors + [str(exc)]
    recorded_reports = attribution.get("convention_reports")
    if not _reports_equal(recorded_reports, computed["convention_reports"]):
        errors.append("convention_reports drift (statuses/intervals must be the "
                      "recomputed data-driven values)")
    if not _reports_equal(attribution.get("overall_composite_range"), computed["overall"]):
        errors.append("overall_composite_range must equal the hull of the reported "
                      "convention composite intervals")
    if not _reports_equal(cert.get("sensitivity_status"), computed["sensitivity"]):
        errors.append("sensitivity_status drift (three-state system is recomputed)")
    flags = cert.get("sensitivity_flags")
    if not isinstance(flags, list) or set(flags) - {"ORDER_SENSITIVE", "MODEL_SENSITIVE"}:
        errors.append("sensitivity_flags must be a list of registered flag values")
    elif sorted(flags) != sorted(computed["flags"]):
        errors.append("sensitivity_flags must match CONFIRMED_SENSITIVE statuses only "
                      "(required flags cannot be suppressed; indeterminate is not a flag)")
    if cert.get("composite_scalar_grade") != computed["grade"]:
        errors.append("composite_scalar_grade drift")
    warning = cert.get("scalar_export_warning")
    if not isinstance(warning, str):
        errors.append("scalar_export_warning must be a string")
    elif (mode == "INTERVAL" or computed["flags"]) and not warning.strip():
        errors.append("flagged or interval certificates must carry a scalar-export warning")
    if cert.get("threshold_provenance") != THRESHOLD_PROVENANCE:
        errors.append("threshold_provenance must declare the post hoc frozen status")
    if cert.get("detection_policy") != DETECTION_POLICY:
        errors.append("detection_policy must declare the data-driven rule, its "
                      "provenance, and that no deployable decision uses exact truth")
    reasons, unknown = _degradation_inventory(profile)
    if cert.get("degradation_reasons") != reasons:
        errors.append("degradation_reasons drift")
    if cert.get("unknown_channels") != unknown:
        errors.append("unknown_channels drift")
    if cert.get("evidence_ceiling") != _r20_ceiling(cert):
        errors.append("evidence_ceiling must respect unknown/degraded channels")
    if mode == "POINT":
        if cert.get("state_autonomy_interval") is not None:
            errors.append("POINT certificate must not carry state_autonomy_interval")
        if layer == "L0":
            primary = computed["convention_reports"]["L0_INTERNAL_CAUSAL"]["composite_interval"]["bounds"][0]
        else:
            primary = computed["convention_reports"]["registered"]["RNI"]["composite_interval"]["bounds"][0]
        if abs(float(cert["state_autonomy"]) - float(primary)) > TOL:
            errors.append("state_autonomy must equal the registered primary-convention composite")
    else:
        actual = cert.get("state_autonomy_interval")
        if (not isinstance(actual, (list, tuple))
                or any(abs(float(a) - float(b)) > TOL
                       for a, b in zip(actual, computed["overall"]))):
            errors.append("state_autonomy_interval must equal the overall composite hull")
    current = cert.get("current_structural_profile", {})
    if not _reports_equal(current.get("composite_range_across_conventions"),
                          computed["overall"]):
        errors.append("current profile composite range drift")
    if current.get("sensitivity_flags") != flags:
        errors.append("current profile sensitivity flags drift")
    if not _reports_equal(current.get("sensitivity_status"), computed["sensitivity"]):
        errors.append("current profile sensitivity status drift")
    if current.get("composite_scalar_grade") != computed["grade"]:
        errors.append("current profile scalar grade drift")
    if current.get("full_channel_profile_field") != "channel_profile":
        errors.append("current profile must reference the full channel profile")
    if current.get("composite_scale") != COMPOSITE_SCALE:
        errors.append("current composite must remain marked protocol-normalized")
    return errors


def write_r20_certificate(path: str, cert: dict) -> None:
    errors = validate_r20_certificate(cert)
    if errors:
        raise ValueError("invalid R20 certificate: " + "; ".join(errors))
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(cert, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def produce_r20_certificate(*, channel_profile: dict, attribution: dict,
                            lambda_time_origin: str, lambda_counterfactual_scope: str,
                            **kwargs) -> dict:
    return make_r20_audit_certificate(
        channel_profile=channel_profile, attribution=attribution,
        lambda_time_origin=lambda_time_origin,
        lambda_counterfactual_scope=lambda_counterfactual_scope, **kwargs)