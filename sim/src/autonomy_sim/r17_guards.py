"""R17 co-primary current/history certificate schema.

The R16 certificate remains a compatibility layer.  R17 adds two top-level
co-primary profiles and explicit Lambda time-origin semantics; it does not
turn historical provenance into a scalar inferred from current channels.
"""
from __future__ import annotations

import json

from .formation_audit import (FORMATION_STATUSES, LAMBDA_TIME_ORIGIN_SCOPE,
                              formation_status, validate_lambda_time_origin)
from .logschema import validate_r15_certificate as validate_r16_certificate
from .r15_guards import (R16_CHANNEL_SCHEMA_VERSION, produce_r15_certificate)

R17_CHANNEL_SCHEMA_VERSION = "R17_CHANNEL_SCHEMA_V1"
CURRENT_STRUCTURAL_SCOPE = "PRESENT_STRUCTURAL_AUTONOMY"
HISTORICAL_FORMATION_SCOPE = "HISTORICAL_FORMATION_AUTONOMY"
COMPOSITE_SCALE = "PROTOCOL_NORMALIZED_NOT_RATIO_SCALE"

R17_EXTRA_FIELDS = (
    "current_structural_profile", "historical_formation_profile",
    "lambda_time_origin", "lambda_counterfactual_scope",
)


def _lambda_origin_for_status(lambda_status: str, origin: str, scope: str) -> list[str]:
    errors = []
    try:
        validate_lambda_time_origin(origin, scope)
    except ValueError as exc:
        errors.append(str(exc))
        return errors
    if lambda_status == "DEFINED":
        if origin not in {"AUDIT_CURRENT_REMOVAL", "ORIGINAL_IMPLANT_PREVENTION"}:
            errors.append("DEFINED Lambda requires an explicit counterfactual time origin")
    elif lambda_status == "NOT_APPLICABLE":
        if origin != "NOT_APPLICABLE":
            errors.append("NOT_APPLICABLE Lambda requires NOT_APPLICABLE time origin")
    elif lambda_status == "UNKNOWN":
        if origin != "UNKNOWN":
            errors.append("UNKNOWN Lambda requires UNKNOWN time origin")
    return errors


def make_r17_audit_certificate(*, r16_certificate: dict, lambda_time_origin: str,
                               lambda_counterfactual_scope: str,
                               formation_status_override: str | None = None) -> dict:
    errors = validate_r16_certificate(r16_certificate)
    if errors:
        raise ValueError("invalid R16 base certificate: " + "; ".join(errors))
    if r16_certificate.get("channel_schema_version") != R16_CHANNEL_SCHEMA_VERSION:
        raise ValueError("R17 upgrade requires an R16 base certificate")
    expected_status = formation_status(r16_certificate["surgery_history"])
    status = formation_status_override or expected_status
    if status != expected_status:
        raise ValueError("formation_status must agree with surgery_history")
    origin_errors = _lambda_origin_for_status(
        r16_certificate["lambda_status"], lambda_time_origin, lambda_counterfactual_scope)
    if origin_errors:
        raise ValueError("; ".join(origin_errors))

    cert = dict(r16_certificate)
    cert["channel_schema_version"] = R17_CHANNEL_SCHEMA_VERSION
    cert["lambda_time_origin"] = lambda_time_origin
    cert["lambda_counterfactual_scope"] = lambda_counterfactual_scope
    cert["current_structural_profile"] = {
        "scope": CURRENT_STRUCTURAL_SCOPE,
        "state_autonomy": cert["state_autonomy"],
        "viability_state": cert["viability_state"],
        "defense_readiness": cert["defense_readiness"],
        "composite_scale": COMPOSITE_SCALE,
    }
    cert["historical_formation_profile"] = {
        "scope": HISTORICAL_FORMATION_SCOPE,
        "formation_status": status,
        "surgery_history": cert["surgery_history"],
        "source_registration": cert["source_registration"],
        "lambda_status": cert["lambda_status"],
        "Lambda": cert["Lambda"],
        "time_origin": lambda_time_origin,
        "counterfactual_scope": lambda_counterfactual_scope,
        "evidence_only_not_scalar": True,
    }
    errors = validate_r17_certificate(cert)
    if errors:
        raise ValueError("invalid R17 certificate: " + "; ".join(errors))
    return cert


