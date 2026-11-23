#!/usr/bin/env python3
"""R22 detection study: matched A/B/C interval-method contrasts.

Supersedes the R21 detection study (read-only, retained).  The predeclared grid
is unchanged: 16 independent seeds (20261122..20261137) x n in {2048,8192} x
200 trajectory-block bootstrap resamples, the frozen R19 estimator, and the R20
data-driven detection rule.  The formal certificate remains the R21 basic
share-conditional interval / logical envelope.

R22 repairs R21's attribution-identification problem.  On the SAME replicates:
A = basic share-conditional, B = percentile share-conditional composite, and
C = percentile joint composite.  B versus C is a matched-percentile channel-
propagation contrast; A versus B is an interval-construction contrast.  A versus
C still mixes construction and conditioning.  Coverage-pattern counts are named
``descriptive_interval_method_contrast`` and are NEVER interpreted as a formal
bias decomposition or single-cause attribution.  Exact-truth multi-seed plug-in
bias/RMSE are reported separately as descriptive simulation results.

Logical-envelope anchor containment remains distinct from every sampling
coverage rate.  This is an internal descriptive finite-sample study, not a power
analysis, universal-coverage claim, or external construct validation.  Software
validation checks structure, formulas, bounds, anchors, and governance only;
empirical findings are data, not pass conditions.
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
                                        basic_bootstrap_bias_corrected_interval,
                                        classify_share_interval,
                                        oracle_assisted_fixture_classification)
from autonomy_sim.r21_guards import SHARE_CONDITIONAL_KIND  # noqa: E402
from autonomy_sim.r22_interval_contrast import (  # noqa: E402
    CONTRAST_POLICY, METHOD_A, METHOD_B, METHOD_C, METHODS,
    coverage_transitions, matched_interval_bootstrap, method_coverage)

PREDECLARED_GRID = {
    "seeds": list(range(20261122, 20261138)),
    "n_samples_per_stream": [2048, 8192],
    "n_bootstrap": 200,
    "n_joint_bootstrap": 200,
    "n_matched_bootstrap": 200,
    "estimator": "r19_joint_audit.estimate_from_logs_r19 (frozen R19 estimator)",
    "decision_rule": DETECTION_RULE_VERSION,
    "detection_limit": DETECTION_LIMIT,
    "resampling_unit": "trajectory",
    "joint_resampling": "operating_joint_all_channels; execution_stratified_by_sequence_independent",
    "comparison_grid": "convention x n_samples: classification rates vs oracle, "
                       "envelope containment, formal-A coverage, matched A/B/C coverage "
                       "and descriptive construction/propagation contrasts",
    "matched_design": "same replicates: A basic-SC, B percentile-SC, C percentile-joint",
    "declared_before_outcomes": True,
    "matched_design_declared_before_r22_outcomes": True,
}
CONVENTIONS = (("RNI", "normative_share_RNI"),
               ("NRI", "normative_share_NRI"),
               ("order_average", "normative_share_order_average"))
CONDITIONING_SCOPE_PLUGIN = "other_channels_fixed_at_plugin"
COVERAGE_SEMANTICS = {
    "logical_envelope_anchor_containment":
        "CONTAINMENT_DIAGNOSTIC_NOT_STATISTICAL_COVERAGE",
    "formal_basic_share_conditional_coverage":
        "CERTIFICATE_A_ORIGINAL_BOOTSTRAP_STREAM_UNCHANGED",
    "A_basic_share_conditional_coverage":
        "MATCHED_STREAM_RECOMPUTATION_OF_CERTIFICATE_CONSTRUCTION",
    "B_percentile_share_conditional_coverage":
        "OTHER_CHANNELS_FIXED_AT_ORIGINAL_PLUGIN_POINTS",
    "C_percentile_joint_coverage":
        "ALL_DATA_ESTIMATED_CHANNELS_RECOMPUTED_STRUCTURAL_GOAL_FIXED_SUPPLEMENTARY_DIAGNOSTIC",
    "no_combined_or_cross_kind_coverage_comparison": True,
    "no_single_cause_attribution_from_coverage_patterns": True,
    "potential_undercoverage_sources": [
        "source_share_plugin_bias",
        "other_channel_estimation_bias_and_covariance",
        "interval_construction_basic_vs_percentile",
    ],
}


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
    n_matched = grid.get("n_matched_bootstrap", grid["n_joint_bootstrap"])
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

            # R22: one matched stream for A/B/C.  Its C operation/RNG sequence is
            # identical to R21, while A/B are added without another resampling draw.
            rng_matched = np.random.default_rng([seed, n_samples, 21])
            matched = matched_interval_bootstrap(
                config, operating, execution, sampled,
                n_bootstrap=n_matched, rng=rng_matched)
            convention_rows = {}
            for convention, key in CONVENTIONS:
                plugin = registered[key]
                perc = intervals[key]["percentile_95"]
                decision = basic_bootstrap_bias_corrected_interval(plugin, perc[0], perc[1])
                status = classify_share_interval(decision)
                if status == "DATA_ABOVE_LIMIT":
                    bounds = [float(fn(decision[0])), float(fn(decision[1]))] if fn else None
                    kind = SHARE_CONDITIONAL_KIND
                else:
                    bounds = [0.0, float(fn(decision[1]))] if fn else None
                    kind = "LOGICAL_ENVELOPE"
                exact_c = exact_composites[convention]
                contains = (bool(bounds[0] <= exact_c <= bounds[1])
                            if bounds is not None else None)
                oracle = oracle_assisted_fixture_classification(exact_shares[convention])
                below = oracle["oracle_below_limit"]
                if status == "DATA_BELOW_LIMIT":
                    comparison = "TRUE_BELOW" if below else "FALSE_BELOW"
                elif status == "DATA_ABOVE_LIMIT":
                    comparison = "FALSE_ABOVE" if below else "TRUE_ABOVE"
                else:
                    comparison = ("INDETERMINATE_TRUE_BELOW" if below
                                  else "INDETERMINATE_TRUE_ABOVE")
                interval_entry = matched["intervals"]["registered"][convention]
                coverage = method_coverage(interval_entry, exact_c)
                plugin_composite = float(fn(plugin)) if fn else None
                c_bounds = interval_entry[METHOD_C]["bounds"]
                convention_rows[convention] = {
                    "convention_status": status,
                    "classification_vs_oracle": comparison,
                    "decision_share_interval": decision,
                    "reported_composite_interval": bounds,
                    "reported_interval_kind": kind,
                    "reported_interval_conditioning_scope": CONDITIONING_SCOPE_PLUGIN,
                    "logical_envelope_anchor_containment":
                        contains if kind == "LOGICAL_ENVELOPE" else None,
                    "share_conditional_sampling_covers_exact":
                        contains if kind == SHARE_CONDITIONAL_KIND else None,
                    # Backward-readable names for the R21 C diagnostic; R22 tables
                    # use the explicit A/B/C fields below.
                    "joint_sampling_interval": c_bounds,
                    "joint_sampling_covers_exact": coverage[METHOD_C],
                    "reported_width": (bounds[1] - bounds[0]) if bounds else None,
                    "share_interval_covers_exact_share":
                        bool(decision[0] <= exact_shares[convention] <= decision[1]),
                    "diagnostic_plugin_share": plugin,
                    "diagnostic_plugin_composite": plugin_composite,
                    "diagnostic_abs_error":
                        abs(plugin_composite - exact_c) if plugin_composite is not None else None,
                    "matched_interval_methods": interval_entry,
                    "method_coverage": coverage,
                    "method_widths": {
                        method: interval_entry[method]["bounds"][1]
                                - interval_entry[method]["bounds"][0]
                        for method in METHODS},
                    "matched_replicate_audit":
                        matched["replicate_audit"]["registered"][convention],
                }
            cells.append({
                "n_samples": n_samples,
                "seed": seed,
                "operating_log_sha256": _canonical_hash(operating),
                "execution_log_sha256": _canonical_hash(execution),
                "matched_resampling_audit": matched["resampling_audit"],
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
            statuses = {s: sum(r["convention_status"] == s for r in rows) / count
                        for s in ("DATA_BELOW_LIMIT", "DATA_ABOVE_LIMIT",
                                  "INDETERMINATE_NEAR_ZERO")}
            comparisons = {lab: sum(r["classification_vs_oracle"] == lab for r in rows) / count
                           for lab in ("TRUE_BELOW", "FALSE_ABOVE", "INDETERMINATE_TRUE_BELOW",
                                       "TRUE_ABOVE", "FALSE_BELOW", "INDETERMINATE_TRUE_ABOVE")}
            kinds = {r["reported_interval_kind"] for r in rows}
            kind = next(iter(kinds)) if len(kinds) == 1 else "MIXED"
            envelope_rows = [r for r in rows if r["reported_interval_kind"] == "LOGICAL_ENVELOPE"]
            sampling_rows = [r for r in rows
                             if r["reported_interval_kind"] == SHARE_CONDITIONAL_KIND]
            errors = [r["diagnostic_abs_error"] for r in rows
                      if r["diagnostic_abs_error"] is not None]
            plugins = [r["diagnostic_plugin_composite"] for r in rows
                       if r["diagnostic_plugin_composite"] is not None]
            method_rates = {method: sum(r["method_coverage"][method] for r in rows) / count
                            for method in METHODS}
            method_widths = {method: math.fsum(r["method_widths"][method] for r in rows) / count
                             for method in METHODS}
            aggregates[str(n_samples)][convention] = {
                "status_rates": statuses,
                "oracle_comparison_rates": comparisons,
                "false_below_rate": comparisons["FALSE_BELOW"],
                "false_above_rate": comparisons["FALSE_ABOVE"],
                "indeterminate_rate": statuses["INDETERMINATE_NEAR_ZERO"],
                "reported_interval_kind": kind,
                "logical_envelope_anchor_containment_rate":
                    (sum(r["logical_envelope_anchor_containment"] for r in envelope_rows)
                     / len(envelope_rows)) if envelope_rows else None,
                "share_conditional_sampling_coverage_rate":
                    (sum(r["share_conditional_sampling_covers_exact"] for r in sampling_rows)
                     / len(sampling_rows)) if sampling_rows else None,
                "joint_sampling_coverage_rate": method_rates[METHOD_C],
                "interval_method_coverage_rates": method_rates,
                "interval_method_mean_widths": method_widths,
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
                "descriptive_interval_method_contrast": {
                    "A_vs_B": coverage_transitions(rows, METHOD_A, METHOD_B),
                    "B_vs_C": coverage_transitions(rows, METHOD_B, METHOD_C),
                    "A_vs_C": coverage_transitions(rows, METHOD_A, METHOD_C),
                    "n_cells": count,
                    "note": ("Descriptive coverage-pattern counts only. A/C mixes interval "
                             "construction and conditioning; B/C matches replicates and "
                             "percentile construction but is not a formal bias decomposition. "
                             "Both-miss cells receive no single-cause attribution."),
                },
            }
    return {
        "artifact_version": "R22-detection-study-v1",
        "status": "INTERNAL_FINITE_SAMPLE_STUDY_NOT_EXTERNAL_NOT_POWER",
        "predeclared_grid": grid,
        "coverage_semantics": dict(COVERAGE_SEMANTICS),
        "contrast_policy": dict(CONTRAST_POLICY),
        "method_labels": {METHOD_A: "basic-share-conditional",
                          METHOD_B: "percentile-share-conditional",
                          METHOD_C: "percentile-joint"},
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
            "joint_bootstrap": "SUPPLEMENTARY_DIAGNOSTIC_NOT_REPORTED_SEMANTICS",
            "causal_undercoverage_attribution": False,
            "formal_bias_decomposition": False,
            "supersedes": ("R21 detection study (read-only; its A/C conditional-design "
                           "attribution is withdrawn and replaced by matched A/B/C "
                           "descriptive interval-method contrasts)"),
        },
        "interpretation": ("Descriptive finite-sample behavior on one registered instance. "
                           "A/B/C are computed on common replicates. B/C contrasts channel "
                           "propagation under matched percentile construction; A/B contrasts "
                           "interval constructions; A/C remains mixed. No coverage pattern is "
                           "a single-cause attribution or formal bias decomposition. Plug-in "
                           "bias/RMSE are separate exact-truth simulation summaries. Logical-"
                           "envelope containment is not statistical coverage; INDETERMINATE is "
                           "an honest outcome. Rates describe this grid only."),
    }


def validate_result(result: dict) -> None:
    """Structural/formula/boundary/anchor/governance checks; no empirical targets."""
    grid = result["predeclared_grid"]
    if not grid["declared_before_outcomes"] or not grid.get(
            "matched_design_declared_before_r22_outcomes", False):
        raise ValueError("grid and matched design must be declared before outcomes")
    if grid["decision_rule"] != DETECTION_RULE_VERSION:
        raise ValueError("decision rule version drift")
    if grid["detection_limit"] != DETECTION_LIMIT:
        raise ValueError("detection limit drift")
    if grid.get("n_matched_bootstrap", grid["n_joint_bootstrap"]) != \
            grid["n_joint_bootstrap"]:
        raise ValueError("joint and matched bootstrap counts must agree for the C alias")
    seeds = grid["seeds"]
    if len(set(seeds)) != len(seeds):
        raise ValueError("study seeds must be distinct")
    expected_cells = len(seeds) * len(grid["n_samples_per_stream"])
    if len(result["cells"]) != expected_cells:
        raise ValueError("cell count must match the predeclared grid")
    seen = {(cell["n_samples"], cell["seed"]) for cell in result["cells"]}
    if len(seen) != expected_cells:
        raise ValueError("grid cells must be unique")
    if result["coverage_semantics"] != COVERAGE_SEMANTICS:
        raise ValueError("coverage semantics drift")
    if result["contrast_policy"] != CONTRAST_POLICY:
        raise ValueError("descriptive contrast policy drift")
    for cell in result["cells"]:
        if cell["seed"] not in seeds or cell["n_samples"] not in grid["n_samples_per_stream"]:
            raise ValueError("cell outside the predeclared grid")
        if not cell["matched_resampling_audit"]["not_analysis_output_float_hash"] or \
                len(cell["matched_resampling_audit"]["draws_sha256"]) != 64:
            raise ValueError("cell must hash exact resampling inputs, not float outputs")
        for value in cell["channel_errors"].values():
            # Descriptive simulation errors are data, not an empirical pass gate.
            if not math.isfinite(value) or value < 0.0:
                raise ValueError("channel error must be finite and nonnegative")
        for convention, _ in CONVENTIONS:
            row = cell["conventions"][convention]
            if row["convention_status"] not in (
                    "DATA_BELOW_LIMIT", "DATA_ABOVE_LIMIT", "INDETERMINATE_NEAR_ZERO"):
                raise ValueError("invalid classification status")
            lo, hi = row["decision_share_interval"]
            if not 0.0 <= lo <= hi <= 1.0:
                raise ValueError("decision interval out of bounds")
            kind = row["reported_interval_kind"]
            if kind == "LOGICAL_ENVELOPE":
                if row["logical_envelope_anchor_containment"] is None or \
                        row["share_conditional_sampling_covers_exact"] is not None:
                    raise ValueError("envelope must report containment, not sampling coverage")
            elif kind == SHARE_CONDITIONAL_KIND:
                if row["share_conditional_sampling_covers_exact"] is None or \
                        row["logical_envelope_anchor_containment"] is not None:
                    raise ValueError("sampling must report coverage, not envelope containment")
            else:
                raise ValueError("invalid reported interval kind")
            if row["reported_composite_interval"] is not None:
                rlo, rhi = row["reported_composite_interval"]
                if not 0.0 <= rlo <= rhi <= 1.0:
                    raise ValueError("reported composite interval out of bounds")
            if set(row["matched_interval_methods"]) != set(METHODS):
                raise ValueError("matched interval entry must contain exactly A/B/C")
            entry = row["matched_interval_methods"]
            if row["joint_sampling_interval"] != entry[METHOD_C]["bounds"] or \
                    row["joint_sampling_covers_exact"] is not row["method_coverage"][METHOD_C]:
                raise ValueError("backward-readable C alias drift")
            if entry[METHOD_A]["plugin_share"] != row["diagnostic_plugin_share"]:
                raise ValueError("matched A plugin share differs from the R19 cell input")
            expected_basic = basic_bootstrap_bias_corrected_interval(
                row["diagnostic_plugin_share"],
                *entry[METHOD_A]["share_percentile_95"])
            if entry[METHOD_A]["share_basic_interval"] != expected_basic:
                raise ValueError("A basic interval fails independent recomputation")
            if set(row["method_coverage"]) != set(METHODS):
                raise ValueError("method coverage must contain exactly A/B/C")
            for method in METHODS:
                bounds = row["matched_interval_methods"][method]["bounds"]
                if not 0.0 <= bounds[0] <= bounds[1] <= 1.0:
                    raise ValueError("matched method interval out of bounds")
                if not isinstance(row["method_coverage"][method], bool):
                    raise ValueError("method coverage flag must be Boolean")
                expected_width = bounds[1] - bounds[0]
                if abs(row["method_widths"][method] - expected_width) > 1e-12:
                    raise ValueError("method width mismatch")
            audit = row["matched_replicate_audit"]
            if audit["n_common_finite"] < 2 or audit["n_common_finite"] > audit["n_bootstrap"]:
                raise ValueError("invalid common replicate count")
            if audit["n_common_finite"] + audit["n_excluded_from_matched_contrast"] != \
                    audit["n_bootstrap"]:
                raise ValueError("matched replicate accounting mismatch")
            if len(audit["common_finite_mask_sha256"]) != 64:
                raise ValueError("common-mask audit missing or malformed")
    for n_key, conventions in result["aggregates"].items():
        for convention, _ in CONVENTIONS:
            agg = conventions[convention]
            if abs(sum(agg["status_rates"].values()) - 1.0) > 1e-9:
                raise ValueError("status rates must sum to one")
            for rate in agg["oracle_comparison_rates"].values():
                if not 0.0 <= rate <= 1.0:
                    raise ValueError("comparison rate out of range")
            for rate in agg["interval_method_coverage_rates"].values():
                if not 0.0 <= rate <= 1.0:
                    raise ValueError("method coverage rate out of range")
            contrast = agg["descriptive_interval_method_contrast"]
            if "undercoverage_attribution" in agg:
                raise ValueError("causal attribution field must not reappear")
            for pair in ("A_vs_B", "B_vs_C", "A_vs_C"):
                counts = contrast[pair]
                if sum(counts.values()) != contrast["n_cells"]:
                    raise ValueError("coverage-transition counts must sum to cell count")
                if any(value < 0 for value in counts.values()):
                    raise ValueError("coverage-transition counts must be nonnegative")
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
    if result["scope"]["causal_undercoverage_attribution"] or \
            result["scope"]["formal_bias_decomposition"]:
        raise ValueError("study must not claim causal attribution or formal bias decomposition")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(HERE / "analysis_r22_detection_study.json"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = compute()
    validate_result(result)
    if args.check:
        saved = json.loads(Path(args.out).read_text(encoding="utf-8"))
        from analysis_r15_x5c_paired import compare_replay_json
        comparison = compare_replay_json(saved, result)
        if not comparison["passed"]:
            raise SystemExit("R22 detection study check FAILED: "
                             + "; ".join(comparison["differences"][:8]))
        print("R22 detection study check OK: predeclared 16-seed x {2048,8192} grid, "
              "matched A/B/C descriptive construction/propagation contrasts, no causal "
              "under-coverage attribution; "
              f"max abs float diff={comparison['max_abs_float_difference']:.3e}")
        return 0
    Path(args.out).write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                              encoding="utf-8")
    print("R22 detection study PASS (internal descriptive finite-sample study)")
    for n_key, conventions in result["aggregates"].items():
        for convention, _ in CONVENTIONS:
            agg = conventions[convention]
            rates = agg["interval_method_coverage_rates"]
            bc = agg["descriptive_interval_method_contrast"]["B_vs_C"]
            env = agg["logical_envelope_anchor_containment_rate"]
            print(f"  n={n_key} {convention}: indet={agg['indeterminate_rate']:.3f} "
                  f"envelope_containment={env if env is None else round(env,3)} "
                  f"A={rates[METHOD_A]:.3f} B={rates[METHOD_B]:.3f} C={rates[METHOD_C]:.3f} "
                  f"Bmiss_Ccover={bc['miss_cover']} Bmiss_Cmiss={bc['miss_miss']}")
    print("[out]", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
