"""R20 data-driven near-zero detection rule (deployable; no truth input).

R19 answer to the near-zero problem was oracle-assisted: the exact share
(known only in the white-box validation fixture) triggered the
below-detection-limit classification, and the resulting interval lived
OUTSIDE the formal certificate.  The R19 review correctly objected that a
deployment cannot know the exact share, and that on the registered instance
the sampled plug-in share and its percentile bootstrap interval both lie
ABOVE the limit, so no data-driven rule would reproduce the oracle
classification there.

R20 declares, BEFORE running the R20 study outcomes, one executable rule:

* input: the plug-in share and its trajectory-block bootstrap percentile
  95% interval (both estimable from logs alone);
* decision interval: the BASIC (pivotal) bootstrap interval of the
  bias-corrected share, [2*p - q97.5, 2*p - q2.5] clipped to [0,1] --- the
  standard bias-corrected bootstrap construction, not a post hoc choice of
  a favorable estimator;
* three-state classification against the detection limit delta:
    upper < delta  -> DATA_BELOW_LIMIT      (data support below the limit)
    lower > delta  -> DATA_ABOVE_LIMIT      (data support above the limit)
    otherwise      -> INDETERMINATE_NEAR_ZERO (cannot decide)
  Boundary equality is INDETERMINATE (fail-closed).
* reporting: BELOW and INDETERMINATE conventions export a conservative
  logical envelope [0, composite(upper)] (kind LOGICAL_ENVELOPE, NOT a
  statistical confidence interval); ABOVE conventions export the monotone
  propagation of the sampling interval (kind SAMPLING_BASIC_BOOTSTRAP).
  The plug-in composite is retained only as a DIAGNOSTIC plugin output and
  may lie outside the reported interval; it is never the reported point.

The detection limit VALUE (1e-6) is inherited from the R19 post hoc frozen
internal reporting constant; it is not a domain SESOI.  The decision RULE
is declared before the R20 study outcomes.  The old truth-triggered rule is
retained only as ``oracle_assisted_fixture_classification``, explicitly
labeled ORACLE_ASSISTED_VALIDATION_FIXTURE_ONLY_NOT_DEPLOYABLE, for
misclassification evaluation of the data rule against known truth.

This module is internal audit machinery, not external construct validation.
"""
from __future__ import annotations

import math

# Inherited from R19 NRI_SHARE_DETECTION_LIMIT (post hoc frozen internal
# reporting constant; NOT a domain SESOI, NOT a power analysis).
DETECTION_LIMIT = 1e-6
DETECTION_LIMIT_PROVENANCE = (
    "POST_HOC_FROZEN_INTERNAL_DETECTION_LIMIT_VALUE_INHERITED_FROM_R19_"
    "NOT_DOMAIN_SESOI_NOT_POWER")
DETECTION_RULE_VERSION = "R20_BASIC_BOOTSTRAP_BIAS_CORRECTED_THREE_STATE_V1"
DETECTION_RULE_PROVENANCE = (
    "RULE_DECLARED_BEFORE_R20_STUDY_OUTCOMES_LIMIT_VALUE_POST_HOC_FROZEN_R19_"
    "NOT_DOMAIN_SESOI_NOT_POWER")
ORACLE_RULE_LABEL = "ORACLE_ASSISTED_VALIDATION_FIXTURE_ONLY_NOT_DEPLOYABLE"

CONVENTION_STATUSES = frozenset({
    "DATA_BELOW_LIMIT", "DATA_ABOVE_LIMIT", "INDETERMINATE_NEAR_ZERO"})
ORACLE_COMPARISONS = frozenset({
    "TRUE_BELOW", "FALSE_ABOVE", "INDETERMINATE_TRUE_BELOW",
    "TRUE_ABOVE", "FALSE_BELOW", "INDETERMINATE_TRUE_ABOVE"})


def _check_share(value, label: str) -> float:
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{label} must be finite and in [0,1], got {value!r}")
    return value


def _check_limit(limit) -> float:
    limit = float(limit)
    if not math.isfinite(limit) or limit <= 0.0 or limit >= 1.0:
        raise ValueError("detection limit must be finite and in (0,1)")
    return limit


def basic_bootstrap_bias_corrected_interval(plugin_share: float,
                                            percentile_lower: float,
                                            percentile_upper: float) -> list[float]:
    """Basic (pivotal) bootstrap interval of the bias-corrected share.

    corrected = 2*plugin - bootstrap_mean; the basic interval reflects the
    percentile interval about the plug-in: [2p - q97.5, 2p - q2.5], clipped
    to [0,1].  Declared construction; no truth input.
    """
    plugin_share = _check_share(plugin_share, "plugin_share")
    percentile_lower = _check_share(percentile_lower, "percentile_lower")
    percentile_upper = _check_share(percentile_upper, "percentile_upper")
    if percentile_lower > percentile_upper:
        raise ValueError("percentile interval must be ordered")
    lower = min(1.0, max(0.0, 2.0 * plugin_share - percentile_upper))
    upper = min(1.0, max(0.0, 2.0 * plugin_share - percentile_lower))
    return [lower, upper]


