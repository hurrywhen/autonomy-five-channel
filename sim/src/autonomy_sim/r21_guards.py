"""R21 conditioning-honest audit certificate schema.

R20 remains a compatibility layer (read-only replay of R20 artifacts).  R21
closes the two gaps identified in the R20 review, WITHOUT changing the
detection rule, the three-state sensitivity system, or the historical archive:

1. **Conditioning scope of composite sampling intervals is disclosed.**  The
   above-detection-limit composite sampling interval propagates ONLY the
   source-share basic bootstrap interval; the execution, epistemic, and
   reflection channels are held at their declared plug-in (or structural)
   point estimates.  It is therefore a SHARE-CONDITIONAL composite sampling
   interval, not a full joint-uncertainty interval.  R21 renames its kind to
   ``SHARE_CONDITIONAL_SAMPLING_BASIC_BOOTSTRAP`` and adds a
   ``conditioning_scope`` field to every interval-mode composite interval, plus
   a certificate-level ``composite_interval_conditioning`` policy.  The
   ``share_interval`` itself keeps ``SAMPLING_BASIC_BOOTSTRAP`` (it is the
   share's own unconditional bootstrap interval).  A joint trajectory
   bootstrap that recomputes ALL channels is provided as an ARTIFACT-LEVEL
   supplementary diagnostic (r21_joint_audit / analysis_r21_detection_study);
   it is NOT the certificate's reported semantics.
2. **Logical-envelope anchor containment is separated from sampling coverage.**
   Logical envelopes are explicitly not confidence intervals; whether an
   envelope contains the model anchor is ``logical_envelope_anchor_containment``
   (a containment diagnostic), never a statistical coverage rate, and is never
   compared against or combined with sampling-interval coverage.  The
   separation is enforced in the detection study; the certificate already
   marks envelopes LOGICAL_ENVELOPE.

Under-coverage of above-limit sampling intervals has TWO disclosed causes:
(i) finite-sample plug-in bias of the directed-information share estimates,
and (ii) the share-conditional design itself (other channels fixed at points,
so their estimation error and inter-channel covariance are not propagated).
R21 states both; the joint-bootstrap diagnostic quantifies their relative
contribution on the registered grid.

Thresholds, the detection limit value, and the detection rule provenance are
unchanged from R20 (post hoc frozen internal constants; rule declared before
R20 study outcomes).  This module is internal audit machinery, not external
construct validation.
"""
from __future__ import annotations

import json
import math

from .formation_audit import validate_lambda_time_origin
from .r17_guards import (COMPOSITE_SCALE, CURRENT_STRUCTURAL_SCOPE,
                         R17_CHANNEL_SCHEMA_VERSION, validate_r17_certificate)
from . import r19_guards as _r19
from . import r20_guards as _r20
from .r19_guards import (LAYER_CHANNELS, ORDER_CONVENTIONS, SHARE_KEYS,
                         THRESHOLD_PROVENANCE, TOL,
                         _degradation_inventory, _expected_ceiling,
                         _historical_profile, _interval, _unit,
                         _validate_l0_report)
from .r20_detection import (DETECTION_LIMIT, DETECTION_RULE_PROVENANCE,
                            DETECTION_RULE_VERSION,
                            basic_bootstrap_bias_corrected_interval,
                            classify_share_interval,
                            oracle_assisted_fixture_classification)

R21_CHANNEL_SCHEMA_VERSION = "R21_CHANNEL_SCHEMA_V1"

# R21 adds the share-conditional composite sampling kind.  The share's own
# bootstrap interval keeps SAMPLING_BASIC_BOOTSTRAP (unconditional).
INTERVAL_KINDS = frozenset({
    "POINT_EXACT", "LOGICAL_ENVELOPE", "SAMPLING_BASIC_BOOTSTRAP",
    "SAMPLING_PERCENTILE", "SAMPLING_NORMAL_APPROX", "SENSITIVITY",
    "MODEL_SELECTION", "SHARE_CONDITIONAL_SAMPLING_BASIC_BOOTSTRAP"})
