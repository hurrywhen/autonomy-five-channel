#!/usr/bin/env python3
"""R17-native multi-step end-to-end benchmark artifact (internal only)."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "src"))

from autonomy_sim.native_benchmark import NativeConfig, exact_bundle, run_benchmark  # noqa: E402
from autonomy_sim.formation_audit import fixed_point_replacement_witness  # noqa: E402
from autonomy_sim.r17_guards import produce_r17_certificate, validate_r17_certificate  # noqa: E402
from analysis_r15_x5c_paired import compare_replay_json  # noqa: E402


def _binary_entropy(p: float) -> float:
    if p <= 0 or p >= 1:
        return 0.0
    return -p * math.log(p) - (1 - p) * math.log(1 - p)


def _certificate(bundle: dict) -> dict:
    config = bundle["config"]
    channels = bundle["channels"]
    model_bytes = json.dumps(config, sort_keys=True).encode("utf-8")
    evidence_bytes = json.dumps(bundle, sort_keys=True).encode("utf-8")
    cert = produce_r17_certificate(
        layer="L2",
        channels=(channels["a_org_RNI"], channels["a_goal_structural"],
                  channels["a_exec_open_loop"], channels["a_epi"], channels["a_ref"]),
        weights=config["weights"],
        resource_ratios=config["resource_ratios"],
        defense_margins=config["defense_margins"],
        surgery_history=config["surgery"],
        lambda_value=bundle["reflection"]["Lambda"],
        lambda_status="DEFINED",
        source_registration="COMPLETE",
        mechanism_evidence="NONE",
        org_mode="L1_NORMATIVE_NR",
        goal_mode="STRUCTURAL_POINT",
        state_readiness_version="R15_SPLIT",
        model_hash=hashlib.sha256(model_bytes).hexdigest(),
        evidence_hash=hashlib.sha256(evidence_bytes).hexdigest(),
        lambda_time_origin="AUDIT_CURRENT_REMOVAL",
        lambda_counterfactual_scope="REMOVE_REGISTERED_SURGERIES_AT_AUDIT",
    )
    errors = validate_r17_certificate(cert)
    if errors:
        raise ValueError("native certificate invalid: " + "; ".join(errors))
    return cert


def compute(*, n_samples: int = 4096, seed: int = 20261119) -> dict:
    result = run_benchmark(n_samples=n_samples, seed=seed)
    result["fixed_point_implant_witness"] = fixed_point_replacement_witness()
    result["baseline_certificate"] = _certificate(result["baseline"])
    result["surgery_certificate"] = _certificate(result["surgery_arm"])
    result["sampling"]["bias_note"] = (
        "Plug-in directed-information estimates have finite-sample bias; bootstrap "
        "intervals describe sampling variability of the plug-in estimator and need "
        "not cover the exact truth. The internal 0.01 threshold is not a domain SESOI."
    )
    return result


def validate_result(result: dict) -> None:
    baseline = result["baseline"]
    config = baseline["config"]
    p = config["p_obs"]
    q = config["q_self"]
    expected_exec = ((math.log(2.0) - _binary_entropy(p)) / (2 * math.log(2.0))
                     if config["action_effect"] else 0.0)
    expected_fidelity = 1.0 - _binary_entropy(q) / math.log(2.0)
    checks = [
        ("a_epi", baseline["channels"]["a_epi"], 1 - p),
        ("a_goal", baseline["channels"]["a_goal_structural"], 0.5),
        ("a_exec", baseline["channels"]["a_exec_open_loop"], expected_exec),
        ("fidelity", baseline["reflection"]["fidelity"], expected_fidelity),
        ("Lambda", baseline["reflection"]["Lambda"], 1.0),
    ]
    for name, actual, expected in checks:
        if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError(f"native anchor failed: {name}")
    if result["surgery_arm"]["reflection"]["Lambda"] != 0.0:
        raise ValueError("surgery Lambda anchor failed")
    if result["action_decoupled_negative_control"]["execution_open_loop"]["state_averaged_a_exec"] != 0.0:
        raise ValueError("decoupled open-loop zero anchor failed")
    registered = baseline["source"]["registered_partition"]
    alternative = baseline["source"]["alternative_partition_R_as_normative_memory"]
    if math.isclose(registered["normative_share_order_average"],
                    alternative["normative_share_order_average"], abs_tol=1e-9):
        raise ValueError("semantic-partition sensitivity anchor failed")
    if validate_r17_certificate(result["baseline_certificate"]):
        raise ValueError("baseline certificate invalid")
    if result["surgery_certificate"]["historical_formation_profile"]["formation_status"] != "REGISTERED_SURGERY":
        raise ValueError("surgery formation status anchor failed")
    for value in result["sampling"]["source_share_abs_errors"].values():
        if not math.isfinite(value):
            raise ValueError("non-finite sampling error")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-samples", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=20261119)
    parser.add_argument("--out", default=str(HERE / "analysis_r17_native_benchmark.json"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = compute(n_samples=args.n_samples, seed=args.seed)
    validate_result(result)
    if args.check:
        saved = json.loads(Path(args.out).read_text(encoding="utf-8"))
        comparison = compare_replay_json(saved, result)
        if not comparison["passed"]:
            raise SystemExit("R17 native benchmark check FAILED: "
                             + "; ".join(comparison["differences"][:8]))
        print("R17 native benchmark check OK: exact anchors, certificates, sampling, "
              f"semantic sensitivity; max abs float diff={comparison['max_abs_float_difference']:.3e}")
        return 0
    Path(args.out).write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                              encoding="utf-8")
    print("R17 native benchmark PASS (internal concept validation, not external)")
    print("[out]", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
