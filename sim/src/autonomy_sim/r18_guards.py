"""R18 full-profile audit certificate schema.

R17 remains a compatibility layer.  R18 makes the framework's own audit
principle --- profile first, scalar second, sensitivity visible ---
machine-checkable in the final certificate:

* the full layer-applicable channel vector, each component carrying its
  value, state, optional interval, and protocol version;
* the registered attribution-order report (RNI, NRI, two-order average, and
  every flow term) plus every preregistered alternative semantic partition;
* goal structural point and IRL interval, execution open-loop horizon,
  reflection three factors and logged event counts;
* the aggregation weights and the composite range across all registered
  conventions, not a single RNI point;
* enforced ``ORDER_SENSITIVE`` / ``MODEL_SENSITIVE`` flags whenever the
  composite spread across registered conventions exceeds the preregistered
  internal thresholds, with a mandatory scalar-export warning and a
  sensitivity-qualified scalar grade.

The thresholds below are preregistered *internal engineering* thresholds on
this framework's protocol-normalized composite scale.  They are not a domain
SESOI, not a power calculation, and not external construct validation.  A
certificate that presents a single positive scalar while registered
conventions materially disagree fails closed.
"""
from __future__ import annotations

import json
import math

from .aggregate import composite_A
from .r15_guards import R16_CHANNEL_SCHEMA_VERSION, produce_r15_certificate
from .r17_guards import (COMPOSITE_SCALE, R17_CHANNEL_SCHEMA_VERSION,
                         make_r17_audit_certificate, validate_r17_certificate)

R18_CHANNEL_SCHEMA_VERSION = "R18_CHANNEL_SCHEMA_V1"

# Preregistered internal sensitivity thresholds (composite-scale spread).
ORDER_SENSITIVITY_THRESHOLD = 0.05
MODEL_SENSITIVITY_THRESHOLD = 0.05

CHANNEL_ORDER_L2 = ("a_org", "a_goal", "a_exec", "a_epi", "a_ref")
LAYER_CHANNELS = {
    "L0": ("a_org", "a_exec"),
    "L1": ("a_org", "a_goal", "a_exec", "a_epi"),
    "L2": CHANNEL_ORDER_L2,
}
ORDER_CONVENTIONS = ("RNI", "NRI", "order_average")
SENSITIVITY_FLAG_VALUES = frozenset({"ORDER_SENSITIVE", "MODEL_SENSITIVE"})
GRADE_SENSITIVE = "SENSITIVITY_QUALIFIED_NOT_A_ROBUST_POINT_READING"
GRADE_POINT = "POINT_READING_UNDER_REGISTERED_CONVENTION_ONLY"
GRADE_UNDEFINED = "UNDEFINED_ZERO_TOTAL_FLOW"
CHANNEL_STATES = frozenset({"DEFINED"})
SHARE_KEYS = ("normative_share_RNI", "normative_share_NRI",
              "normative_share_order_average")
FLOW_KEYS = ("flows_bits_RNI", "flows_bits_NRI", "joint_di_bits")
TOL = 1e-9

R18_EXTRA_FIELDS = (
    "channel_profile", "attribution_sensitivity", "sensitivity_flags",
    "composite_scalar_grade", "scalar_export_warning",
)


def _unit(value, label: str) -> float:
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{label} must be finite and in [0,1], got {value!r}")
    return value


def _optional_interval(interval, label: str):
    if interval is None:
        return None
    if not isinstance(interval, (list, tuple)) or len(interval) != 2:
        raise ValueError(f"{label} interval must be None or [lower, upper]")
    lower = _unit(interval[0], f"{label} interval lower")
    upper = _unit(interval[1], f"{label} interval upper")
    if lower > upper:
        raise ValueError(f"{label} interval must be ordered lower <= upper")
    return [lower, upper]