SHARE_CONDITIONAL_KIND = "SHARE_CONDITIONAL_SAMPLING_BASIC_BOOTSTRAP"

CONDITIONING_SCOPES = frozenset({
    "other_channels_fixed_at_plugin", "other_channels_at_declared_bounds"})

COMPOSITE_INTERVAL_CONDITIONING = {
    "design": "SHARE_CONDITIONAL",
    "propagated_uncertainty": "source_share_basic_bootstrap_interval_only",
    "other_channels": "fixed_at_declared_plugin_or_structural_points",
    "not_a_full_joint_uncertainty_interval": True,
    "undercoverage_causes": ["directed_information_plugin_bias",
                             "share_conditional_design_other_channels_fixed"],
    "joint_bootstrap_diagnostic":
        "ARTIFACT_LEVEL_SUPPLEMENTARY_NOT_CERTIFICATE_REPORTED_SEMANTICS",
    "scope_field": "conditioning_scope",
}

SENSITIVITY_STATUSES = _r20.SENSITIVITY_STATUSES
CONVENTION_STATUSES = _r20.CONVENTION_STATUSES
GRADE_POINT = _r20.GRADE_POINT
GRADE_SENSITIVE = _r20.GRADE_SENSITIVE
GRADE_L0 = _r20.GRADE_L0
GRADE_INTERVAL = _r20.GRADE_INTERVAL
GRADE_INTERVAL_SENSITIVE = _r20.GRADE_INTERVAL_SENSITIVE
GRADE_INTERVAL_INDETERMINATE = _r20.GRADE_INTERVAL_INDETERMINATE
GRADE_ZERO_FLOW = _r20.GRADE_ZERO_FLOW

R21_EXTRA_FIELDS = _r20.R20_EXTRA_FIELDS + ("composite_interval_conditioning",)

DETECTION_POLICY = dict(_r20.DETECTION_POLICY)


def _conditioning_scope(channel_profile: dict, applicable: tuple[str, ...]) -> str:
    non_org = [name for name in applicable if name != "a_org"]
    if all(channel_profile[name]["state"] == "DEFINED" for name in non_org):
        return "other_channels_fixed_at_plugin"
    return "other_channels_at_declared_bounds"


def _composite_interval(bounds, kind: str, scope: str) -> dict:
    return {"bounds": list(bounds), "kind": kind, "conditioning_scope": scope}


