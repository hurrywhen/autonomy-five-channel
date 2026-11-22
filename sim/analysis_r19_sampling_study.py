#!/usr/bin/env python3
"""R19 multi-seed sampling study: bias, coverage, and interval width (internal).

The R18 review required more than a single batch: near-zero channel estimation
error propagates through the geometric composite (x^0.2 amplification), so the
exact-truth convention endpoints must not be mistaken for finite-sample
recoverability.  This study runs the SAME registered instance under multiple
independent seeds and reports, per attribution convention:

* plug-in and bootstrap-bias-corrected composite bias / RMSE vs exact truth;
* trajectory-block bootstrap 95% interval coverage of the exact composite and
  mean interval width;
* the near-zero NRI detection-limit classification (post hoc frozen internal
  reporting constant, not a domain SESOI).

It is an internal finite-sample study on one small registered SCM, not a power
analysis, not external construct validation, and not evidence of statistical
consistency.  Historical artifacts are read-only.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "src"))

import numpy as np  # noqa: E402

from autonomy_sim.aggregate import composite_A  # noqa: E402
from autonomy_sim.native_benchmark import NativeConfig, exact_bundle  # noqa: E402
from autonomy_sim.native_joint_audit import (_canonical_hash,  # noqa: E402
                                             generate_execution_logs,
                                             generate_operating_logs)
from autonomy_sim.r19_joint_audit import (NRI_SHARE_DETECTION_LIMIT,  # noqa: E402
                                          estimate_from_logs_r19)

STUDY_SEEDS = (20261122, 20261123, 20261124, 20261125,
               20261126, 20261127, 20261128, 20261129)
CONVENTIONS = (("RNI", "normative_share_RNI"),
               ("NRI", "normative_share_NRI"),
               ("order_average", "normative_share_order_average"))


def _exact_composites(exact: dict) -> dict:
    channels = exact["channels"]
    rest = (channels["a_goal_structural"], channels["a_exec_open_loop"],
            channels["a_epi"], channels["a_ref"])
    report = exact["source"]["registered_partition"]
    return {convention: float(composite_A(
        exact["viability_state"], (report[key],) + rest,
        exact["config"]["weights"], sigma=1.0))
        for convention, key in CONVENTIONS}


def compute(*, n_samples: int = 8192, n_bootstrap: int = 200,
            seeds=STUDY_SEEDS) -> dict:
    config = NativeConfig(surgery=0)
    exact = exact_bundle(config)
    exact_composites = _exact_composites(exact)
    exact_shares = {convention: exact["source"]["registered_partition"][key]
                    for convention, key in CONVENTIONS}
    rows = []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        operating = generate_operating_logs(config, n_trajectories=n_samples, rng=rng)
        execution = generate_execution_logs(config, n_samples=n_samples, rng=rng)
        sampled = estimate_from_logs_r19(config, operating, execution,
                                         n_bootstrap=n_bootstrap, rng=rng)
        registered = sampled["source"]["registered_partition"]
        corrected = sampled["bias_corrected_shares"]["registered"]
        intervals = sampled["source_bootstrap_intervals"]
        uncertainty = sampled["composite_uncertainty"]["registered"]
        share_rows, composite_rows = {}, {}
        for convention, key in CONVENTIONS:
            plugin_share = registered[key]
            boot = intervals[key]["percentile_95"]
            share_rows[convention] = {
                "exact": exact_shares[convention],
                "plugin": plugin_share,
                "bias_corrected": corrected[key],
                "bootstrap_95": boot,
                "width": boot[1] - boot[0],
                "covers_exact": bool(boot[0] <= exact_shares[convention] <= boot[1]),
            }
            row = uncertainty[convention]
            interval = row["composite_bootstrap_95"]
            composite_rows[convention] = {
                "exact": exact_composites[convention],
                "plugin": row["plugin_composite"],
                "bias_corrected": row["bias_corrected_composite"],
                "bootstrap_95": interval,
                "width": interval[1] - interval[0],
                "abs_error_plugin": abs(row["plugin_composite"]
                                        - exact_composites[convention]),
                "abs_error_bias_corrected": abs(row["bias_corrected_composite"]
                                                - exact_composites[convention]),
                "covers_exact_plugin": bool(
                    interval[0] <= exact_composites[convention] <= interval[1]),
            }
        rows.append({
            "seed": seed,
            "operating_log_sha256": _canonical_hash(operating),
            "execution_log_sha256": _canonical_hash(execution),
            "shares": share_rows,
            "composites": composite_rows,
            "channel_errors": {
                "epistemic_abs": abs(sampled["epistemic"]["sample_mean"]
                                     - exact["epistemic"]["A_epi"]),
                "fidelity_abs": abs(sampled["reflection"]["fidelity"]
                                    - exact["reflection"]["fidelity"]),
                "execution_abs": abs(sampled["execution_open_loop"]["sample_a_exec"]
                                     - exact["execution_open_loop"]["state_averaged_a_exec"]),
                "Lambda_abs": abs(sampled["reflection"]["Lambda"]
                                  - exact["reflection"]["Lambda"]),
            },
        })

    def _aggregate(convention):
        values = [row["composites"][convention] for row in rows]
        n = len(values)
        bias_plugin = math.fsum(v["plugin"] - v["exact"] for v in values) / n
        bias_corrected = math.fsum(v["bias_corrected"] - v["exact"] for v in values) / n
        rmse_plugin = math.sqrt(math.fsum((v["plugin"] - v["exact"]) ** 2
                                          for v in values) / n)
        rmse_corrected = math.sqrt(math.fsum((v["bias_corrected"] - v["exact"]) ** 2
                                             for v in values) / n)
        return {
            "mean_bias_plugin": bias_plugin,
            "mean_bias_bias_corrected": bias_corrected,
            "rmse_plugin": rmse_plugin,
            "rmse_bias_corrected": rmse_corrected,
            "coverage_plugin_95": sum(v["covers_exact_plugin"] for v in values) / n,
            "mean_interval_width": math.fsum(v["width"] for v in values) / n,
            "max_abs_error_plugin": max(v["abs_error_plugin"] for v in values),
            "share_coverage_plugin_95":
                sum(row["shares"][convention]["covers_exact"] for row in rows) / n,
        }

    aggregates = {convention: _aggregate(convention) for convention, _ in CONVENTIONS}
    nri = aggregates["NRI"]
    return {
        "artifact_version": "R19-sampling-study-v1",
        "status": "INTERNAL_FINITE_SAMPLE_STUDY_NOT_EXTERNAL_NOT_POWER",
        "config": {"horizon": config.horizon, "p_obs": config.p_obs,
                   "q_self": config.q_self, "weights": list(config.weights)},
        "n_samples_per_stream": n_samples,
        "n_bootstrap": n_bootstrap,
        "seeds": list(seeds),
        "exact_composites": exact_composites,
        "exact_shares": exact_shares,
        "detection_limit": NRI_SHARE_DETECTION_LIMIT,
        "per_seed": rows,
        "aggregates": aggregates,
        "near_zero_finding": {
            "convention": "NRI",
            "exact_share": exact_shares["NRI"],
            "below_detection_limit": bool(exact_shares["NRI"] < NRI_SHARE_DETECTION_LIMIT),
            "plugin_composite_range_across_seeds": [
                min(row["composites"]["NRI"]["plugin"] for row in rows),
                max(row["composites"]["NRI"]["plugin"] for row in rows)],
            "interpretation": (
                "The exact NRI share is below the post hoc frozen internal detection "
                "limit. Plug-in sampling produces positive NRI composites far from the "
                "near-zero truth (geometric x^0.2 amplification); percentile intervals "
                "describe plug-in variability and do not cover the truth. Below-limit "
                "conventions must be reported with interval semantics ('below "
                "identifiable threshold'), never as high-confidence positive points. "
                "Bootstrap bias correction reduces the near-zero bias on average but "
                "is not a consistency guarantee."),
        },
        "scope": {
            "single_registered_instance": True,
            "independent_seeds": len(seeds),
            "resampling_unit": "trajectory",
            "external_construct_validation": False,
            "power_analysis": False,
            "statistical_consistency_claim": False,
        },
    }


def validate_result(result: dict) -> None:
    exact = result["exact_composites"]
    for convention, expected in (("RNI", 0.4608565248033332),
                                 ("NRI", 0.0003907988672884718),
                                 ("order_average", 0.4011989072662361)):
        if abs(exact[convention] - expected) > 1e-9:
            raise ValueError(f"sampling study exact anchor failed: {convention}")
    if len(result["per_seed"]) != len(result["seeds"]):
        raise ValueError("per-seed row count mismatch")
    seeds = [row["seed"] for row in result["per_seed"]]
    if len(set(seeds)) != len(seeds):
        raise ValueError("study seeds must be independent (distinct)")
    for row in result["per_seed"]:
        for convention, _ in CONVENTIONS:
            crow = row["composites"][convention]
            if not math.isfinite(crow["plugin"]) or not 0.0 <= crow["plugin"] <= 1.0:
                raise ValueError("composite out of range")
            if crow["bootstrap_95"][0] > crow["bootstrap_95"][1]:
                raise ValueError("interval order violated")
        for value in row["channel_errors"].values():
            if value > 0.05:
                raise ValueError("channel sampling error out of internal bound")
    aggregates = result["aggregates"]
    for convention, _ in CONVENTIONS:
        agg = aggregates[convention]
        if not 0.0 <= agg["coverage_plugin_95"] <= 1.0:
            raise ValueError("coverage rate out of range")
    # R20 test-design decoupling (R19 review item 4): the near-zero NRI
    # findings (plug-in error exceeding the threshold, bias correction
    # improving RMSE, percentile under-coverage) are DESCRIPTIVE empirical
    # results of this frozen study, recorded in the artifact and the paper.
    # They are NOT software invariants: a future improved estimator, a new
    # interval method, or new legitimate seeds must not fail validation for
    # recovering the endpoint better.  Only structural checks remain here;
    # the frozen artifact's specific values are covered by snapshot
    # regression in the test suite, not by universal acceptance conditions.
    if not result["near_zero_finding"]["below_detection_limit"]:
        raise ValueError("NRI exact share anchor: the fixture truth is below the limit")
    if result["scope"]["external_construct_validation"] or result["scope"]["power_analysis"]:
        raise ValueError("sampling study must not claim external validation or power")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-samples", type=int, default=8192)
    parser.add_argument("--n-bootstrap", type=int, default=200)
    parser.add_argument("--out", default=str(HERE / "analysis_r19_sampling_study.json"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = compute(n_samples=args.n_samples, n_bootstrap=args.n_bootstrap)
    validate_result(result)
    if args.check:
        saved = json.loads(Path(args.out).read_text(encoding="utf-8"))
        # The study is a deterministic function of its seeds; compare exactly
        # up to the default float tolerance (no optimizer coordinates here).
        from analysis_r15_x5c_paired import compare_replay_json
        comparison = compare_replay_json(saved, result)
        if not comparison["passed"]:
            raise SystemExit("R19 sampling study check FAILED: "
                             + "; ".join(comparison["differences"][:8]))
        print("R19 sampling study check OK: "
              f"{len(result['seeds'])} independent seeds, bias/coverage/width anchored; "
              f"max abs float diff={comparison['max_abs_float_difference']:.3e}")
        return 0
    Path(args.out).write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                              encoding="utf-8")
    print("R19 multi-seed sampling study PASS (internal finite-sample study)")
    for convention, _ in CONVENTIONS:
        agg = result["aggregates"][convention]
        print(f"  {convention}: bias_plugin={agg['mean_bias_plugin']:.6f} "
              f"rmse_plugin={agg['rmse_plugin']:.6f} "
              f"coverage95={agg['coverage_plugin_95']:.3f} "
              f"width={agg['mean_interval_width']:.6f} "
              f"rmse_corrected={agg['rmse_bias_corrected']:.6f}")
    print("[out]", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
