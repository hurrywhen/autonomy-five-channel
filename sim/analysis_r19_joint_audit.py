#!/usr/bin/env python3
"""R19 native joint-log audit artifact (internal only).

Supersedes the R18 joint-audit artifact, which is retained read-only together
with its recorded cross-environment replay failure.  R19 adds: canonicalized
optimizer coordinates, immutable-input-only evidence binding, the corrected
state_autonomy_RNI field, sampled surgery/decoupled negative controls,
bias-corrected shares, per-convention composite uncertainty, and near-zero
detection-limit reporting.  Replay uses declared per-field tolerances for
auxiliary numerical outputs; raw hashes/counts/statuses remain byte-exact.
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
from autonomy_sim.native_benchmark import NativeConfig  # noqa: E402
from autonomy_sim.native_joint_audit import ALTERNATIVE_PARTITION_NAME  # noqa: E402
from autonomy_sim.r19_joint_audit import (NRI_SHARE_DETECTION_LIMIT,  # noqa: E402
                                          run_joint_audit_r19)
from autonomy_sim.formation_audit import fixed_point_replacement_witness  # noqa: E402
from autonomy_sim.open_loop_execution import sequence_channel_mi_nats  # noqa: E402
from autonomy_sim.r19_guards import (ORDER_SENSITIVITY_THRESHOLD,  # noqa: E402
                                     SEMANTIC_SENSITIVITY_THRESHOLD,
                                     THRESHOLD_PROVENANCE,
                                     produce_r19_certificate, validate_r19_certificate)
from analysis_r15_x5c_paired import compare_replay_json  # noqa: E402

# Declared per-field replay tolerances for AUXILIARY numerical analysis
# outputs (non-unique/ill-conditioned optimizer coordinates and derived
# capacity values).  Immutable raw-log hashes, event counts, seeds, and
# statuses are not float leaves and remain byte-exact.
REPLAY_FIELD_TOLERANCES = {
    "input_distribution_over_allowed": 1e-6,
    "empowerment_nats": 1e-9,
    "capacity_certificate_nats": 1e-9,
    "a_exec": 1e-9,
}


def _binary_entropy(p: float) -> float:
    if p <= 0 or p >= 1:
        return 0.0
    return -p * math.log(p) - (1 - p) * math.log(1 - p)


def _sha(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _hull(interval, point):
    if interval is None:
        return None
    return [min(interval[0], point), max(interval[1], point)]


def _channel_profile(*, channels: dict, reflection: dict, goal: dict,
                     org_interval=None, epi_interval=None,
                     ref_protocol: str = "FIDELITY_CONSISTENCY_LAMBDA_R19") -> dict:
    a_ref = reflection["A_ref"]
    if a_ref is None:
        ref_entry = {"value": None, "state": "INTERVAL",
                     "interval": list(reflection["A_ref_interval"]),
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
    org_state = "DEFINED" if channels["a_org_RNI"] is not None else "INTERVAL"
    return {
        "a_org": {"value": channels["a_org_RNI"],
                  "state": org_state,
                  "interval": ([0.0, 1.0] if org_state == "INTERVAL" else org_interval),
                  "protocol_version": "RNI_ORDERED_RESIDUAL_SHARE_R19"},
        "a_goal": {"value": channels["a_goal_structural"], "state": "DEFINED",
                   "interval": None,
                   "protocol_version": "STRUCTURAL_POINT_AND_IRL_INTERVAL_R19",
                   "structural_point": channels["a_goal_structural"],
                   "irl_interval": list(goal["behavior_IRL_identified_interval"])},
        "a_exec": {"value": channels["a_exec_open_loop"], "state": "DEFINED",
                   "interval": None,
                   "protocol_version": "PRECOMMITTED_OPEN_LOOP_CANONICAL_R19",
                   "horizon_actions": 2, "uses_intermediate_observations": False},
        "a_epi": {"value": channels["a_epi"], "state": "DEFINED",
                  "interval": epi_interval,
                  "protocol_version": "LOGGED_BELIEF_ACCURACY_R19"},
        "a_ref": ref_entry,
    }


def _attribution(source: dict, weights: list[float], *, mode: str) -> dict:
    registered = json.loads(json.dumps(source["registered_partition"]))
    alternative = json.loads(json.dumps(
        source[f"alternative_partition_{ALTERNATIVE_PARTITION_NAME}"]))
    if mode == "INTERVAL":
        for report in (registered, alternative):
            total = float(report["joint_di_bits"])
            report["share_intervals"] = {
                convention: (None if total <= 1e-9 else [report[key], report[key]])
                for convention, key in (
                    ("RNI", "normative_share_RNI"),
                    ("NRI", "normative_share_NRI"),
                    ("order_average", "normative_share_order_average"))}
    return {"registered_partition": registered,
            "alternative_partitions": {ALTERNATIVE_PARTITION_NAME: alternative},
            "weights": list(weights), "sigma": 1.0}


def _certificate(*, channels: dict, reflection: dict, goal: dict, config: dict,
                 viability: float, defense: float, surgery: int,
                 source: dict, evidence_payload,
                 org_interval=None, epi_interval=None,
                 ref_protocol: str = "FIDELITY_CONSISTENCY_LAMBDA_R19") -> dict:
    mode = "POINT" if reflection["A_ref"] is not None else "INTERVAL"
    profile = _channel_profile(channels=channels, reflection=reflection, goal=goal,
                               org_interval=org_interval, epi_interval=epi_interval,
                               ref_protocol=ref_protocol)
    cert = produce_r19_certificate(
        layer="L2", channel_profile=profile,
        attribution=_attribution(source, config["weights"], mode=mode),
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
    errors = validate_r19_certificate(cert)
    if errors:
        raise ValueError("R19 native certificate invalid: " + "; ".join(errors))
    return cert


def _exact_evidence_payload(bundle: dict) -> dict:
    """Deterministic subset of the exact bundle: NO optimizer coordinates."""
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
        source=bundle["source"], evidence_payload=_exact_evidence_payload(bundle),
        ref_protocol="FIDELITY_CONSISTENCY_LAMBDA_R19_EXACT_ENUMERATION")


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
        for convention, key in (("RNI", "normative_share_RNI"),
                                ("NRI", "normative_share_NRI"),
                                ("order_average", "normative_share_order_average")):
            out[name][convention] = float(composite_A(
                viability, (report[key],) + rest, weights, sigma=1.0))
    return out


def _convention_table(result: dict) -> dict:
    exact = result["exact_truth"]
    sampled = result["sampled"]
    independent = _independent_exact_composites(exact)
    table = {}
    for partition in ("registered", ALTERNATIVE_PARTITION_NAME):
        table[partition] = {}
        uncertainty = sampled["composite_uncertainty"][partition]
        for convention in ("RNI", "NRI", "order_average"):
            exact_value = independent[partition][convention]
            row = uncertainty[convention]
            plugin = row["plugin_composite"]
            corrected = row["bias_corrected_composite"]
            interval = row["composite_bootstrap_95"]
            table[partition][convention] = {
                "exact_composite": exact_value,
                "sampled_plugin_composite": plugin,
                "abs_error_plugin": abs(plugin - exact_value),
                "sampled_bias_corrected_composite": corrected,
                "abs_error_bias_corrected": abs(corrected - exact_value),
                "composite_bootstrap_95": interval,
                "covers_exact_plugin": bool(interval[0] <= exact_value <= interval[1]),
                "bias_corrected_closer_to_exact": bool(
                    abs(corrected - exact_value) < abs(plugin - exact_value)),
            }
    return table


def _near_zero_detection(result: dict) -> dict:
    exact = result["exact_truth"]["source"]["registered_partition"]
    sampled = result["sampled"]
    registered = sampled["source"]["registered_partition"]
    channels = sampled["channels"]
    rest = (channels["a_goal_structural"], channels["a_exec_open_loop"],
            channels["a_epi"], channels["a_ref"])
    weights = result["config"]["weights"]
    viability = sampled["viability_state"]
    report = {}
    for convention, key in (("RNI", "normative_share_RNI"),
                            ("NRI", "normative_share_NRI"),
                            ("order_average", "normative_share_order_average")):
        exact_share = exact[key]
        below = exact_share is not None and exact_share < NRI_SHARE_DETECTION_LIMIT
        boot_hi = sampled["source_bootstrap_intervals"][key]["percentile_95"][1]
        upper = float(composite_A(viability, (boot_hi,) + rest, weights, sigma=1.0))
        report[convention] = {
            "exact_share": exact_share,
            "below_detection_limit": bool(below),
            "detection_limit": NRI_SHARE_DETECTION_LIMIT,
            "sampled_plugin_share": registered[key],
            "sampled_plugin_composite":
                sampled["composite_uncertainty"]["registered"][convention]["plugin_composite"],
            "reported_semantics": ("INTERVAL_BELOW_DETECTION_LIMIT" if below
                                   else "POINT_WITH_SENSITIVITY_QUALIFICATION"),
            "reported_composite_interval": [0.0, upper] if below else None,
        }
    return report


def compute(*, n_samples: int = 8192, seed: int = 20261122,
            n_bootstrap: int = 100) -> dict:
    result = run_joint_audit_r19(n_samples=n_samples, seed=seed, n_bootstrap=n_bootstrap)
    sampled = result["sampled"]
    config = result["config"]
    reflection = sampled["reflection"]
    evidence_payload = result["evidence_binding"]["payload"]
    org_interval = None
    if sampled["source_bootstrap_intervals"]["normative_share_RNI"] is not None:
        org_interval = _hull(
            sampled["source_bootstrap_intervals"]["normative_share_RNI"]["percentile_95"],
            sampled["channels"]["a_org_RNI"])
    result["baseline_certificate"] = _certificate(
        channels=sampled["channels"], reflection=reflection, goal=sampled["goal"],
        config=config, viability=sampled["viability_state"],
        defense=sampled["defense_readiness"], surgery=0,
        source=sampled["source"], evidence_payload=evidence_payload,
        org_interval=org_interval, epi_interval=sampled["epistemic"]["normal_95"])
    result["baseline_certificate_exact"] = _exact_certificate(result["exact_truth"])
    result["surgery_certificate_exact"] = _exact_certificate(result["surgery_arm_exact"])
    result["decoupled_certificate_exact"] = _exact_certificate(
        result["action_decoupled_negative_control_exact"])
    surgery_sampled = result["surgery_arm_sampled"]
    result["surgery_certificate_sampled"] = _certificate(
        channels=surgery_sampled["channels"], reflection=surgery_sampled["reflection"],
        goal=surgery_sampled["goal"],
        config=dict(config, surgery=1), viability=surgery_sampled["viability_state"],
        defense=surgery_sampled["defense_readiness"], surgery=1,
        source=surgery_sampled["source"],
        evidence_payload={"log_hashes": {
            "surgery_operating_log_sha256": result["logs"]["surgery_operating_log_sha256"],
            "surgery_execution_log_sha256": result["logs"]["surgery_execution_log_sha256"]},
            "config": dict(config, surgery=1), "seed": seed,
            "n_samples_per_stream": n_samples})
    decoupled_sampled = result["action_decoupled_negative_control_sampled"]
    result["decoupled_certificate_sampled"] = _certificate(
        channels=decoupled_sampled["channels"],
        reflection=decoupled_sampled["reflection"], goal=decoupled_sampled["goal"],
        config=dict(config, action_effect=False),
        viability=decoupled_sampled["viability_state"],
        defense=decoupled_sampled["defense_readiness"], surgery=0,
        source=decoupled_sampled["source"],
        evidence_payload={"log_hashes": {
            "decoupled_operating_log_sha256": result["logs"]["decoupled_operating_log_sha256"],
            "decoupled_execution_log_sha256": result["logs"]["decoupled_execution_log_sha256"]},
            "config": dict(config, action_effect=False), "seed": seed,
            "n_samples_per_stream": n_samples})
    result["fixed_point_implant_witness"] = fixed_point_replacement_witness()
    result["convention_composite_table"] = _convention_table(result)
    result["near_zero_detection"] = _near_zero_detection(result)
    result["sensitivity_thresholds"] = {
        "order_composite_spread": ORDER_SENSITIVITY_THRESHOLD,
        "semantic_partition_spread": SEMANTIC_SENSITIVITY_THRESHOLD,
        "provenance": THRESHOLD_PROVENANCE,
        "note": ("Post hoc frozen internal engineering thresholds on the composite "
                 "scale, frozen after the R17-native results were observed; not a "
                 "domain SESOI, not a power calculation, not external validation. "
                 "Preregistration language applies only to future audits frozen "
                 "before their outcomes are seen."),
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
    result["bias_note"] = (
        "Plug-in directed-information estimates have finite-sample bias; the "
        "geometric composite amplifies near-zero share differences (x^0.2), so the "
        "sampled NRI-convention composite deviates from its exact near-zero value by "
        "more than the internal sensitivity threshold. Exact-truth composites are "
        "model anchors, NOT evidence of finite-sample recoverability; below-limit "
        "conventions are reported with interval semantics. Bootstrap percentile "
        "intervals describe plug-in sampling variability and need not cover the "
        "exact truth; bias-corrected values are reported separately.")
    return result


def validate_result(result: dict) -> None:
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
            raise ValueError(f"R19 exact anchor failed: {name}")
    if result["surgery_arm_exact"]["reflection"]["Lambda"] != 0.0:
        raise ValueError("surgery Lambda anchor failed")
    if result["action_decoupled_negative_control_exact"]["execution_open_loop"]["state_averaged_a_exec"] != 0.0:
        raise ValueError("decoupled open-loop zero anchor failed")

    # Single-batch provenance and event carriers.
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

    # R19 evidence binding: immutable inputs only, recomputed hash agreement.
    binding = result["evidence_binding"]
    if binding["policy"] != "IMMUTABLE_RAW_INPUTS_ONLY_NOT_ANALYSIS_OUTPUTS":
        raise ValueError("evidence binding policy drift")
    if _sha(binding["payload"]) != binding["evidence_sha256"]:
        raise ValueError("evidence binding hash mismatch")
    payload = binding["payload"]
    if set(payload) != {"log_hashes", "config", "seed", "n_samples_per_stream",
                        "n_bootstrap", "log_schema"}:
        raise ValueError("evidence payload must contain immutable registered inputs only")
    for digest in payload["log_hashes"].values():
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError("evidence log hashes must be SHA-256 digests")
    cert = result["baseline_certificate"]
    if cert["evidence_hash"] != binding["evidence_sha256"]:
        raise ValueError("baseline certificate must bind the immutable-input hash")

    # R19 FIX regression: returned field equals the registered RNI composite.
    sampled = result["sampled"]
    if abs(sampled["state_autonomy_RNI"] - cert["state_autonomy"]) > 1e-12:
        raise ValueError("state_autonomy_RNI must equal the registered RNI certificate composite")
    if abs(sampled["state_autonomy_RNI"] - sampled["viability_state"]) < 1e-9:
        raise ValueError("state_autonomy_RNI must not collapse to the resource gate")

    # Canonicalized execution coordinates (declared rule, verified precision).
    score = sampled["execution_open_loop"]["score"]
    canonicalization = score["input_canonicalization"]
    if canonicalization is None:
        raise ValueError("canonicalization metadata missing")
    q_canon = score["input_distribution_over_allowed"]
    if abs(sum(q_canon) - 1.0) > 1e-12 or any(v < 0 for v in q_canon):
        raise ValueError("canonical input must be a distribution")
    achieved = sequence_channel_mi_nats(
        q_canon, sampled["execution_open_loop"]["sequence_kernels"])
    if achieved < canonicalization["capacity_certificate_nats"] - 1e-6:
        raise ValueError("canonical input must achieve capacity within declared precision")

    # Sampling agreement on shares/channels (internal bound, not SESOI).
    errors = result["sampling_errors"]
    for group in ("source_registered", "source_alternative"):
        for value in errors[group].values():
            if not math.isfinite(value) or value > 0.05:
                raise ValueError(f"R19 sampling error out of internal bound: {group}")
    for key in ("epistemic_abs", "fidelity_abs", "Lambda_abs", "execution_abs"):
        if not math.isfinite(errors[key]) or errors[key] > 0.05:
            raise ValueError(f"R19 sampling error out of internal bound: {key}")

    # Certificate governance.
    if validate_r19_certificate(cert):
        raise ValueError("baseline R19 certificate invalid")
    if cert["sensitivity_flags"] != ["ORDER_SENSITIVE", "MODEL_SENSITIVE"]:
        raise ValueError("baseline must carry both decomposed sensitivity flags")
    if not cert["scalar_export_warning"].strip():
        raise ValueError("flagged certificate lacks scalar-export warning")
    sensitivity = cert["attribution_sensitivity"]
    # Sampled spreads reflect plug-in bias (the NRI endpoint is not recovered);
    # only flag firing is anchored here.  Exact spreads are anchored below.
    if sensitivity["order_spread"] <= ORDER_SENSITIVITY_THRESHOLD:
        raise ValueError("sampled order spread must fire ORDER_SENSITIVE")
    if sensitivity["semantic_partition_spread"] <= SEMANTIC_SENSITIVITY_THRESHOLD:
        raise ValueError("sampled semantic spread must fire MODEL_SENSITIVE")
    exact_cert = result["baseline_certificate_exact"]
    if validate_r19_certificate(exact_cert):
        raise ValueError("exact baseline R19 certificate invalid")
    if exact_cert["sensitivity_flags"] != ["ORDER_SENSITIVE", "MODEL_SENSITIVE"]:
        raise ValueError("exact baseline must carry both sensitivity flags")
    exact_sensitivity = exact_cert["attribution_sensitivity"]
    if abs(exact_sensitivity["order_spread"] - 0.4604657) > 1e-6:
        raise ValueError("exact order spread anchor failed")
    if abs(exact_sensitivity["semantic_partition_spread"] - 0.4604657) > 1e-6:
        raise ValueError("exact semantic partition spread anchor failed")
    # Decomposition anchor: under the alternative partition the RNI convention
    # agrees with the registered RNI (partition difference 0), while NRI and
    # order-average differ -- the model flag has an independent semantic cause.
    exact_comp = exact_sensitivity["composite_by_convention"]
    rni_partition_diff = abs(exact_comp["registered"]["RNI"]
                             - exact_comp[ALTERNATIVE_PARTITION_NAME]["RNI"])
    nri_partition_diff = abs(exact_comp["registered"]["NRI"]
                             - exact_comp[ALTERNATIVE_PARTITION_NAME]["NRI"])
    if rni_partition_diff > 1e-9:
        raise ValueError("RNI partition difference anchor failed")
    if abs(nri_partition_diff - 0.4604657) > 1e-6:
        raise ValueError("NRI partition difference anchor failed")
    exact_composites = exact_cert["attribution_sensitivity"]["composite_by_convention"]
    independent = _independent_exact_composites(exact)
    for partition, conventions in independent.items():
        for convention, value in conventions.items():
            if abs(exact_composites[partition][convention] - value) > 1e-9:
                raise ValueError("exact convention composite fails independent anchor")
    exact_range = exact_cert["attribution_sensitivity"]["overall_composite_range"]
    if abs(exact_range[0] - 0.0003908) > 1e-6 or abs(exact_range[1] - 0.4608565) > 1e-6:
        raise ValueError("exact composite range fails the registered-convention anchor")

    # Near-zero detection semantics.
    detection = result["near_zero_detection"]
    if not detection["NRI"]["below_detection_limit"]:
        raise ValueError("exact NRI share must be below the detection limit")
    if detection["NRI"]["reported_semantics"] != "INTERVAL_BELOW_DETECTION_LIMIT":
        raise ValueError("below-limit NRI must use interval semantics")
    if detection["RNI"]["below_detection_limit"]:
        raise ValueError("RNI share is not below the detection limit")
    table = result["convention_composite_table"]["registered"]["NRI"]
    if table["abs_error_plugin"] <= ORDER_SENSITIVITY_THRESHOLD:
        raise ValueError("the sampled NRI composite error is expected to exceed the threshold")
    if table["covers_exact_plugin"]:
        raise ValueError("plugin bootstrap interval is not expected to cover the near-zero truth")

    # Sampled negative controls.
    surgery_sampled = result["surgery_arm_sampled"]
    if surgery_sampled["reflection"]["Lambda"] != 0.0:
        raise ValueError("sampled surgery Lambda must be exactly zero")
    if surgery_sampled["state_autonomy_RNI"] != 0.0:
        raise ValueError("sampled surgery composite must annihilate")
    surgery_cert = result["surgery_certificate_sampled"]
    if validate_r19_certificate(surgery_cert):
        raise ValueError("sampled surgery certificate invalid")
    if surgery_cert["state_autonomy"] != 0.0:
        raise ValueError("sampled surgery certificate composite must be zero")
    if surgery_cert["historical_formation_profile"]["formation_status"] != "REGISTERED_SURGERY":
        raise ValueError("sampled surgery formation status anchor failed")
    if result["surgery_certificate_exact"]["state_autonomy"] != 0.0:
        raise ValueError("exact surgery composite must be zero")
    decoupled_sampled = result["action_decoupled_negative_control_sampled"]
    # Sampled decoupling is zero WITHIN SAMPLING PRECISION (rows differ by
    # finite-sample noise; normalized capacity <= ~7e-4); the exact arm is
    # exactly zero.
    if decoupled_sampled["channels"]["a_exec_open_loop"] > 1e-3:
        raise ValueError("sampled decoupled execution must be zero within sampling precision")
    decoupled_cert = result["decoupled_certificate_sampled"]
    if validate_r19_certificate(decoupled_cert):
        raise ValueError("sampled decoupled certificate invalid")
    if decoupled_cert["channel_profile"]["a_exec"]["value"] > 1e-3:
        raise ValueError("sampled decoupled execution anchor failed")
    if decoupled_sampled["execution_open_loop"]["score"]["input_distribution_over_allowed"] != [0.25, 0.25, 0.25, 0.25]:
        raise ValueError("near-zero canonical branch must return exact uniform")
    if result["scope"]["external_construct_validation"]:
        raise ValueError("joint audit must not claim external validation")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-samples", type=int, default=8192)
    parser.add_argument("--seed", type=int, default=20261122)
    parser.add_argument("--n-bootstrap", type=int, default=100)
    parser.add_argument("--out", default=str(HERE / "analysis_r19_joint_audit.json"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = compute(n_samples=args.n_samples, seed=args.seed, n_bootstrap=args.n_bootstrap)
    validate_result(result)
    if args.check:
        saved = json.loads(Path(args.out).read_text(encoding="utf-8"))
        comparison = compare_replay_json(saved, result,
                                         field_tolerances=REPLAY_FIELD_TOLERANCES)
        if not comparison["passed"]:
            raise SystemExit("R19 joint audit check FAILED: "
                             + "; ".join(comparison["differences"][:8]))
        print("R19 joint audit check OK: exact anchors, immutable-input evidence binding, "
              "canonical optimizer coordinates, corrected state_autonomy_RNI, sampled "
              "negative controls, detection-limit semantics; "
              f"max abs float diff={comparison['max_abs_float_difference']:.3e}")
        return 0
    Path(args.out).write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                              encoding="utf-8")
    print("R19 native joint-log audit PASS (internal concept validation, not external)")
    print("[out]", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