def _compute_convention_reports_r21(*, attribution: dict, channel_profile: dict,
                                    applicable: tuple[str, ...], layer: str,
                                    mode: str, viability: float) -> dict:
    """Recompute per-convention reports; R21 adds conditioning disclosure.

    Identical detection decisions to R20 (same estimable inputs, same rule);
    the composite interval KIND and conditioning_scope are the R21 change.
    """
    weights = attribution["weights"]
    sigma = float(attribution.get("sigma", 1.0))
    other_bounds = {name: _r20._channel_bounds(channel_profile[name])
                    for name in applicable if name != "a_org"}
    others_defined = all(channel_profile[name]["state"] == "DEFINED"
                         for name in applicable if name != "a_org")
    scope = _conditioning_scope(channel_profile, applicable)

    def box(share_bounds):
        return [share_bounds if name == "a_org" else other_bounds[name]
                for name in applicable]

    def comp(share_bounds):
        return _r20._composite_bounds(viability, box(share_bounds), weights, sigma)

    if layer == "L0":
        report = attribution["attribution_report"]
        share = report.get("internal_causal_share")
        share_bounds = (0.0, 1.0) if share is None else (float(share), float(share))
        interval = comp(share_bounds)
        if share is None:
            kind = "LOGICAL_ENVELOPE"
        elif mode == "POINT":
            kind = "POINT_EXACT"
        else:
            kind = SHARE_CONDITIONAL_KIND
        composite = ({"bounds": interval, "kind": kind} if mode == "POINT"
                     else _composite_interval(interval, kind, scope))
        return {"L0_INTERNAL_CAUSAL": {
            "convention_status": ("NOT_EVALUABLE" if share is None else
                                  ("POINT_EXACT" if mode == "POINT" else "DATA_ABOVE_LIMIT")),
            "share_interval": (None if share is None else
                               {"bounds": [float(share), float(share)] if mode == "POINT"
                                else list(channel_profile["a_org"]["interval"]),
                                "kind": "POINT_EXACT" if mode == "POINT"
                                else channel_profile["a_org"]["interval_kind"]}),
            "composite_interval": composite,
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
        zero_flow = _r20._partition_zero_flow(report)
        for convention, key in zip(ORDER_CONVENTIONS, SHARE_KEYS):
            share = report[key]
            base = {"detection_limit": DETECTION_LIMIT,
                    "detection_rule_version": DETECTION_RULE_VERSION,
                    "detection_provenance": DETECTION_RULE_PROVENANCE}
            if zero_flow:
                reports[partition_name][convention] = dict(
                    base, convention_status="NOT_EVALUABLE",
                    share_interval=None, share_bootstrap_percentile_95=None,
                    composite_interval=_composite_interval(
                        comp((0.0, 1.0)), "LOGICAL_ENVELOPE", scope),
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
                reported = _composite_interval(sampling_bounds, SHARE_CONDITIONAL_KIND, scope)
            else:
                reported = _composite_interval(comp((0.0, decision[1])),
                                               "LOGICAL_ENVELOPE", scope)
            plugin_composite = (comp((share, share))[0] if others_defined else None)
            reports[partition_name][convention] = dict(
                base, convention_status=status,
                share_interval={"bounds": decision, "kind": "SAMPLING_BASIC_BOOTSTRAP"},
                share_bootstrap_percentile_95=[float(perc[0]), float(perc[1])],
                composite_interval=reported,
                composite_interval_sampling=_composite_interval(
                    sampling_bounds, SHARE_CONDITIONAL_KIND, scope),
                diagnostic_plugin_share=share,
                diagnostic_plugin_composite=plugin_composite)
    return reports


def _validate_attribution_r21(attribution: dict, *, layer: str, mode: str,
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
        _r20._validate_partition_report_r20(attribution["registered_partition"],
                                            "registered_partition", mode=mode)
        alternatives = attribution.get("alternative_partitions", {})
        if not isinstance(alternatives, dict):
            raise ValueError("alternative_partitions must be an object")
        for name, report in alternatives.items():
            _r20._validate_partition_report_r20(report, f"alternative_partitions.{name}",
                                                mode=mode)
    convention_reports = _compute_convention_reports_r21(
        attribution=attribution, channel_profile=channel_profile,
        applicable=applicable, layer=layer, mode=mode, viability=viability)
    sensitivity = _r20._compute_sensitivity_status(
        convention_reports, layer=layer, attribution=attribution,
        channel_profile=channel_profile, applicable=applicable)
    overall = _r20._overall_range(convention_reports, layer=layer)
    zero_flow = _r20._zero_total_flow(attribution, layer)
    flags, grade = _r20._flags_and_grade(sensitivity, layer=layer, mode=mode,
                                         zero_flow=zero_flow)
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
            if _r20._partition_zero_flow(registered):
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


def _validate_base_point_r21(cert: dict) -> list[str]:
    base = dict(cert)
    for field in R21_EXTRA_FIELDS:
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


def _validate_base_interval_r21(cert: dict) -> list[str]:
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
    for field in R21_EXTRA_FIELDS:
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


def _check_conditioning_fields(cert: dict, mode: str, layer: str) -> list[str]:
    """R21: every interval-mode composite interval must disclose its scope."""
    errors = []
    if cert.get("composite_interval_conditioning") != COMPOSITE_INTERVAL_CONDITIONING:
        errors.append("composite_interval_conditioning must declare the share-conditional "
                      "design, its two under-coverage causes, and that the joint bootstrap "
                      "is an artifact-level supplementary diagnostic")
    if mode != "INTERVAL":
        return errors
    attribution = cert.get("attribution_sensitivity", {})
    reports = attribution.get("convention_reports", {})
    if layer == "L0":
        blocks = [reports.get("L0_INTERNAL_CAUSAL", {})]
    else:
        blocks = [rep for partition in reports.values() for rep in partition.values()]
    for rep in blocks:
        for field in ("composite_interval", "composite_interval_sampling"):
            obj = rep.get(field)
            if obj is None:
                continue
            kind = obj.get("kind")
            if kind not in INTERVAL_KINDS:
                errors.append(f"{field}.kind must be a registered R21 kind")
            scope = obj.get("conditioning_scope")
            if scope not in CONDITIONING_SCOPES:
                errors.append(f"{field}.conditioning_scope must be a registered scope "
                              "(other channels fixed at plugin / declared bounds)")
            if kind == SHARE_CONDITIONAL_KIND and scope is None:
                errors.append("share-conditional composite interval requires conditioning_scope")
    return errors


def make_r21_audit_certificate(*, layer: str, channel_profile: dict, attribution: dict,
                               viability_state: float, defense_readiness: float,
                               surgery_history, lambda_value, lambda_status: str,
                               source_registration: str, mechanism_evidence: str,
                               goal_mode: str, lambda_time_origin: str,
                               lambda_counterfactual_scope: str,
                               model_hash=None, evidence_hash=None,
                               weights=None, sigma: float = 1.0) -> dict:
    """Produce an R21 certificate (conditioning-honest; R20 decisions unchanged)."""
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
    # Channel entries carry share/sampling/envelope kinds (not the composite
    # share-conditional kind), so the R20 channel validation applies unchanged.
    _r20._validate_channel_profile_r20(profile, layer=layer, goal_mode=goal_mode,
                                       lambda_status=lambda_status, mode=mode)
    attribution = json.loads(json.dumps(attribution))
    if weights is not None:
        attribution["weights"] = [float(w) for w in weights]
    attribution.setdefault("sigma", float(sigma))
    computed = _validate_attribution_r21(attribution, layer=layer, mode=mode,
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
                + _r20._sensitivity_warning(sensitivity))
    else:
        state_autonomy = None
        state_autonomy_interval = list(overall)
        warning = (
            "INTERVAL certificate: no point export. Above-limit composite intervals are "
            "SHARE-CONDITIONAL sampling intervals: they propagate ONLY the source-share "
            "basic bootstrap interval with the other channels fixed at their declared "
            "plugin/structural points (conditioning_scope), NOT a full joint-uncertainty "
            "interval; their under-coverage reflects both directed-information plug-in "
            "bias and this share-conditional design. A joint trajectory bootstrap is an "
            "artifact-level supplementary diagnostic, not the reported semantics. "
            "LOGICAL_ENVELOPE intervals (detection-limited reporting, degradation, "
            "unidentifiability) are NOT confidence intervals; anchor containment is not "
            "statistical coverage. Diagnostic plug-in outputs are stored separately and "
            "are not the reported semantics. "
            + _r20._sensitivity_warning(sensitivity))
    cert = {
        "layer": layer,
        "construct_scope": ("internal_causal_only" if layer == "L0"
                            else "normative_structure_required"),
        "channel_schema_version": R21_CHANNEL_SCHEMA_VERSION,
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
        "composite_interval_conditioning": dict(COMPOSITE_INTERVAL_CONDITIONING),
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
    cert["evidence_ceiling"] = _r20._r20_ceiling(cert)
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
    errors = validate_r21_certificate(cert)
    if errors:
        raise ValueError("invalid R21 certificate: " + "; ".join(errors))
    return cert


def validate_r21_certificate(cert: dict) -> list[str]:
    errors = []
    if not isinstance(cert, dict):
        return ["certificate must be an object"]
    for field in R21_EXTRA_FIELDS:
        if field not in cert:
            errors.append(f"missing R21 field {field}")
    if cert.get("channel_schema_version") != R21_CHANNEL_SCHEMA_VERSION:
        errors.append("channel_schema_version must be R21_CHANNEL_SCHEMA_V1")
    if errors:
        return errors
    mode = cert.get("certificate_mode")
    if mode not in {"POINT", "INTERVAL"}:
        return errors + ["certificate_mode must be POINT or INTERVAL"]
    layer = cert.get("layer")
    if layer not in LAYER_CHANNELS:
        return errors + ["invalid layer"]
    if mode == "POINT":
        errors.extend(_validate_base_point_r21(cert))
    else:
        errors.extend(_validate_base_interval_r21(cert))
    if errors:
        return errors
    try:
        applicable = _r20._validate_channel_profile_r20(
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
        computed = _validate_attribution_r21(
            attribution, layer=layer, mode=mode, channel_profile=profile,
            applicable=applicable, viability=float(cert["viability_state"]))
    except ValueError as exc:
        return errors + [str(exc)]
    recorded_reports = attribution.get("convention_reports")
    if not _r20._reports_equal(recorded_reports, computed["convention_reports"]):
        errors.append("convention_reports drift (statuses/intervals/conditioning must be "
                      "the recomputed data-driven values)")
    if not _r20._reports_equal(attribution.get("overall_composite_range"), computed["overall"]):
        errors.append("overall_composite_range must equal the hull of the reported "
                      "convention composite intervals")
    if not _r20._reports_equal(cert.get("sensitivity_status"), computed["sensitivity"]):
        errors.append("sensitivity_status drift (three-state system is recomputed)")
    flags = cert.get("sensitivity_flags")
    if not isinstance(flags, list) or set(flags) - {"ORDER_SENSITIVE", "MODEL_SENSITIVE"}:
        errors.append("sensitivity_flags must be a list of registered flag values")
    elif sorted(flags) != sorted(computed["flags"]):
        errors.append("sensitivity_flags must match CONFIRMED_SENSITIVE statuses only")
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
        errors.append("detection_policy must declare the data-driven rule and provenance")
    errors.extend(_check_conditioning_fields(cert, mode, layer))
    reasons, unknown = _degradation_inventory(profile)
    if cert.get("degradation_reasons") != reasons:
        errors.append("degradation_reasons drift")
    if cert.get("unknown_channels") != unknown:
        errors.append("unknown_channels drift")
    if cert.get("evidence_ceiling") != _r20._r20_ceiling(cert):
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
    if not _r20._reports_equal(current.get("composite_range_across_conventions"),
                               computed["overall"]):
        errors.append("current profile composite range drift")
    if current.get("sensitivity_flags") != flags:
        errors.append("current profile sensitivity flags drift")
    if not _r20._reports_equal(current.get("sensitivity_status"), computed["sensitivity"]):
        errors.append("current profile sensitivity status drift")
    if current.get("composite_scalar_grade") != computed["grade"]:
        errors.append("current profile scalar grade drift")
    if current.get("full_channel_profile_field") != "channel_profile":
        errors.append("current profile must reference the full channel profile")
    if current.get("composite_scale") != COMPOSITE_SCALE:
        errors.append("current composite must remain marked protocol-normalized")
    return errors


def write_r21_certificate(path: str, cert: dict) -> None:
    errors = validate_r21_certificate(cert)
    if errors:
        raise ValueError("invalid R21 certificate: " + "; ".join(errors))
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(cert, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def produce_r21_certificate(*, channel_profile: dict, attribution: dict,
                            lambda_time_origin: str, lambda_counterfactual_scope: str,
                            **kwargs) -> dict:
    return make_r21_audit_certificate(
        channel_profile=channel_profile, attribution=attribution,
        lambda_time_origin=lambda_time_origin,
        lambda_counterfactual_scope=lambda_counterfactual_scope, **kwargs)