def classify_share_interval(interval, limit: float = DETECTION_LIMIT) -> str:
    """Three-state data-driven classification.  No truth input.

    Strict inequalities; a bound exactly at the limit is INDETERMINATE
    (fail-closed: the data do not strictly support either side).
    """
    limit = _check_limit(limit)
    if not isinstance(interval, (list, tuple)) or len(interval) != 2:
        raise ValueError("decision interval must be [lower, upper]")
    lower = _check_share(interval[0], "interval lower")
    upper = _check_share(interval[1], "interval upper")
    if lower > upper:
        raise ValueError("decision interval must be ordered")
    if upper < limit:
        return "DATA_BELOW_LIMIT"
    if lower > limit:
        return "DATA_ABOVE_LIMIT"
    return "INDETERMINATE_NEAR_ZERO"


def oracle_assisted_fixture_classification(exact_share: float,
                                           limit: float = DETECTION_LIMIT) -> dict:
    """R19 truth-triggered rule, retained ONLY for fixture evaluation.

    This is NOT a deployable decision rule: the exact share is unknown in a
    real audit.  It is used to label the data rule's classifications as
    true/false/indeterminate in the validation fixture and the multi-seed
    misclassification study.
    """
    exact_share = _check_share(exact_share, "exact_share")
    limit = _check_limit(limit)
    return {"label": ORACLE_RULE_LABEL,
            "exact_share": exact_share,
            "oracle_below_limit": bool(exact_share < limit),
            "detection_limit": limit}


def _oracle_comparison(status: str, oracle_below: bool) -> str:
    if status == "DATA_BELOW_LIMIT":
        return "TRUE_BELOW" if oracle_below else "FALSE_BELOW"
    if status == "DATA_ABOVE_LIMIT":
        return "FALSE_ABOVE" if oracle_below else "TRUE_ABOVE"
    return ("INDETERMINATE_TRUE_BELOW" if oracle_below
            else "INDETERMINATE_TRUE_ABOVE")


def convention_detection_report(*, plugin_share: float,
                                percentile_interval,
                                composite_fn=None,
                                limit: float = DETECTION_LIMIT,
                                exact_share=None) -> dict:
    """Full per-convention detection report from estimable inputs only.

    ``composite_fn`` maps a share to the composite with the other channels
    held at their declared bounds (coordinatewise monotone); it may be None
    when another channel is undefined (degraded reflection), in which case
    composite intervals are null and only the share decision is reported.

    ``exact_share`` is OPTIONAL and used only to attach an explicitly
    labeled oracle evaluation for the validation fixture; it never enters
    the decision.
    """
    limit = _check_limit(limit)
    plugin_share = _check_share(plugin_share, "plugin_share")
    if not isinstance(percentile_interval, (list, tuple)) or len(percentile_interval) != 2:
        raise ValueError("percentile_interval must be [lower, upper]")
    decision_interval = basic_bootstrap_bias_corrected_interval(
        plugin_share, percentile_interval[0], percentile_interval[1])
    status = classify_share_interval(decision_interval, limit)
    sampling_composite = None
    plugin_composite = None
    if composite_fn is not None:
        sampling_composite = [float(composite_fn(decision_interval[0])),
                              float(composite_fn(decision_interval[1]))]
        plugin_composite = float(composite_fn(plugin_share))
    if status == "DATA_ABOVE_LIMIT":
        reported_composite = sampling_composite
        reported_kind = "SAMPLING_BASIC_BOOTSTRAP"
    else:
        # Conservative logical envelope: the share may be anywhere in
        # [0, upper]; geometric annihilation gives lower composite 0.
        reported_composite = (None if composite_fn is None
                              else [0.0, float(composite_fn(decision_interval[1]))])
        reported_kind = "LOGICAL_ENVELOPE"
    report = {
        "convention_status": status,
        "share_interval": {"bounds": list(decision_interval),
                           "kind": "SAMPLING_BASIC_BOOTSTRAP"},
        "share_bootstrap_percentile_95": [float(percentile_interval[0]),
                                          float(percentile_interval[1])],
        "composite_interval": (None if reported_composite is None
                               else {"bounds": list(reported_composite),
                                     "kind": reported_kind}),
        "composite_interval_sampling": (None if sampling_composite is None
                                        else {"bounds": list(sampling_composite),
                                              "kind": "SAMPLING_BASIC_BOOTSTRAP"}),
        "diagnostic_plugin_share": plugin_share,
        "diagnostic_plugin_composite": plugin_composite,
        "detection_limit": limit,
        "detection_rule_version": DETECTION_RULE_VERSION,
        "detection_provenance": DETECTION_RULE_PROVENANCE,
    }
    if exact_share is not None:
        oracle = oracle_assisted_fixture_classification(exact_share, limit)
        oracle["classification_vs_oracle"] = _oracle_comparison(
            status, oracle["oracle_below_limit"])
        report["oracle_evaluation"] = oracle
    return report