"""R17 historical-formation audit helpers and fixed-point implant witness.

Current structural autonomy and historical formation autonomy are co-primary
outputs.  The historical profile is evidence, not a scalar inferred from the
five current channels.  Lambda time origins are distinct estimands.
"""
from __future__ import annotations

FORMATION_STATUSES = {
    0: "NO_REGISTERED_SURGERY",
    1: "REGISTERED_SURGERY",
    None: "UNKNOWN",
}

LAMBDA_TIME_ORIGIN_SCOPE = {
    "AUDIT_CURRENT_REMOVAL": "REMOVE_REGISTERED_SURGERIES_AT_AUDIT",
    "ORIGINAL_IMPLANT_PREVENTION": "PREVENT_ORIGINAL_SURGERY_AND_RECOMPUTE_DESCENDANTS",
    "NOT_APPLICABLE": "NOT_APPLICABLE",
    "UNKNOWN": "UNKNOWN",
}


def formation_status(surgery_history: int | None) -> str:
    if surgery_history not in FORMATION_STATUSES:
        raise ValueError("surgery_history must be 0, 1, or None")
    return FORMATION_STATUSES[surgery_history]


def validate_lambda_time_origin(origin: str, scope: str) -> None:
    if origin not in LAMBDA_TIME_ORIGIN_SCOPE:
        raise ValueError("invalid lambda_time_origin")
    if LAMBDA_TIME_ORIGIN_SCOPE[origin] != scope:
        raise ValueError("lambda_time_origin and lambda_counterfactual_scope must match")


def fixed_point_replacement_witness() -> dict:
    """A goal implant between two distinct self-endorsed fixed points.

    Theta={0,0.5,1,1.5,2}, Fix={0,1}, d_c=1.  U0=0 and U1=1 are both fixed
    points, so A_goal=1 before and after.  The update is registered inside N,
    hence residual external bypass flow is zero by construction.  The current
    channel profile cannot distinguish the two formations; the historical
    profile must.  The two Lambda values below are different counterfactual
    estimands, not interchangeable readings.
    """
    return {
        "Theta": [0.0, 0.5, 1.0, 1.5, 2.0],
        "Fix": [0.0, 1.0],
        "d_c": 1.0,
        "U_before": 0.0,
        "U_after": 1.0,
        "A_goal_before": 1.0,
        "A_goal_after": 1.0,
        "current_channel_profile_identical": True,
        "residual_external_bypass_flow": 0.0,
        "surgery_history": 1,
        "historical_formation_status": "REGISTERED_SURGERY",
        "lambda_audit_current_removal": 1.0,
        "lambda_audit_current_removal_note": (
            "At audit the implant is already formed; removing currently active "
            "endorsement surgeries leaves the formed goal U1 and identity output Y=U1."
        ),
        "lambda_original_implant_prevention": 0.0,
        "lambda_original_implant_prevention_note": (
            "Preventing the original implant keeps U0; with identity output Y=U, "
            "the factual U1 and prevented U0 point-mass laws differ maximally."
        ),
        "interpretation": (
            "A_goal=1 is present fixed-point alignment, not provenance legitimacy. "
            "Historical formation requires the co-primary history profile."
        ),
    }