def _nonnegative_int(value, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer")
    return value


def _validate_partition_report(report, label: str) -> dict:
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
    # Chain additivity: each order's flows sum to the joint directed information.
    for flows, name in ((flows_rni, "RNI"), (flows_nri, "NRI")):
        if abs(math.fsum(float(v) for v in flows) - total) > 1e-6:
            raise ValueError(f"{label} {name} flows do not sum to joint_di_bits")
    shares = {}
    for key in SHARE_KEYS:
        if key not in report:
            raise ValueError(f"{label} missing {key}")
        value = report[key]
        if value is None:
            if total > TOL:
                raise ValueError(f"{label}.{key} is None but total flow is positive")
            shares[key] = None
        else:
            shares[key] = _unit(value, f"{label}.{key}")
    if total > TOL:
        expected_rni = float(flows_rni[1]) / total
        expected_nri = float(flows_nri[0]) / total
        if abs(shares["normative_share_RNI"] - expected_rni) > 1e-6:
            raise ValueError(f"{label} RNI share disagrees with its flow term")
        if abs(shares["normative_share_NRI"] - expected_nri) > 1e-6:
            raise ValueError(f"{label} NRI share disagrees with its flow term")
        if abs(shares["normative_share_order_average"]
               - 0.5 * (expected_rni + expected_nri)) > 1e-6:
            raise ValueError(f"{label} order average must be the two-order mean")
    return report


def _validate_channel_entry(entry, name: str) -> None:
    if not isinstance(entry, dict):
        raise ValueError(f"channel_profile.{name} must be an object")
    if entry.get("state") not in CHANNEL_STATES:
        raise ValueError(f"channel_profile.{name}.state must be DEFINED for a scalar certificate")
    _unit(entry.get("value"), f"channel_profile.{name}.value")
    protocol = entry.get("protocol_version")
    if not isinstance(protocol, str) or not protocol:
        raise ValueError(f"channel_profile.{name}.protocol_version is required")
    _optional_interval(entry.get("interval"), f"channel_profile.{name}")


def _validate_channel_profile(profile: dict, layer: str) -> tuple[str, ...]:
    if not isinstance(profile, dict):
        raise ValueError("channel_profile must be an object")
    applicable = LAYER_CHANNELS[layer]
    if set(profile) != set(applicable):
        raise ValueError(f"channel_profile must contain exactly the {layer} channels {applicable}")
    for name in applicable:
        _validate_channel_entry(profile[name], name)
    if "a_exec" in profile:
        exec_entry = profile["a_exec"]
        horizon = exec_entry.get("horizon_actions")
        if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon < 1:
            raise ValueError("a_exec.horizon_actions must be a positive integer")
        if exec_entry.get("uses_intermediate_observations") is not False:
            raise ValueError("a_exec must be a precommitted open-loop audit object")
    if "a_goal" in profile:
        goal_entry = profile["a_goal"]
        _unit(goal_entry.get("structural_point"), "a_goal.structural_point")
        _optional_interval(goal_entry.get("irl_interval"), "a_goal.irl")
        if goal_entry.get("irl_interval") is None:
            raise ValueError("a_goal must report the registered IRL interval (or an explicit flagged fallback)")
    if "a_ref" in profile:
        ref_entry = profile["a_ref"]
        fidelity = _unit(ref_entry.get("fidelity"), "a_ref.fidelity")
        consistency = _unit(ref_entry.get("endorsement_consistency"),
                            "a_ref.endorsement_consistency")
        lambda_value = _unit(ref_entry.get("Lambda"), "a_ref.Lambda")
        if abs(fidelity * consistency * lambda_value - float(ref_entry["value"])) > TOL:
            raise ValueError("a_ref.value must equal fidelity * consistency * Lambda")
        counts = ref_entry.get("event_counts")
        if not isinstance(counts, dict):
            raise ValueError("a_ref.event_counts is required (logged carriers, not asserted constants)")
        updates = _nonnegative_int(counts.get("normative_update_events"),
                                   "normative_update_events")
        endorsements = _nonnegative_int(counts.get("endorsement_events"),
                                        "endorsement_events")
        contexts = _nonnegative_int(counts.get("surgery_contexts"), "surgery_contexts")
        if updates < 1 or contexts < 1:
            raise ValueError("R18 reflection audit requires logged normative-update and surgery-context events")
        if endorsements > updates:
            raise ValueError("endorsement_events cannot exceed normative_update_events")
        if abs(consistency - endorsements / updates) > TOL:
            raise ValueError("endorsement_consistency must equal the logged event ratio")
    return applicable


def _compute_convention_composites(*, channel_profile: dict, applicable: tuple[str, ...],
                                   sensitivity: dict, viability: float) -> dict:
    """Recompute every registered-convention composite from declared inputs."""
    weights = sensitivity["weights"]
    sigma = float(sensitivity.get("sigma", 1.0))
    partitions = {"registered": sensitivity["registered_partition"]}
    partitions.update(sensitivity.get("alternative_partitions", {}))
    composites = {}
    for partition_name, report in partitions.items():
        composites[partition_name] = {}
        for convention, share_key in zip(ORDER_CONVENTIONS, SHARE_KEYS):
            share = report[share_key]
            if share is None:
                composites[partition_name][convention] = None
                continue
            values = []
            for name in applicable:
                if name == "a_org":
                    values.append(float(share))
                else:
                    values.append(float(channel_profile[name]["value"]))
            composites[partition_name][convention] = float(
                composite_A(viability, values, weights, sigma=sigma))
    return composites


def _sensitivity_summary(composites: dict) -> dict:
    numeric = [value for partition in composites.values()
               for value in partition.values() if value is not None]
    registered = [composites["registered"][convention] for convention in ORDER_CONVENTIONS]
    if not numeric or any(value is None for value in registered):
        return {"composite_range": None, "order_spread": None, "model_spread": None,
                "flags": [], "grade": GRADE_UNDEFINED}
    order_spread = max(registered) - min(registered)
    model_spread = max(numeric) - min(numeric)
    flags = []
    if order_spread > ORDER_SENSITIVITY_THRESHOLD:
        flags.append("ORDER_SENSITIVE")
    if model_spread > MODEL_SENSITIVITY_THRESHOLD:
        flags.append("MODEL_SENSITIVE")
    return {
        "composite_range": [min(numeric), max(numeric)],
        "order_spread": float(order_spread),
        "model_spread": float(model_spread),
        "flags": flags,
        "grade": GRADE_SENSITIVE if flags else GRADE_POINT,
    }


def _validate_attribution_sensitivity(sensitivity: dict, *, channel_profile: dict,
                                      applicable: tuple[str, ...], viability: float,
                                      state_autonomy: float) -> dict:
    if not isinstance(sensitivity, dict):
        raise ValueError("attribution_sensitivity must be an object")
    if "registered_partition" not in sensitivity:
        raise ValueError("attribution_sensitivity requires registered_partition")
    _validate_partition_report(sensitivity["registered_partition"], "registered_partition")
    alternatives = sensitivity.get("alternative_partitions", {})
    if not isinstance(alternatives, dict):
        raise ValueError("alternative_partitions must be an object")
    for name, report in alternatives.items():
        _validate_partition_report(report, f"alternative_partitions.{name}")
    weights = sensitivity.get("weights")
    if not isinstance(weights, (list, tuple)) or len(weights) != len(applicable):
        raise ValueError("attribution_sensitivity.weights must match the applicable channel count")
    weights = tuple(float(w) for w in weights)
    if any(not math.isfinite(w) or w <= 0.0 for w in weights):
        raise ValueError("certificate weights must be strictly positive (interior simplex)")
    if abs(math.fsum(weights) - 1.0) > 1e-9:
        raise ValueError("certificate weights must sum to one")
    sigma = float(sensitivity.get("sigma", 1.0))
    if not math.isfinite(sigma) or sigma <= 0.0:
        raise ValueError("sigma must be positive")
    composites = _compute_convention_composites(
        channel_profile=channel_profile, applicable=applicable,
        sensitivity=sensitivity, viability=viability)
    summary = _sensitivity_summary(composites)
    recorded = sensitivity.get("composite_by_convention")
    if recorded != composites:
        # Compare numerically with tolerance instead of exact dict equality.
        if not isinstance(recorded, dict) or set(recorded) != set(composites):
            raise ValueError("composite_by_convention drift")
        for partition_name, partition in composites.items():
            for convention, value in partition.items():
                other = recorded[partition_name].get(convention)
                if (value is None) != (other is None):
                    raise ValueError("composite_by_convention drift")
                if value is not None and abs(float(other) - value) > TOL:
                    raise ValueError("composite_by_convention drift")
    for key in ("composite_range", "order_spread", "model_spread"):
        expected = summary[key]
        actual = sensitivity.get(key)
        if (expected is None) != (actual is None):
            raise ValueError(f"attribution_sensitivity.{key} drift")
        if expected is not None:
            if key == "composite_range":
                if (not isinstance(actual, (list, tuple)) or len(actual) != 2
                        or any(abs(float(a) - float(b)) > TOL
                               for a, b in zip(actual, expected))):
                    raise ValueError("composite_range drift")
            elif abs(float(actual) - expected) > TOL:
                raise ValueError(f"attribution_sensitivity.{key} drift")
    # The exported scalar must be the registered primary (RNI) convention.
    primary = composites["registered"]["RNI"]
    if primary is None:
        if state_autonomy != 0.0:
            raise ValueError("undefined primary composite cannot export a positive scalar")
    elif abs(primary - state_autonomy) > TOL:
        raise ValueError("state_autonomy must equal the registered RNI-convention composite")
    return summary


def make_r18_audit_certificate(*, r17_certificate: dict, channel_profile: dict,
                               attribution_sensitivity: dict) -> dict:
    """Upgrade a valid R17 certificate to the R18 full-profile schema.

    Composite values across conventions, the composite range, sensitivity
    flags, the scalar grade, and the export warning are *computed here* from
    the declared shares, channels, weights, and viability; callers cannot
    suppress a required flag by omitting it.
    """
    errors = validate_r17_certificate(r17_certificate)
    if errors:
        raise ValueError("invalid R17 base certificate: " + "; ".join(errors))
    if r17_certificate.get("channel_schema_version") != R17_CHANNEL_SCHEMA_VERSION:
        raise ValueError("R18 upgrade requires an R17 base certificate")
    layer = r17_certificate["layer"]
    applicable = _validate_channel_profile(channel_profile, layer)
    profile = json.loads(json.dumps(channel_profile))  # detached copy
    for name in applicable:
        entry = profile[name]
        entry["value"] = _unit(entry["value"], f"{name}.value")
        entry["interval"] = _optional_interval(entry.get("interval"), name)
    sensitivity = json.loads(json.dumps(attribution_sensitivity))
    sensitivity["weights"] = [float(w) for w in sensitivity["weights"]]
    viability = float(r17_certificate["viability_state"])
    # Compute the convention bookkeeping first; the caller cannot suppress it.
    composites = _compute_convention_composites(
        channel_profile=profile, applicable=applicable, sensitivity=sensitivity,
        viability=viability)
    summary = _sensitivity_summary(composites)
    sensitivity["composite_by_convention"] = composites
    sensitivity["composite_range"] = summary["composite_range"]
    sensitivity["order_spread"] = summary["order_spread"]
    sensitivity["model_spread"] = summary["model_spread"]
    _validate_attribution_sensitivity(
        sensitivity, channel_profile=profile, applicable=applicable,
        viability=viability, state_autonomy=float(r17_certificate["state_autonomy"]))
    flags = summary["flags"]
    warning = ""
    if flags:
        warning = (
            "Registered attribution conventions disagree beyond the preregistered "
            "internal threshold(s); the scalar composite is sensitivity-qualified "
            "and must be read together with channel_profile and "
            "attribution_sensitivity. A near-one RNI share with a near-zero NRI "
            "share is an ordering convention, not an order-free causal fraction."
        )
    cert = dict(r17_certificate)
    cert["channel_schema_version"] = R18_CHANNEL_SCHEMA_VERSION
    cert["channel_profile"] = profile
    cert["attribution_sensitivity"] = sensitivity
    cert["sensitivity_flags"] = list(flags)
    cert["composite_scalar_grade"] = summary["grade"]
    cert["scalar_export_warning"] = warning
    current = dict(cert["current_structural_profile"])
    current["composite_range_across_conventions"] = summary["composite_range"]
    current["sensitivity_flags"] = list(flags)
    current["composite_scalar_grade"] = summary["grade"]
    current["full_channel_profile_field"] = "channel_profile"
    cert["current_structural_profile"] = current
    errors = validate_r18_certificate(cert)
    if errors:
        raise ValueError("invalid R18 certificate: " + "; ".join(errors))
    return cert


def validate_r18_certificate(cert: dict) -> list[str]:
    errors = []
    if not isinstance(cert, dict):
        return ["certificate must be an object"]
    for field in R18_EXTRA_FIELDS:
        if field not in cert:
            errors.append(f"missing R18 field {field}")
    if cert.get("channel_schema_version") != R18_CHANNEL_SCHEMA_VERSION:
        errors.append("channel_schema_version must be R18_CHANNEL_SCHEMA_V1")

    base = dict(cert)
    for field in R18_EXTRA_FIELDS:
        base.pop(field, None)
    base["channel_schema_version"] = R17_CHANNEL_SCHEMA_VERSION
    base_current = base.get("current_structural_profile")
    if isinstance(base_current, dict):
        base_current = dict(base_current)
        for field in ("composite_range_across_conventions", "sensitivity_flags",
                      "composite_scalar_grade", "full_channel_profile_field"):
            base_current.pop(field, None)
        base["current_structural_profile"] = base_current
    errors.extend(validate_r17_certificate(base))
    if errors:
        return errors

    layer = cert["layer"]
    try:
        applicable = _validate_channel_profile(cert["channel_profile"], layer)
    except ValueError as exc:
        return errors + [str(exc)]
    profile = cert["channel_profile"]
    if "a_ref" in profile and cert.get("lambda_status") == "DEFINED":
        if abs(float(profile["a_ref"]["Lambda"]) - float(cert["Lambda"])) > TOL:
            errors.append("a_ref.Lambda drift from certificate Lambda")
    try:
        summary = _validate_attribution_sensitivity(
            cert["attribution_sensitivity"], channel_profile=profile,
            applicable=applicable, viability=float(cert["viability_state"]),
            state_autonomy=float(cert["state_autonomy"]))
    except ValueError as exc:
        return errors + [str(exc)]

    flags = cert.get("sensitivity_flags")
    if not isinstance(flags, list) or set(flags) - SENSITIVITY_FLAG_VALUES:
        errors.append("sensitivity_flags must be a list of registered flag values")
    elif sorted(flags) != sorted(summary["flags"]):
        errors.append("sensitivity_flags must match the recomputed convention spreads "
                      "(required flags cannot be suppressed)")
    if cert.get("composite_scalar_grade") != summary["grade"]:
        errors.append("composite_scalar_grade drift")
    warning = cert.get("scalar_export_warning")
    if not isinstance(warning, str):
        errors.append("scalar_export_warning must be a string")
    elif summary["flags"] and not warning.strip():
        errors.append("a sensitivity-flagged certificate must carry a scalar-export warning")
    current = cert.get("current_structural_profile", {})
    if current.get("composite_range_across_conventions") != summary["composite_range"]:
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


def write_r18_certificate(path: str, cert: dict) -> None:
    errors = validate_r18_certificate(cert)
    if errors:
        raise ValueError("invalid R18 certificate: " + "; ".join(errors))
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(cert, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def produce_r18_certificate(*, channel_profile: dict, attribution_sensitivity: dict,
                            lambda_time_origin: str, lambda_counterfactual_scope: str,
                            formation_status_override: str | None = None,
                            **kwargs) -> dict:
    schema = kwargs.pop("channel_schema_version", None)
    if schema not in {None, R16_CHANNEL_SCHEMA_VERSION}:
        raise ValueError("produce_r18_certificate builds from the R16 base schema via R17")
    r16 = produce_r15_certificate(channel_schema_version=R16_CHANNEL_SCHEMA_VERSION, **kwargs)
    r17 = make_r17_audit_certificate(
        r16_certificate=r16,
        lambda_time_origin=lambda_time_origin,
        lambda_counterfactual_scope=lambda_counterfactual_scope,
        formation_status_override=formation_status_override)
    return make_r18_audit_certificate(
        r17_certificate=r17, channel_profile=channel_profile,
        attribution_sensitivity=attribution_sensitivity)