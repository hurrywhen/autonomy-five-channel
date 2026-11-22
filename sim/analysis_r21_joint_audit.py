#!/usr/bin/env python3
"""R21 native joint-log audit artifact (internal only).

Supersedes the R20 joint-audit artifact (retained read-only).  R21 keeps the
R20 data-driven detection rule and three-state sensitivity unchanged, and closes
the R20 review's two remaining items:

1. **Conditioning disclosure.**  Above-limit composite sampling intervals are
   SHARE-CONDITIONAL (only the source-share basic bootstrap interval is
   propagated; other channels fixed at plugin/structural points).  Their kind is
   SHARE_CONDITIONAL_SAMPLING_BASIC_BOOTSTRAP with a conditioning_scope field,
   and the certificate carries a composite_interval_conditioning policy.
2. **Coverage semantics separated + joint diagnostic.**  Logical-envelope anchor
   containment is reported as a containment diagnostic (never statistical
   coverage); share-conditional sampling coverage is reported with its scope; a
   supplementary JOINT trajectory bootstrap (all channels recomputed per
   resample) gives a genuine joint composite sampling interval.  Under-coverage
   is attributed to BOTH plug-in bias and the share-conditional design.

Software validation checks formulas, structures, boundaries, analytic anchors,
and governance --- NOT expected empirical outcomes.  Empirical coverage/bias
findings are descriptive, recorded here and in the detection study.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "src"))

from autonomy_sim.aggregate import composite_A  # noqa: E402
from autonomy_sim.native_joint_audit import ALTERNATIVE_PARTITION_NAME  # noqa: E402
from autonomy_sim.r20_detection import (DETECTION_LIMIT,  # noqa: E402
                                        DETECTION_RULE_VERSION,
                                        basic_bootstrap_bias_corrected_interval,
                                        classify_share_interval)
from autonomy_sim.r21_guards import (COMPOSITE_INTERVAL_CONDITIONING,  # noqa: E402
                                     SHARE_CONDITIONAL_KIND,
                                     produce_r21_certificate, validate_r21_certificate)
from autonomy_sim.r21_joint_audit import run_joint_audit_r21  # noqa: E402
from autonomy_sim.formation_audit import fixed_point_replacement_witness  # noqa: E402
from autonomy_sim.r19_guards import (ORDER_SENSITIVITY_THRESHOLD,  # noqa: E402
                                     SEMANTIC_SENSITIVITY_THRESHOLD,
                                     THRESHOLD_PROVENANCE)
from analysis_r15_x5c_paired import compare_replay_json  # noqa: E402

REPLAY_FIELD_TOLERANCES = {
    "input_distribution_over_allowed": 1e-6,
    "empowerment_nats": 1e-9,
    "capacity_certificate_nats": 1e-9,
    "a_exec": 1e-9,
}
CONVENTION_KEYS = (("RNI", "normative_share_RNI"),
                   ("NRI", "normative_share_NRI"),
                   ("order_average", "normative_share_order_average"))
COVERAGE_SEMANTICS = {
    "logical_envelope_anchor_containment":
        "CONTAINMENT_DIAGNOSTIC_NOT_STATISTICAL_COVERAGE",
    "share_conditional_sampling_interval_coverage":
        "CONDITIONAL_ON_OTHER_CHANNELS_FIXED_AT_PLUGIN",
    "joint_sampling_interval_coverage":
        "SUPPLEMENTARY_JOINT_DIAGNOSTIC_NOT_CERTIFICATE_REPORTED_SEMANTICS",
    "no_combined_or_cross_kind_coverage_comparison": True,
    "undercoverage_causes": ["directed_information_plugin_bias",
                             "share_conditional_design_other_channels_fixed"],
}


def _binary_entropy(p: float) -> float:
    if p <= 0 or p >= 1:
        return 0.0
    return -p * math.log(p) - (1 - p) * math.log(1 - p)


def _sha(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _percentiles(intervals: dict) -> dict:
    return {convention: (intervals[key]["percentile_95"] if intervals[key] else None)
            for convention, key in CONVENTION_KEYS}


def _channel_profile(*, channels: dict, reflection: dict, goal: dict,
                     org_interval=None, org_kind=None, epi_interval=None,
                     ref_protocol: str = "FIDELITY_CONSISTENCY_LAMBDA_R21") -> dict:
    a_ref = reflection["A_ref"]
    if a_ref is None:
        ref_entry = {"value": None, "state": "INTERVAL",
                     "interval": list(reflection["A_ref_interval"]),
                     "interval_kind": "LOGICAL_ENVELOPE",
                     "protocol_version": ref_protocol,
                     "degradation_reason": reflection["degradation_reason"],
                     "fidelity": reflection["fidelity"],
                     "endorsement_consistency": reflection["endorsement_consistency"],
                     "Lambda": reflection["Lambda"],
                     "event_counts": dict(reflection["event_counts"])}
    else:
        ref_entry = {"value": a_ref, "state": "DEFINED", "interval": None,
                     "protocol_version": ref_protocol,
                     "fidelity": reflection["fidelity"],
                     "endorsement_consistency": reflection["endorsement_consistency"],
                     "Lambda": reflection["Lambda"],
                     "event_counts": dict(reflection["event_counts"])}
    if channels["a_org_RNI"] is None:
        org_entry = {"value": None, "state": "INTERVAL", "interval": [0.0, 1.0],
                     "interval_kind": "LOGICAL_ENVELOPE",
                     "protocol_version": "RNI_ORDERED_RESIDUAL_SHARE_R21"}
    elif org_interval is not None:
        org_entry = {"value": None, "state": "INTERVAL", "interval": list(org_interval),
                     "interval_kind": org_kind,
                     "protocol_version": "RNI_ORDERED_RESIDUAL_SHARE_R21"}
    else:
        org_entry = {"value": channels["a_org_RNI"], "state": "DEFINED",
                     "interval": None,
                     "protocol_version": "RNI_ORDERED_RESIDUAL_SHARE_R21"}
    epi_entry = {"value": channels["a_epi"], "state": "DEFINED",
                 "interval": epi_interval,
                 "protocol_version": "LOGGED_BELIEF_ACCURACY_R21"}
    if epi_interval is not None:
        epi_entry["interval_kind"] = "SAMPLING_NORMAL_APPROX"
    return {
        "a_org": org_entry,
        "a_goal": {"value": channels["a_goal_structural"], "state": "DEFINED",
                   "interval": None,
                   "protocol_version": "STRUCTURAL_POINT_AND_IRL_INTERVAL_R21",
                   "structural_point": channels["a_goal_structural"],
                   "irl_interval": list(goal["behavior_IRL_identified_interval"]),
                   "irl_interval_kind": "MODEL_SELECTION"},
        "a_exec": {"value": channels["a_exec_open_loop"], "state": "DEFINED",
                   "interval": None,
                   "protocol_version": "PRECOMMITTED_OPEN_LOOP_CANONICAL_R21",
                   "horizon_actions": 2, "uses_intermediate_observations": False},
        "a_epi": epi_entry,
        "a_ref": ref_entry,
    }


def _attribution(source: dict, intervals, weights: list[float], *,
                 mode: str) -> dict:
    registered = json.loads(json.dumps(source["registered_partition"]))
    alternative = json.loads(json.dumps(
        source[f"alternative_partition_{ALTERNATIVE_PARTITION_NAME}"]))
    if mode == "INTERVAL":
        registered["share_bootstrap_percentile_95"] = _percentiles(intervals[0])
        alternative["share_bootstrap_percentile_95"] = _percentiles(intervals[1])
    return {"registered_partition": registered,
            "alternative_partitions": {ALTERNATIVE_PARTITION_NAME: alternative},
            "weights": list(weights), "sigma": 1.0}


def _certificate(*, channels: dict, reflection: dict, goal: dict, config: dict,
                 viability: float, defense: float, surgery: int,
                 source: dict, intervals, evidence_payload,
                 org_interval=None, org_kind=None, epi_interval=None,
                 ref_protocol: str = "FIDELITY_CONSISTENCY_LAMBDA_R21") -> dict:
    profile = _channel_profile(channels=channels, reflection=reflection, goal=goal,
                               org_interval=org_interval, org_kind=org_kind,
                               epi_interval=epi_interval, ref_protocol=ref_protocol)
    mode = "POINT" if org_interval is None and channels["a_org_RNI"] is not None \
        and reflection["A_ref"] is not None else "INTERVAL"
    cert = produce_r21_certificate(
        layer="L2", channel_profile=profile,
        attribution=_attribution(source, intervals, config["weights"], mode=mode),
        viability_state=viability, defense_readiness=defense,
        surgery_history=surgery,
        lambda_value=reflection["Lambda"],
        lambda_status="DEFINED" if reflection["Lambda"] is not None else "UNKNOWN",
        source_registration="COMPLETE", mechanism_evidence="NONE",
        goal_mode="STRUCTURAL_POINT",
        lambda_time_origin=("AUDIT_CURRENT_REMOVAL" if reflection["Lambda"] is not None
                            else "UNKNOWN"),
        lambda_counterfactual_scope=("REMOVE_REGISTERED_SURGERIES_AT_AUDIT"
                                     if reflection["Lambda"] is not None else "UNKNOWN"),
        model_hash=_sha(config), evidence_hash=_sha(evidence_payload))
    errors = validate_r21_certificate(cert)
    if errors:
        raise ValueError("R21 native certificate invalid: " + "; ".join(errors))
    return cert


def _exact_evidence_payload(bundle: dict) -> dict:
    return {"config": bundle["config"], "source": bundle["source"],
            "channels": bundle["channels"], "reflection": bundle["reflection"],
            "goal": bundle["goal"], "epistemic": bundle["epistemic"],
            "viability_state": bundle["viability_state"],
            "defense_readiness": bundle["defense_readiness"],
            "analytic_capacity_nats":
                bundle["execution_open_loop"]["analytic_capacity_nats"]}


def _exact_certificate(bundle: dict) -> dict:
    reflection = dict(bundle["reflection"])
    reflection["event_counts"] = {
        "normative_update_events": 2 ** (1 + 3 * bundle["config"]["horizon"])
        * bundle["config"]["horizon"],
        "endorsement_events": 2 ** (1 + 3 * bundle["config"]["horizon"])
        * bundle["config"]["horizon"],
        "surgery_contexts": 2 ** (1 + 3 * bundle["config"]["horizon"]),
        "carrier": "EXACT_ENUMERATION_OF_REGISTERED_SCM"}
    reflection["A_ref_interval"] = None
    reflection["degradation_reason"] = None
    return _certificate(
        channels=bundle["channels"], reflection=reflection, goal=bundle["goal"],
        config=bundle["config"], viability=bundle["viability_state"],
        defense=bundle["defense_readiness"], surgery=bundle["config"]["surgery"],
        source=bundle["source"], intervals=None,
        evidence_payload=_exact_evidence_payload(bundle),
        ref_protocol="FIDELITY_CONSISTENCY_LAMBDA_R21_EXACT_ENUMERATION")


def _independent_exact_composites(exact: dict) -> dict:
    channels = exact["channels"]
    weights = exact["config"]["weights"]
    viability = exact["viability_state"]
    rest = (channels["a_goal_structural"], channels["a_exec_open_loop"],
            channels["a_epi"], channels["a_ref"])
    partitions = {
        "registered": exact["source"]["registered_partition"],
        ALTERNATIVE_PARTITION_NAME:
            exact["source"][f"alternative_partition_{ALTERNATIVE_PARTITION_NAME}"],
    }
    out = {}
    for name, report in partitions.items():
        out[name] = {}
        for convention, key in CONVENTION_KEYS:
            out[name][convention] = float(composite_A(
                viability, (report[key],) + rest, weights, sigma=1.0))
    return out


def _convention_table(result: dict) -> dict:
    """Exact anchors vs DIAGNOSTIC plug-in vs REPORTED share-conditional intervals,
    with separated containment/coverage semantics and the supplementary joint interval."""
    exact = result["exact_truth"]
    independent = _independent_exact_composites(exact)
    cert_reports = result["baseline_certificate"]["attribution_sensitivity"]["convention_reports"]
    joint = result["joint_bootstrap"]["composite_intervals"]
    table = {}
    for partition in ("registered", ALTERNATIVE_PARTITION_NAME):
        table[partition] = {}
        for convention, _ in CONVENTION_KEYS:
            exact_value = independent[partition][convention]
            rep = cert_reports[partition][convention]
            plugin = rep["diagnostic_plugin_composite"]
            bounds = rep["composite_interval"]["bounds"]
            kind = rep["composite_interval"]["kind"]
            contains = bool(bounds[0] <= exact_value <= bounds[1])
            joint_iv = joint[partition][convention]
            joint_bounds = joint_iv["percentile_95"] if joint_iv else None
            table[partition][convention] = {
                "exact_composite_model_anchor": exact_value,
                "diagnostic_plugin_composite": plugin,
                "diagnostic_abs_error": abs(plugin - exact_value),
                "convention_status": rep["convention_status"],
                "reported_composite_interval": list(bounds),
                "reported_interval_kind": kind,
                "reported_interval_conditioning_scope":
                    rep["composite_interval"].get("conditioning_scope"),
                # Separated semantics: envelope -> containment; sampling -> coverage.
                "logical_envelope_anchor_containment":
                    contains if kind == "LOGICAL_ENVELOPE" else None,
                "share_conditional_sampling_covers_exact":
                    contains if kind == SHARE_CONDITIONAL_KIND else None,
                # Supplementary joint diagnostic (not the reported semantics).
                "joint_sampling_interval": joint_bounds,
                "joint_sampling_covers_exact":
                    (bool(joint_bounds[0] <= exact_value <= joint_bounds[1])
                     if joint_bounds else None),
            }
    return table


def compute(*, n_samples: int = 8192, seed: int = 20261122,
            n_bootstrap: int = 100, n_joint_bootstrap: int = 200) -> dict:
    result = run_joint_audit_r21(n_samples=n_samples, seed=seed, n_bootstrap=n_bootstrap,
                                 n_joint_bootstrap=n_joint_bootstrap)
    sampled = result["sampled"]
    config = result["config"]
    evidence_payload = result["evidence_binding"]["payload"]
    bi = sampled["source_bootstrap_intervals"]
    bai = sampled["alternative_bootstrap_intervals"]
    rni_plugin = sampled["source"]["registered_partition"]["normative_share_RNI"]
    org_interval = basic_bootstrap_bias_corrected_interval(
        rni_plugin, *bi["normative_share_RNI"]["percentile_95"])
    result["baseline_certificate"] = _certificate(
        channels=sampled["channels"], reflection=sampled["reflection"],
        goal=sampled["goal"], config=config, viability=sampled["viability_state"],
        defense=sampled["defense_readiness"], surgery=0,
        source=sampled["source"], intervals=(bi, bai),
        evidence_payload=evidence_payload,
        org_interval=org_interval, org_kind="SAMPLING_BASIC_BOOTSTRAP",
        epi_interval=sampled["epistemic"]["normal_95"])
    result["baseline_certificate_exact"] = _exact_certificate(result["exact_truth"])
    result["surgery_certificate_exact"] = _exact_certificate(result["surgery_arm_exact"])
    result["decoupled_certificate_exact"] = _exact_certificate(
        result["action_decoupled_negative_control_exact"])
    for arm, key, surgery in (("surgery", "surgery_arm_sampled", 1),
                              ("decoupled", "action_decoupled_negative_control_sampled", 0)):
        arm_sampled = result[key]
        arm_config = dict(config, surgery=1) if arm == "surgery" \
            else dict(config, action_effect=False)
        abi = arm_sampled["source_bootstrap_intervals"]
        abai = arm_sampled["alternative_bootstrap_intervals"]
        arm_rni = arm_sampled["source"]["registered_partition"]["normative_share_RNI"]
        arm_org = basic_bootstrap_bias_corrected_interval(
            arm_rni, *abi["normative_share_RNI"]["percentile_95"])
        hashes_key = ("surgery" if arm == "surgery" else "decoupled")
        result[f"{arm}_certificate_sampled"] = _certificate(
            channels=arm_sampled["channels"], reflection=arm_sampled["reflection"],
            goal=arm_sampled["goal"], config=arm_config,
            viability=arm_sampled["viability_state"],
            defense=arm_sampled["defense_readiness"], surgery=surgery,
            source=arm_sampled["source"], intervals=(abi, abai),
            evidence_payload={"log_hashes": {
                f"{hashes_key}_operating_log_sha256":
                    result["logs"][f"{hashes_key}_operating_log_sha256"],
                f"{hashes_key}_execution_log_sha256":
                    result["logs"][f"{hashes_key}_execution_log_sha256"]},
                "config": arm_config, "seed": seed,
                "n_samples_per_stream": n_samples},
            org_interval=arm_org, org_kind="SAMPLING_BASIC_BOOTSTRAP",
            epi_interval=arm_sampled["epistemic"]["normal_95"])
    result["fixed_point_implant_witness"] = fixed_point_replacement_witness()
    result["convention_composite_table"] = _convention_table(result)
    result["coverage_semantics"] = dict(COVERAGE_SEMANTICS)
    result["sensitivity_thresholds"] = {
        "order_composite_spread": ORDER_SENSITIVITY_THRESHOLD,
        "semantic_partition_spread": SEMANTIC_SENSITIVITY_THRESHOLD,
        "provenance": THRESHOLD_PROVENANCE,
        "note": ("Post hoc frozen internal engineering thresholds on the composite "
                 "scale, frozen after the R17-native results were observed; not a "
                 "domain SESOI, not a power calculation. Evaluated against "
                 "minimum-possible/worst-case convention separation (three-state "
                 "system), never midpoint agreement."),
    }
    result["replay_policy"] = {
        "default_float_abs_tol": 1e-12,
        "field_tolerances": REPLAY_FIELD_TOLERANCES,
        "justification": ("Capacity-achieving input distributions are generally "
                          "non-unique; canonicalized coordinates carry a declared "
                          "1e-6 field tolerance, capacity-derived values 1e-9. "
                          "Raw log hashes, counts, seeds, and statuses remain "
                          "byte-exact and are never covered by float tolerances."),
    }
    result["detection_rule_declaration"] = {
        "rule_version": DETECTION_RULE_VERSION,
        "decision_inputs": ["plug-in share", "trajectory-block bootstrap percentile 95% interval"],
        "decision_interval": "basic (pivotal) bootstrap interval of the bias-corrected share, clipped to [0,1]",
        "classification": {
            "DATA_BELOW_LIMIT": "upper bound < detection limit",
            "DATA_ABOVE_LIMIT": "lower bound > detection limit",
            "INDETERMINATE_NEAR_ZERO": "otherwise (boundary equality fail-closed)"},
        "reporting": ("BELOW/INDETERMINATE -> conservative LOGICAL_ENVELOPE "
                      "[0, composite(upper)] (not a confidence interval); "
                      "ABOVE -> SHARE-CONDITIONAL propagation of the share sampling "
                      "interval (other channels fixed at points); plug-in composite "
                      "retained only as diagnostic output"),
        "detection_limit": DETECTION_LIMIT,
        "declared_before_r20_study_outcomes": True,
        "oracle_rule": "ORACLE_ASSISTED_VALIDATION_FIXTURE_ONLY_NOT_DEPLOYABLE",
    }
    result["conditioning_note"] = (
        "Above-detection-limit composite sampling intervals are SHARE-CONDITIONAL: "
        "they propagate only the source-share basic bootstrap interval, with the "
        "execution, epistemic, and reflection channels fixed at their declared "
        "plugin/structural point estimates (conditioning_scope). They are NOT full "
        "joint-uncertainty intervals. Their under-coverage has two causes: (i) "
        "finite-sample plug-in bias of the directed-information share estimates, and "
        "(ii) the share-conditional design itself (other channels' estimation error "
        "and inter-channel covariance are not propagated). The supplementary joint "
        "trajectory bootstrap recomputes all channels per resample and quantifies the "
        "second cause; it does not remove the first. Logical-envelope anchor "
        "containment is a containment diagnostic, not statistical coverage, and is "
        "never combined with or compared against sampling-interval coverage.")
    result["bias_note"] = (
        "Plug-in directed-information estimates have finite-sample bias; the "
        "geometric composite amplifies near-zero share differences (x^0.2). The "
        "diagnostic plug-in NRI composite is NOT the reported certificate semantics: "
        "the formal certificate reports the data-driven detection status and the "
        "declared share-conditional interval / logical envelope. Exact-truth "
        "composites are model anchors, not evidence of finite-sample recoverability. "
        "On this instance the data-driven rule returns INDETERMINATE_NEAR_ZERO for "
        "NRI: the honest conclusion is that n=8192 data cannot confirm the near-zero "
        "share, not that the share is confirmed above it.")
    return result


def validate_result(result: dict) -> None:
    """Software correctness only; empirical coverage/bias are descriptive."""
    exact = result["exact_truth"]
    config = result["config"]
    p, q = config["p_obs"], config["q_self"]
    expected_exec = ((math.log(2.0) - _binary_entropy(p)) / (2 * math.log(2.0))
                     if config["action_effect"] else 0.0)
    expected_fidelity = 1.0 - _binary_entropy(q) / math.log(2.0)
    for name, actual, expected in (
            ("a_epi", exact["channels"]["a_epi"], 1 - p),
            ("a_goal", exact["channels"]["a_goal_structural"], 0.5),
            ("a_exec", exact["channels"]["a_exec_open_loop"], expected_exec),
            ("fidelity", exact["reflection"]["fidelity"], expected_fidelity),
            ("Lambda", exact["reflection"]["Lambda"], 1.0)):
        if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError(f"R21 exact anchor failed: {name}")
    if result["surgery_arm_exact"]["reflection"]["Lambda"] != 0.0:
        raise ValueError("surgery Lambda anchor failed")
    if result["action_decoupled_negative_control_exact"]["execution_open_loop"]["state_averaged_a_exec"] != 0.0:
        raise ValueError("decoupled open-loop zero anchor failed")

    n = result["n_samples_per_stream"]
    counts = result["sampled"]["reflection"]["event_counts"]
    if counts["normative_update_events"] != n * config["horizon"]:
        raise ValueError("normative-update event count mismatch")
    if counts["endorsement_events"] != counts["normative_update_events"]:
        raise ValueError("endorsement event count mismatch")
    if counts["surgery_contexts"] != n:
        raise ValueError("surgery-context count mismatch")
    if result["logs"]["operating_trajectories"] != n:
        raise ValueError("operating batch size mismatch")
    if result["logs"]["execution_trajectories"] != 4 * n:
        raise ValueError("execution stream size mismatch")
    if result["logs"]["execution_excerpt"]["uses_intermediate_observations"]:
        raise ValueError("execution stream must not read intermediate observations")

    binding = result["evidence_binding"]
    if binding["policy"] != "IMMUTABLE_RAW_INPUTS_ONLY_NOT_ANALYSIS_OUTPUTS":
        raise ValueError("evidence binding policy drift")
    if _sha(binding["payload"]) != binding["evidence_sha256"]:
        raise ValueError("evidence binding hash mismatch")
    payload = binding["payload"]
    if set(payload) != {"log_hashes", "config", "seed", "n_samples_per_stream",
                        "n_bootstrap", "log_schema"}:
        raise ValueError("evidence payload must contain immutable registered inputs only")
    cert = result["baseline_certificate"]
    if cert["evidence_hash"] != binding["evidence_sha256"]:
        raise ValueError("baseline certificate must bind the immutable-input hash")

    sampled = result["sampled"]
    independent_plugin = float(composite_A(
        sampled["viability_state"],
        (sampled["channels"]["a_org_RNI"], sampled["channels"]["a_goal_structural"],
         sampled["channels"]["a_exec_open_loop"], sampled["channels"]["a_epi"],
         sampled["channels"]["a_ref"]), config["weights"], sigma=1.0))
    if abs(result["diagnostic_state_autonomy_RNI_plugin"] - independent_plugin) > 1e-12:
        raise ValueError("diagnostic plugin composite must equal the five-channel recomputation")
    if abs(result["diagnostic_state_autonomy_RNI_plugin"] - sampled["viability_state"]) < 1e-9:
        raise ValueError("diagnostic plugin composite must not collapse to the resource gate")

    # Formal sampled certificate: INTERVAL, no scalar, detection + conditioning inside.
    if validate_r21_certificate(cert):
        raise ValueError("baseline R21 certificate invalid")
    if cert["certificate_mode"] != "INTERVAL" or cert["state_autonomy"] is not None:
        raise ValueError("sampled baseline must be INTERVAL-valued with no point export")
    if cert["composite_interval_conditioning"] != COMPOSITE_INTERVAL_CONDITIONING:
        raise ValueError("certificate must declare the share-conditional conditioning policy")
    reports = cert["attribution_sensitivity"]["convention_reports"]
    if set(reports) != {"registered", ALTERNATIVE_PARTITION_NAME}:
        raise ValueError("convention_reports must cover both partitions")
    for partition, conventions in reports.items():
        if set(conventions) != {"RNI", "NRI", "order_average"}:
            raise ValueError("convention_reports must cover all three conventions")
        for convention, rep in conventions.items():
            for field in ("convention_status", "share_interval", "composite_interval",
                          "detection_limit", "detection_rule_version",
                          "detection_provenance", "diagnostic_plugin_share",
                          "diagnostic_plugin_composite"):
                if field not in rep:
                    raise ValueError(f"convention report missing {field}")
            if rep["detection_limit"] != DETECTION_LIMIT:
                raise ValueError("detection limit drift")
            if rep["detection_rule_version"] != DETECTION_RULE_VERSION:
                raise ValueError("detection rule version drift")
            perc = rep["share_bootstrap_percentile_95"]
            decision = basic_bootstrap_bias_corrected_interval(
                rep["diagnostic_plugin_share"], perc[0], perc[1])
            if any(abs(a - b) > 1e-12 for a, b in
                   zip(decision, rep["share_interval"]["bounds"])):
                raise ValueError("share interval must equal the declared basic interval")
            if classify_share_interval(decision) != rep["convention_status"]:
                raise ValueError("convention status must equal the declared classification")
            ci = rep["composite_interval"]
            if ci.get("conditioning_scope") != "other_channels_fixed_at_plugin":
                raise ValueError("composite interval must disclose its conditioning scope")
            if rep["convention_status"] == "DATA_ABOVE_LIMIT":
                if ci["kind"] != SHARE_CONDITIONAL_KIND:
                    raise ValueError("ABOVE_LIMIT composite must be share-conditional sampling")
            elif ci["kind"] != "LOGICAL_ENVELOPE":
                raise ValueError("BELOW/INDETERMINATE composite must be a logical envelope")
            if rep["share_interval"]["kind"] != "SAMPLING_BASIC_BOOTSTRAP":
                raise ValueError("the share interval itself is unconditional sampling")
    if cert["detection_policy"]["deployable_decision_uses_exact_truth"]:
        raise ValueError("deployable decision must not use exact truth")
    if "oracle_evaluation" in json.dumps(reports):
        raise ValueError("oracle evaluation must stay outside the formal certificate")
    all_bounds = [rep["composite_interval"]["bounds"]
                  for partition in reports.values() for rep in partition.values()]
    hull = [min(b[0] for b in all_bounds), max(b[1] for b in all_bounds)]
    if any(abs(a - b) > 1e-12 for a, b in
           zip(hull, cert["attribution_sensitivity"]["overall_composite_range"])):
        raise ValueError("overall_composite_range must equal the reported-interval hull")
    if any(abs(a - b) > 1e-12 for a, b in zip(hull, cert["state_autonomy_interval"])):
        raise ValueError("state_autonomy_interval must equal the reported-interval hull")
    for partition, conventions in result["detection_reports"].items():
        for convention, rep in conventions.items():
            cert_rep = reports[partition][convention]
            if rep["convention_status"] != cert_rep["convention_status"]:
                raise ValueError("audit/certificate detection status drift")
            if rep["oracle_evaluation"]["label"] != \
                    "ORACLE_ASSISTED_VALIDATION_FIXTURE_ONLY_NOT_DEPLOYABLE":
                raise ValueError("oracle evaluation must carry the fixture-only label")

    # Coverage semantics separation (governance, not empirical).
    if result["coverage_semantics"] != COVERAGE_SEMANTICS:
        raise ValueError("coverage semantics must separate envelope containment from coverage")
    table = result["convention_composite_table"]
    for partition, conventions in table.items():
        for convention, row in conventions.items():
            kind = row["reported_interval_kind"]
            if kind == "LOGICAL_ENVELOPE":
                if row["logical_envelope_anchor_containment"] is None or \
                        row["share_conditional_sampling_covers_exact"] is not None:
                    raise ValueError("envelope must report containment, not sampling coverage")
            elif kind == SHARE_CONDITIONAL_KIND:
                if row["share_conditional_sampling_covers_exact"] is None or \
                        row["logical_envelope_anchor_containment"] is not None:
                    raise ValueError("sampling must report coverage, not envelope containment")

    # Joint bootstrap diagnostic: structure + bounds (no empirical pass condition).
    jb = result["joint_bootstrap"]
    if jb["n_bootstrap"] != result["n_joint_bootstrap"]:
        raise ValueError("joint bootstrap resample count drift")
    if jb["scope"].startswith("SUPPLEMENTARY_JOINT_DIAGNOSTIC") is False:
        raise ValueError("joint bootstrap must be labeled supplementary diagnostic")
    for partition, conventions in jb["composite_intervals"].items():
        for convention, iv in conventions.items():
            if iv is None:
                continue
            lo, hi = iv["percentile_95"]
            if not 0.0 <= lo <= hi <= 1.0:
                raise ValueError("joint composite interval out of bounds")
    for key, iv in jb["channel_intervals"].items():
        if iv is None:
            continue
        lo, hi = iv["percentile_95"]
        if not 0.0 <= lo <= hi <= 1.0:
            raise ValueError(f"joint channel interval {key} out of bounds")

    # Exact anchor certificate: POINT, analytic composites, confirmed sensitivity.
    exact_cert = result["baseline_certificate_exact"]
    if validate_r21_certificate(exact_cert):
        raise ValueError("exact baseline R21 certificate invalid")
    if exact_cert["certificate_mode"] != "POINT":
        raise ValueError("exact anchor certificate must be POINT")
    exact_reports = exact_cert["attribution_sensitivity"]["convention_reports"]
    independent = _independent_exact_composites(exact)
    for partition, conventions in independent.items():
        for convention, value in conventions.items():
            got = exact_reports[partition][convention]["composite_interval"]["bounds"][0]
            if abs(got - value) > 1e-9:
                raise ValueError("exact convention composite fails independent anchor")
    exact_range = exact_cert["attribution_sensitivity"]["overall_composite_range"]
    if abs(exact_range[0] - 0.0003908) > 1e-6 or abs(exact_range[1] - 0.4608565) > 1e-6:
        raise ValueError("exact composite range fails the registered-convention anchor")
    if exact_cert["sensitivity_flags"] != ["ORDER_SENSITIVE", "MODEL_SENSITIVE"]:
        raise ValueError("exact instance has confirmed order and semantic sensitivity")
    if exact_cert["sensitivity_status"]["order"]["status"] != "CONFIRMED_SENSITIVE":
        raise ValueError("exact order sensitivity must be CONFIRMED")
    if abs(exact_cert["sensitivity_status"]["order"]["min_possible_spread"] - 0.4604657) > 1e-6:
        raise ValueError("exact order separation anchor failed")
    nri_oracle = exact_reports["registered"]["NRI"]["oracle_detection"]
    if not nri_oracle["oracle_below_limit"] or \
            nri_oracle["label"] != "ORACLE_ASSISTED_VALIDATION_FIXTURE_ONLY_NOT_DEPLOYABLE":
        raise ValueError("exact NRI detection must be oracle-labeled fixture classification")
    reg = exact_reports["registered"]
    alt = exact_reports[ALTERNATIVE_PARTITION_NAME]
    diffs = {c: abs(reg[c]["composite_interval"]["bounds"][0]
                    - alt[c]["composite_interval"]["bounds"][0])
             for c in ("RNI", "NRI", "order_average")}
    if diffs["RNI"] > 1e-9 or abs(diffs["NRI"] - 0.4604657) > 1e-6 \
            or abs(diffs["order_average"] - 0.0596576) > 1e-6:
        raise ValueError("semantic decomposition anchor failed")

    # Sampled negative controls (control precision bounds).
    surgery_sampled = result["surgery_arm_sampled"]
    if surgery_sampled["reflection"]["Lambda"] != 0.0:
        raise ValueError("sampled surgery Lambda must be exactly zero")
    surgery_cert = result["surgery_certificate_sampled"]
    if validate_r21_certificate(surgery_cert):
        raise ValueError("sampled surgery certificate invalid")
    for partition in surgery_cert["attribution_sensitivity"]["convention_reports"].values():
        for rep in partition.values():
            if rep["composite_interval"]["bounds"] != [0.0, 0.0]:
                raise ValueError("surgery annihilation must give [0,0] composite intervals")
    if surgery_cert["historical_formation_profile"]["formation_status"] != "REGISTERED_SURGERY":
        raise ValueError("sampled surgery formation status anchor failed")
    if result["surgery_certificate_exact"]["state_autonomy"] != 0.0:
        raise ValueError("exact surgery composite must be zero")
    decoupled_sampled = result["action_decoupled_negative_control_sampled"]
    if decoupled_sampled["channels"]["a_exec_open_loop"] > 1e-3:
        raise ValueError("sampled decoupled execution must be zero within sampling precision")
    decoupled_cert = result["decoupled_certificate_sampled"]
    if validate_r21_certificate(decoupled_cert):
        raise ValueError("sampled decoupled certificate invalid")
    if decoupled_cert["channel_profile"]["a_exec"]["value"] > 1e-3:
        raise ValueError("sampled decoupled execution anchor failed")
    if decoupled_sampled["execution_open_loop"]["score"]["input_distribution_over_allowed"] != [0.25] * 4:
        raise ValueError("near-zero canonical branch must return exact uniform")
    if result["scope"]["external_construct_validation"]:
        raise ValueError("joint audit must not claim external validation")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-samples", type=int, default=8192)
    parser.add_argument("--seed", type=int, default=20261122)
    parser.add_argument("--n-bootstrap", type=int, default=100)
    parser.add_argument("--n-joint-bootstrap", type=int, default=200)
    parser.add_argument("--out", default=str(HERE / "analysis_r21_joint_audit.json"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = compute(n_samples=args.n_samples, seed=args.seed, n_bootstrap=args.n_bootstrap,
                     n_joint_bootstrap=args.n_joint_bootstrap)
    validate_result(result)
    if args.check:
        saved = json.loads(Path(args.out).read_text(encoding="utf-8"))
        comparison = compare_replay_json(saved, result,
                                         field_tolerances=REPLAY_FIELD_TOLERANCES)
        if not comparison["passed"]:
            raise SystemExit("R21 joint audit check FAILED: "
                             + "; ".join(comparison["differences"][:8]))
        print("R21 joint audit check OK: exact anchors, immutable-input evidence binding, "
              "data-driven in-certificate detection, share-conditional conditioning "
              "disclosure, separated coverage semantics, joint-bootstrap diagnostic, "
              "three-state sensitivity, sampled negative controls; "
              f"max abs float diff={comparison['max_abs_float_difference']:.3e}")
        return 0
    Path(args.out).write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                              encoding="utf-8")
    print("R21 native joint-log audit PASS (internal concept validation, not external)")
    print("[out]", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())