def validate_r17_certificate(cert: dict) -> list[str]:
    errors = []
    if not isinstance(cert, dict):
        return ["certificate must be an object"]
    for field in R17_EXTRA_FIELDS:
        if field not in cert:
            errors.append(f"missing R17 field {field}")
    if cert.get("channel_schema_version") != R17_CHANNEL_SCHEMA_VERSION:
        errors.append("channel_schema_version must be R17_CHANNEL_SCHEMA_V1")

    base = dict(cert)
    for field in R17_EXTRA_FIELDS:
        base.pop(field, None)
    base["channel_schema_version"] = R16_CHANNEL_SCHEMA_VERSION
    errors.extend(validate_r16_certificate(base))

    current = cert.get("current_structural_profile")
    history = cert.get("historical_formation_profile")
    if not isinstance(current, dict):
        errors.append("current_structural_profile must be an object")
    else:
        if current.get("scope") != CURRENT_STRUCTURAL_SCOPE:
            errors.append("current profile scope mismatch")
        for field in ("state_autonomy", "viability_state", "defense_readiness"):
            if current.get(field) != cert.get(field):
                errors.append(f"current profile {field} drift")
        if current.get("composite_scale") != COMPOSITE_SCALE:
            errors.append("current composite must be marked protocol-normalized, not ratio scale")
    if not isinstance(history, dict):
        errors.append("historical_formation_profile must be an object")
    else:
        if history.get("scope") != HISTORICAL_FORMATION_SCOPE:
            errors.append("history profile scope mismatch")
        expected = formation_status(cert.get("surgery_history")) if cert.get("surgery_history") in FORMATION_STATUSES else None
        if history.get("formation_status") != expected:
            errors.append("formation_status must agree with surgery_history")
        for field in ("surgery_history", "source_registration", "lambda_status", "Lambda"):
            if history.get(field) != cert.get(field):
                errors.append(f"history profile {field} drift")
        if history.get("time_origin") != cert.get("lambda_time_origin"):
            errors.append("history time_origin drift")
        if history.get("counterfactual_scope") != cert.get("lambda_counterfactual_scope"):
            errors.append("history counterfactual_scope drift")
        if history.get("evidence_only_not_scalar") is not True:
            errors.append("historical formation must be evidence-only, not a scalar")
    if "lambda_time_origin" in cert and "lambda_counterfactual_scope" in cert:
        errors.extend(_lambda_origin_for_status(
            cert.get("lambda_status"), cert["lambda_time_origin"],
            cert["lambda_counterfactual_scope"]))
    return errors


def write_r17_certificate(path: str, cert: dict) -> None:
    errors = validate_r17_certificate(cert)
    if errors:
        raise ValueError("invalid R17 certificate: " + "; ".join(errors))
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(cert, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def produce_r17_certificate(*, lambda_time_origin: str, lambda_counterfactual_scope: str,
                            formation_status_override: str | None = None,
                            **kwargs) -> dict:
    schema = kwargs.pop("channel_schema_version", None)
    if schema not in {None, R16_CHANNEL_SCHEMA_VERSION}:
        raise ValueError("produce_r17_certificate builds from the R16 base schema")
    base = produce_r15_certificate(channel_schema_version=R16_CHANNEL_SCHEMA_VERSION, **kwargs)
    return make_r17_audit_certificate(
        r16_certificate=base, lambda_time_origin=lambda_time_origin,
        lambda_counterfactual_scope=lambda_counterfactual_scope,
        formation_status_override=formation_status_override)
