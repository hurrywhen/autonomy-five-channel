#!/usr/bin/env python3
"""R18 native joint-log end-to-end audit artifact (internal only).

One SCM, one log schema, one joint operating batch for every operating-side
estimand, plus the separate precommitted open-loop execution stream required
by the execution estimand.  All channels feed one R18 full-profile certificate
with enforced order/semantic sensitivity flags.  The read-only R17-native
artifact is not rewritten.
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

from autonomy_sim.native_benchmark import NativeConfig, exact_bundle  # noqa: E402
from autonomy_sim.native_joint_audit import (ALTERNATIVE_PARTITION_NAME,  # noqa: E402
                                             exact_event_counts, run_joint_audit)
from autonomy_sim.formation_audit import fixed_point_replacement_witness  # noqa: E402
from autonomy_sim.r18_guards import (ORDER_SENSITIVITY_THRESHOLD,  # noqa: E402
                                     MODEL_SENSITIVITY_THRESHOLD,
                                     produce_r18_certificate, validate_r18_certificate)
from analysis_r15_x5c_paired import compare_replay_json  # noqa: E402


def _binary_entropy(p: float) -> float:
    if p <= 0 or p >= 1:
        return 0.0
    return -p * math.log(p) - (1 - p) * math.log(1 - p)


def _sha(payload) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _channel_profile(*, a_org: float, a_goal: float, a_exec: float, a_epi: float,
                     a_ref: float, fidelity: float, consistency: float,
                     lambda_value: float, event_counts: dict,
                     irl_interval: list[float],
                     org_interval=None, epi_interval=None,
                     ref_protocol: str = "FIDELITY_CONSISTENCY_LAMBDA_R18") -> dict:
    return {
        "a_org": {"value": a_org, "state": "DEFINED", "interval": org_interval,
                  "protocol_version": "RNI_ORDERED_RESIDUAL_SHARE_R18"},
        "a_goal": {"value": a_goal, "state": "DEFINED", "interval": None,
                  "protocol_version": "STRUCTURAL_POINT_AND_IRL_INTERVAL_R18",
                  "structural_point": a_goal, "irl_interval": list(irl_interval)},
        "a_exec": {"value": a_exec, "state": "DEFINED", "interval": None,
                   "protocol_version": "PRECOMMITTED_OPEN_LOOP_SEQUENCE_R18",
                   "horizon_actions": 2, "uses_intermediate_observations": False},
        "a_epi": {"value": a_epi, "state": "DEFINED", "interval": epi_interval,
                  "protocol_version": "LOGGED_BELIEF_ACCURACY_R18"},
        "a_ref": {"value": a_ref, "state": "DEFINED", "interval": None,
                  "protocol_version": ref_protocol,
                  "fidelity": fidelity, "endorsement_consistency": consistency,
                  "Lambda": lambda_value, "event_counts": dict(event_counts)},
    }


def _sensitivity_input(source: dict, weights: list[float]) -> dict:
    return {
        "registered_partition": source["registered_partition"],
        "alternative_partitions": {
            ALTERNATIVE_PARTITION_NAME:
                source[f"alternative_partition_{ALTERNATIVE_PARTITION_NAME}"]},
        "weights": list(weights),
        "sigma": 1.0,
    }


def _certificate(*, channels: tuple[float, ...], config: dict,
                 viability: float, defense: float, surgery: int,
                 lambda_value: float, channel_profile: dict,
                 sensitivity: dict, model_payload, evidence_payload) -> dict:
    cert = produce_r18_certificate(
        layer="L2",
        channels=channels,
        weights=config["weights"],
        resource_ratios=[viability],
        defense_margins=[defense],
        surgery_history=surgery,
        lambda_value=lambda_value,
        lambda_status="DEFINED",
        source_registration="COMPLETE",
        mechanism_evidence="NONE",
        org_mode="L1_NORMATIVE_NR",
        goal_mode="STRUCTURAL_POINT",
        state_readiness_version="R15_SPLIT",
        model_hash=_sha(model_payload),
        evidence_hash=_sha(evidence_payload),
        lambda_time_origin="AUDIT_CURRENT_REMOVAL",
        lambda_counterfactual_scope="REMOVE_REGISTERED_SURGERIES_AT_AUDIT",
        channel_profile=channel_profile,
        attribution_sensitivity=sensitivity,
    )
    errors = validate_r18_certificate(cert)
    if errors:
        raise ValueError("R18 native certificate invalid: " + "; ".join(errors))
    return cert


def _exact_certificate(bundle: dict) -> dict:
    config = bundle["config"]
    channels = bundle["channels"]
    reflection = bundle["reflection"]
    profile = _channel_profile(
        a_org=channels["a_org_RNI"], a_goal=channels["a_goal_structural"],
        a_exec=channels["a_exec_open_loop"], a_epi=channels["a_epi"],
        a_ref=channels["a_ref"], fidelity=reflection["fidelity"],
        consistency=reflection["endorsement_consistency"],
        lambda_value=reflection["Lambda"],
        event_counts=exact_event_counts(NativeConfig(surgery=config["surgery"])),
        irl_interval=bundle["goal"]["behavior_IRL_identified_interval"],
        ref_protocol="FIDELITY_CONSISTENCY_LAMBDA_R18_EXACT_ENUMERATION")
    return _certificate(
        channels=(channels["a_org_RNI"], channels["a_goal_structural"],
                  channels["a_exec_open_loop"], channels["a_epi"], channels["a_ref"]),
        config=config, viability=bundle["viability_state"],
        defense=bundle["defense_readiness"], surgery=config["surgery"],
        lambda_value=reflection["Lambda"], channel_profile=profile,
        sensitivity=_sensitivity_input(bundle["source"], config["weights"]),
        model_payload=config, evidence_payload=bundle)


def _independent_exact_composites(exact: dict) -> dict:
    """Independent anchor: recompute convention composites without r18_guards."""
    from autonomy_sim.aggregate import composite_A
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


def compute(*, n_samples: int = 8192, seed: int = 20261121,
            n_bootstrap: int = 100) -> dict:
    result = run_joint_audit(n_samples=n_samples, seed=seed, n_bootstrap=n_bootstrap)
    sampled = result["sampled"]
    config = result["config"]
    channels = sampled["channels"]
    reflection = sampled["reflection"]
    profile = _channel_profile(
        a_org=channels["a_org_RNI"], a_goal=channels["a_goal_structural"],
        a_exec=channels["a_exec_open_loop"], a_epi=channels["a_epi"],
        a_ref=channels["a_ref"], fidelity=reflection["fidelity"],
        consistency=reflection["endorsement_consistency"],
        lambda_value=reflection["Lambda"],
        event_counts=reflection["event_counts"],
        irl_interval=sampled["goal"]["behavior_IRL_identified_interval"],
        org_interval=sampled["source_bootstrap_intervals"]["normative_share_RNI"]["percentile_95"],
        epi_interval=sampled["epistemic"]["normal_95"])
    result["baseline_certificate"] = _certificate(
        channels=(channels["a_org_RNI"], channels["a_goal_structural"],
                  channels["a_exec_open_loop"], channels["a_epi"], channels["a_ref"]),
        config=config, viability=sampled["viability_state"],
        defense=sampled["defense_readiness"], surgery=0,
        lambda_value=reflection["Lambda"], channel_profile=profile,
        sensitivity=_sensitivity_input(sampled["source"], config["weights"]),
        model_payload=config,
        evidence_payload={"operating_log_sha256": result["logs"]["operating_log_sha256"],
                          "execution_log_sha256": result["logs"]["execution_log_sha256"],
                          "sampled": sampled})
    result["baseline_certificate_exact"] = _exact_certificate(result["exact_truth"])
    result["surgery_certificate"] = _exact_certificate(result["surgery_arm_exact"])
    result["decoupled_certificate"] = _exact_certificate(
        result["action_decoupled_negative_control_exact"])
    result["fixed_point_implant_witness"] = fixed_point_replacement_witness()
    result["sensitivity_thresholds"] = {
        "order_composite_spread": ORDER_SENSITIVITY_THRESHOLD,
        "model_composite_spread": MODEL_SENSITIVITY_THRESHOLD,
        "note": ("Preregistered internal engineering thresholds on the composite scale; "
                 "not a domain SESOI, not a power calculation, not external validation."),
    }
    result["bias_note"] = (
        "Plug-in directed-information estimates have finite-sample bias; trajectory-level "
        "bootstrap intervals describe sampling variability of the plug-in estimator and "
        "need not cover the exact truth. The geometric composite amplifies near-zero "
        "share differences, so the sampled NRI-convention composite can deviate "
        "substantially from its exact near-zero value; the exact-truth certificate "
        "pins the registered-convention endpoints. Internal thresholds are not a domain SESOI.")
    return result


def validate_result(result: dict) -> None:
    exact = result["exact_truth"]
    config = result["config"]
    p, q = config["p_obs"], config["q_self"]
    expected_exec = ((math.log(2.0) - _binary_entropy(p)) / (2 * math.log(2.0))
                     if config["action_effect"] else 0.0)
    expected_fidelity = 1.0 - _binary_entropy(q) / math.log(2.0)
    checks = [
        ("a_epi", exact["channels"]["a_epi"], 1 - p),
        ("a_goal", exact["channels"]["a_goal_structural"], 0.5),
        ("a_exec", exact["channels"]["a_exec_open_loop"], expected_exec),
        ("fidelity", exact["reflection"]["fidelity"], expected_fidelity),
        ("Lambda", exact["reflection"]["Lambda"], 1.0),
    ]
    for name, actual, expected in checks:
        if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError(f"R18 exact anchor failed: {name}")
    if result["surgery_arm_exact"]["reflection"]["Lambda"] != 0.0:
        raise ValueError("surgery Lambda anchor failed")
    if result["action_decoupled_negative_control_exact"]["execution_open_loop"]["state_averaged_a_exec"] != 0.0:
        raise ValueError("decoupled open-loop zero anchor failed")
    registered = exact["source"]["registered_partition"]
    alternative = exact["source"][f"alternative_partition_{ALTERNATIVE_PARTITION_NAME}"]
    if math.isclose(registered["normative_share_order_average"],
                    alternative["normative_share_order_average"], abs_tol=1e-9):
        raise ValueError("semantic-partition sensitivity anchor failed")

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
    for key in ("operating_log_sha256", "execution_log_sha256"):
        digest = result["logs"][key]
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError(f"missing log provenance hash {key}")
    if result["logs"]["execution_excerpt"]["uses_intermediate_observations"]:
        raise ValueError("execution stream must not read intermediate observations")

    # Sampling agreement on this registered instance (internal bound, not SESOI).
    errors = result["sampling_errors"]
    for group in ("source_registered", "source_alternative"):
        for value in errors[group].values():
            if not math.isfinite(value) or value > 0.05:
                raise ValueError(f"R18 sampling error out of internal bound: {group}")
    for key in ("epistemic_abs", "fidelity_abs", "Lambda_abs", "execution_abs"):
        if not math.isfinite(errors[key]) or errors[key] > 0.05:
            raise ValueError(f"R18 sampling error out of internal bound: {key}")

    # Certificate governance: full profile, enforced flags, composite range.
    cert = result["baseline_certificate"]
    if validate_r18_certificate(cert):
        raise ValueError("baseline R18 certificate invalid")
    if cert["sensitivity_flags"] != ["ORDER_SENSITIVE", "MODEL_SENSITIVE"]:
        raise ValueError("baseline must be flagged ORDER_SENSITIVE and MODEL_SENSITIVE")
    if not cert["scalar_export_warning"].strip():
        raise ValueError("flagged certificate lacks scalar-export warning")
    if abs(cert["state_autonomy"]
           - cert["attribution_sensitivity"]["composite_by_convention"]["registered"]["RNI"]) > 1e-9:
        raise ValueError("exported scalar is not the registered RNI convention")
    sampled_range = cert["attribution_sensitivity"]["composite_range"]
    if not 0.0 <= sampled_range[0] < sampled_range[1] <= 1.0:
        raise ValueError("sampled composite range malformed")
    if abs(sampled_range[1] - 0.4608565) > 0.01:
        raise ValueError("sampled upper composite endpoint drifts from exact truth")
    # The exact-truth certificate pins the paper's convention endpoints.
    exact_cert = result["baseline_certificate_exact"]
    if validate_r18_certificate(exact_cert):
        raise ValueError("exact baseline R18 certificate invalid")
    if exact_cert["sensitivity_flags"] != ["ORDER_SENSITIVE", "MODEL_SENSITIVE"]:
        raise ValueError("exact baseline must carry both sensitivity flags")
    exact_composites = exact_cert["attribution_sensitivity"]["composite_by_convention"]
    independent = _independent_exact_composites(result["exact_truth"])
    for partition, conventions in independent.items():
        for convention, value in conventions.items():
            if abs(exact_composites[partition][convention] - value) > 1e-9:
                raise ValueError("exact convention composite fails independent anchor")
    exact_range = exact_cert["attribution_sensitivity"]["composite_range"]
    if abs(exact_range[0] - 0.0003908) > 1e-6 or abs(exact_range[1] - 0.4608565) > 1e-6:
        raise ValueError("exact composite range fails the registered-convention anchor")
    surgery_cert = result["surgery_certificate"]
    if validate_r18_certificate(surgery_cert):
        raise ValueError("surgery R18 certificate invalid")
    if surgery_cert["state_autonomy"] != 0.0:
        raise ValueError("surgery arm must annihilate the composite via Lambda=0")
    if surgery_cert["historical_formation_profile"]["formation_status"] != "REGISTERED_SURGERY":
        raise ValueError("surgery formation status anchor failed")
    if surgery_cert["sensitivity_flags"] != []:
        raise ValueError("zero composite has no convention spread to flag")
    decoupled = result["decoupled_certificate"]
    if validate_r18_certificate(decoupled):
        raise ValueError("decoupled R18 certificate invalid")
    if decoupled["channel_profile"]["a_exec"]["value"] != 0.0:
        raise ValueError("decoupled execution anchor failed")
    if result["scope"]["external_construct_validation"]:
        raise ValueError("joint audit must not claim external validation")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-samples", type=int, default=8192)
    parser.add_argument("--seed", type=int, default=20261121)
    parser.add_argument("--n-bootstrap", type=int, default=100)
    parser.add_argument("--out", default=str(HERE / "analysis_r18_native_joint_audit.json"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = compute(n_samples=args.n_samples, seed=args.seed, n_bootstrap=args.n_bootstrap)
    validate_result(result)
    if args.check:
        saved = json.loads(Path(args.out).read_text(encoding="utf-8"))
        comparison = compare_replay_json(saved, result)
        if not comparison["passed"]:
            raise SystemExit("R18 joint audit check FAILED: "
                             + "; ".join(comparison["differences"][:8]))
        print("R18 joint audit check OK: exact anchors, single-batch provenance, "
              "full-profile certificates, enforced sensitivity flags; "
              f"max abs float diff={comparison['max_abs_float_difference']:.3e}")
        return 0
    Path(args.out).write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                              encoding="utf-8")
    print("R18 native joint-log audit PASS (internal concept validation, not external)")
    print("[out]", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())