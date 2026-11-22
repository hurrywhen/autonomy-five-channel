#!/usr/bin/env python3
"""R20 detection-rule misclassification and estimation-coverage study (internal).

PRE-DECLARED GRID (frozen in this source BEFORE any R20 study outcome was
computed; the decision rule itself is r20_detection.DETECTION_RULE_VERSION):

* seeds: 20261122..20261137 (16 independent seeds);
* sample sizes per stream: {2048, 8192};
* trajectory-block bootstrap resamples: 200;
* estimator: the frozen R19 trajectory-block estimator
  (r19_joint_audit.estimate_from_logs_r19), unchanged;
* comparison grid: per attribution convention x sample size, report the
  three-state classification rates against the oracle truth (fixture-only
  evaluation), false-below / false-above / indeterminate rates, reported
  composite-interval coverage of the exact composite anchor, mean interval
  width, share-interval coverage, and descriptive plug-in bias/RMSE.

The oracle truth labels classifications for EVALUATION only; it never enters
the decision.  This is an internal finite-sample study on one registered
instance: descriptive, not a power analysis, not a universal coverage claim,
not external construct validation.  Software validation checks structure,
bounds, and analytic anchors only --- empirical findings are recorded as
data, never enforced as pass conditions (R20 review item 4).
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
from autonomy_sim.r19_joint_audit import estimate_from_logs_r19  # noqa: E402
from autonomy_sim.r20_detection import (DETECTION_LIMIT,  # noqa: E402
                                        DETECTION_RULE_VERSION,
                                        convention_detection_report)

PREDECLARED_GRID = {
    "seeds": list(range(20261122, 20261138)),
    "n_samples_per_stream": [2048, 8192],
    "n_bootstrap": 200,
    "estimator": "r19_joint_audit.estimate_from_logs_r19 (frozen R19 estimator)",
    "decision_rule": DETECTION_RULE_VERSION,
    "detection_limit": DETECTION_LIMIT,
    "resampling_unit": "trajectory",
    "comparison_grid": "convention x n_samples: classification rates vs oracle, "
                       "coverage, width, descriptive bias/RMSE",
    "declared_before_outcomes": True,
}
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


def compute(*, grid: dict | None = None) -> dict:
    grid = dict(grid or PREDECLARED_GRID)
    config = NativeConfig(surgery=0)
    exact = exact_bundle(config)
    exact_composites = _exact_composites(exact)
    exact_shares = {convention: exact["source"]["registered_partition"][key]
                    for convention, key in CONVENTIONS}
    cells = []
    for n_samples in grid["n_samples_per_stream"]:
        for seed in grid["seeds"]:
            rng = np.random.default_rng(seed)
            operating = generate_operating_logs(config, n_trajectories=n_samples, rng=rng)
            execution = generate_execution_logs(config, n_samples=n_samples, rng=rng)
            sampled = estimate_from_logs_r19(config, operating, execution,
                                             n_bootstrap=grid["n_bootstrap"], rng=rng)
            registered = sampled["source"]["registered_partition"]
            intervals = sampled["source_bootstrap_intervals"]
            channels = sampled["channels"]
            fn = None
            if channels["a_ref"] is not None:
                rest = (channels["a_goal_structural"], channels["a_exec_open_loop"],
                        channels["a_epi"], channels["a_ref"])
                viability = sampled["viability_state"]
                weights = config.weights

                def fn(share, rest=rest, viability=viability, weights=weights):
                    return float(composite_A(viability, (share,) + rest, weights, sigma=1.0))
            convention_rows = {}
            for convention, key in CONVENTIONS:
                rep = convention_detection_report(
                    plugin_share=registered[key],
                    percentile_interval=intervals[key]["percentile_95"],
                    composite_fn=fn, exact_share=exact_shares[convention])
                bounds = rep["composite_interval"]["bounds"] if rep["composite_interval"] else None
                share_bounds = rep["share_interval"]["bounds"]
                convention_rows[convention] = {
                    "convention_status": rep["convention_status"],
                    "classification_vs_oracle":
                        rep["oracle_evaluation"]["classification_vs_oracle"],
                    "decision_share_interval": share_bounds,
                    "reported_composite_interval": bounds,
                    "reported_interval_kind":
                        rep["composite_interval"]["kind"] if rep["composite_interval"] else None,
                    "reported_covers_exact_composite":
                        bool(bounds is not None
                             and bounds[0] <= exact_composites[convention] <= bounds[1]),
                    "reported_width": (bounds[1] - bounds[0]) if bounds else None,
                    "share_interval_covers_exact_share":
                        bool(share_bounds[0] <= exact_shares[convention] <= share_bounds[1]),
                    "diagnostic_plugin_composite": rep["diagnostic_plugin_composite"],
                    "diagnostic_abs_error":
                        abs(rep["diagnostic_plugin_composite"] - exact_composites[convention])
                        if rep["diagnostic_plugin_composite"] is not None else None,
                }
            cells.append({
                "n_samples": n_samples,
                "seed": seed,
                "operating_log_sha256": _canonical_hash(operating),
                "execution_log_sha256": _canonical_hash(execution),
                "conventions": convention_rows,
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

    aggregates = {}
    for n_samples in grid["n_samples_per_stream"]:
        subset = [cell for cell in cells if cell["n_samples"] == n_samples]
        count = len(subset)
        aggregates[str(n_samples)] = {}
        for convention, _ in CONVENTIONS:
            rows = [cell["conventions"][convention] for cell in subset]
            statuses = {}
            for status in ("DATA_BELOW_LIMIT", "DATA_ABOVE_LIMIT", "INDETERMINATE_NEAR_ZERO"):
                statuses[status] = sum(r["convention_status"] == status for r in rows) / count
            comparisons = {}
            for label in ("TRUE_BELOW", "FALSE_ABOVE", "INDETERMINATE_TRUE_BELOW",
                          "TRUE_ABOVE", "FALSE_BELOW", "INDETERMINATE_TRUE_ABOVE"):
                comparisons[label] = sum(
                    r["classification_vs_oracle"] == label for r in rows) / count
            errors = [r["diagnostic_abs_error"] for r in rows
                      if r["diagnostic_abs_error"] is not None]
            plugins = [r["diagnostic_plugin_composite"] for r in rows
                       if r["diagnostic_plugin_composite"] is not None]
            aggregates[str(n_samples)][convention] = {
                "status_rates": statuses,
                "oracle_comparison_rates": comparisons,
                "false_below_rate": comparisons["FALSE_BELOW"],
                "false_above_rate": comparisons["FALSE_ABOVE"],
                "indeterminate_rate": statuses["INDETERMINATE_NEAR_ZERO"],
                "reported_composite_coverage_rate":
                    sum(r["reported_covers_exact_composite"] for r in rows) / count,
                "mean_reported_width":
                    math.fsum(r["reported_width"] for r in rows
                              if r["reported_width"] is not None) / count,
                "share_interval_coverage_rate":
                    sum(r["share_interval_covers_exact_share"] for r in rows) / count,
                "diagnostic_mean_bias":
                    math.fsum(p - exact_composites[convention] for p in plugins) / count
                    if plugins else None,
                "diagnostic_rmse":
                    math.sqrt(math.fsum(e * e for e in errors) / count) if errors else None,
            }
    return {
        "artifact_version": "R20-detection-study-v1",
        "status": "INTERNAL_FINITE_SAMPLE_STUDY_NOT_EXTERNAL_NOT_POWER",
        "predeclared_grid": grid,
        "config": {"horizon": config.horizon, "p_obs": config.p_obs,
                   "q_self": config.q_self, "weights": list(config.weights)},
        "exact_composites_model_anchors": exact_composites,
        "exact_shares": exact_shares,
        "cells": cells,
        "aggregates": aggregates,
        "scope": {
            "single_registered_instance": True,
            "independent_seeds": len(grid["seeds"]),
            "oracle_used_for_evaluation_only": True,
            "oracle_used_in_decision": False,
            "external_construct_validation": False,
            "power_analysis": False,
            "universal_coverage_claim": False,
            "statistical_consistency_claim": False,
        },
        "interpretation": ("Descriptive finite-sample behavior of the declared "
                           "data-driven detection rule on one registered instance. "
                           "Classification rates are relative to the fixture's oracle "
                           "truth; INDETERMINATE is an honest outcome, not a failure. "
                           "Coverage rates describe this grid only, not a universal "
                           "guarantee."),
    }


def validate_result(result: dict) -> None:
    """Structural/boundary/anchor checks only; no empirical pass conditions."""
    grid = result["predeclared_grid"]
    if not grid["declared_before_outcomes"]:
        raise ValueError("grid must be declared before outcomes")
    if grid["decision_rule"] != DETECTION_RULE_VERSION:
        raise ValueError("decision rule version drift")
    if grid["detection_limit"] != DETECTION_LIMIT:
        raise ValueError("detection limit drift")
    seeds = grid["seeds"]
    if len(set(seeds)) != len(seeds):
        raise ValueError("study seeds must be distinct")
    expected_cells = len(seeds) * len(grid["n_samples_per_stream"])
    if len(result["cells"]) != expected_cells:
        raise ValueError("cell count must match the predeclared grid")
    seen = {(cell["n_samples"], cell["seed"]) for cell in result["cells"]}
    if len(seen) != expected_cells:
        raise ValueError("grid cells must be unique")
    for cell in result["cells"]:
        if cell["seed"] not in seeds or cell["n_samples"] not in grid["n_samples_per_stream"]:
            raise ValueError("cell outside the predeclared grid")
        for value in cell["channel_errors"].values():
            if not math.isfinite(value) or value > 0.05:
                raise ValueError("channel implementation-agreement bound violated")
        for convention, _ in CONVENTIONS:
            row = cell["conventions"][convention]
            if row["convention_status"] not in (
                    "DATA_BELOW_LIMIT", "DATA_ABOVE_LIMIT", "INDETERMINATE_NEAR_ZERO"):
                raise ValueError("invalid classification status")
            lo, hi = row["decision_share_interval"]
            if not 0.0 <= lo <= hi <= 1.0:
                raise ValueError("decision interval out of bounds")
            if row["reported_composite_interval"] is not None:
                blo, bhi = row["reported_composite_interval"]
                if not 0.0 <= blo <= bhi <= 1.0:
                    raise ValueError("reported composite interval out of bounds")
    for n_key, conventions in result["aggregates"].items():
        for convention, _ in CONVENTIONS:
            agg = conventions[convention]
            total = sum(agg["status_rates"].values())
            if abs(total - 1.0) > 1e-9:
                raise ValueError("status rates must sum to one")
            for rate in agg["oracle_comparison_rates"].values():
                if not 0.0 <= rate <= 1.0:
                    raise ValueError("comparison rate out of range")
            if not 0.0 <= agg["reported_composite_coverage_rate"] <= 1.0:
                raise ValueError("coverage rate out of range")
    anchors = result["exact_composites_model_anchors"]
    for convention, expected in (("RNI", 0.4608565248033332),
                                 ("NRI", 0.0003907988672884718),
                                 ("order_average", 0.4011989072662361)):
        if abs(anchors[convention] - expected) > 1e-9:
            raise ValueError(f"exact composite anchor failed: {convention}")
    if result["scope"]["oracle_used_in_decision"]:
        raise ValueError("oracle must never enter the decision")
    if result["scope"]["external_construct_validation"] or result["scope"]["power_analysis"]:
        raise ValueError("study must not claim external validation or power")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(HERE / "analysis_r20_detection_study.json"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = compute()
    validate_result(result)
    if args.check:
        saved = json.loads(Path(args.out).read_text(encoding="utf-8"))
        from analysis_r15_x5c_paired import compare_replay_json
        comparison = compare_replay_json(saved, result)
        if not comparison["passed"]:
            raise SystemExit("R20 detection study check FAILED: "
                             + "; ".join(comparison["differences"][:8]))
        print("R20 detection study check OK: predeclared 16-seed x {2048,8192} grid, "
              "data-driven rule, oracle evaluation only; "
              f"max abs float diff={comparison['max_abs_float_difference']:.3e}")
        return 0
    Path(args.out).write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                              encoding="utf-8")
    print("R20 detection study PASS (internal descriptive finite-sample study)")
    for n_key, conventions in result["aggregates"].items():
        for convention, _ in CONVENTIONS:
            agg = conventions[convention]
            print(f"  n={n_key} {convention}: below={agg['status_rates']['DATA_BELOW_LIMIT']:.3f} "
                  f"above={agg['status_rates']['DATA_ABOVE_LIMIT']:.3f} "
                  f"indeterminate={agg['indeterminate_rate']:.3f} "
                  f"false_below={agg['false_below_rate']:.3f} false_above={agg['false_above_rate']:.3f} "
                  f"coverage={agg['reported_composite_coverage_rate']:.3f} "
                  f"width={agg['mean_reported_width']:.5f}")
    print("[out]", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())