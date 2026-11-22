#!/usr/bin/env python3
"""R21 detection-rule study: separated coverage semantics + joint diagnostic.

Supersedes the R20 detection study (read-only, retained).  Same PRE-DECLARED
grid (frozen before R20 outcomes, unchanged): 16 independent seeds
(20261122..20261137) x n in {2048, 8192} x 200 trajectory-block bootstrap
resamples; the frozen R19 estimator and the R20 data-driven detection rule.

R21 changes the REPORTING, not the rule or the grid:

1. **Coverage semantics separated.**  For below/indeterminate conventions the
   reported interval is a LOGICAL_ENVELOPE; whether it contains the exact model
   anchor is ``logical_envelope_anchor_containment`` (a containment diagnostic,
   NOT statistical coverage).  For above-limit conventions the reported interval
   is a SHARE_CONDITIONAL sampling interval; its coverage is
   ``share_conditional_sampling_coverage`` (conditional on the other channels
   being fixed at plugin points).  The two are never combined into a single
   coverage rate nor compared as estimator quality.
2. **Joint trajectory bootstrap (supplementary).**  On every cell a joint
   bootstrap recomputes ALL channels per resample (within-batch covariance
   preserved; execution stratified by sequence, independent) and gives a genuine
   joint composite sampling interval; ``joint_sampling_coverage`` is reported as
   a supplementary diagnostic (not the certificate's reported semantics).
3. **Two-cause under-coverage attribution (descriptive).**  For above-limit
   conventions we count cells where the share-conditional interval misses the
   anchor but the joint interval covers it (attributable to the conditional
   design) versus cells where both miss (residual plug-in bias).  This quantifies
   the R20 review's point that under-coverage is not bias alone.

Internal descriptive finite-sample study on one registered instance; not a power
analysis, not a universal coverage claim, not external construct validation.
Software validation checks structure/bounds/anchors/governance only; empirical
rates are recorded as data, never enforced as pass conditions.
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
from autonomy_sim.r21_joint_bootstrap import joint_composite_bootstrap  # noqa: E402

PREDECLARED_GRID = {
    "seeds": list(range(20261122, 20261138)),
    "n_samples_per_stream": [2048, 8192],
    "n_bootstrap": 200,
    "n_joint_bootstrap": 200,
    "estimator": "r19_joint_audit.estimate_from_logs_r19 (frozen R19 estimator)",
    "decision_rule": DETECTION_RULE_VERSION,
    "detection_limit": DETECTION_LIMIT,
    "resampling_unit": "trajectory",
    "joint_resampling": "operating_joint_all_channels; execution_stratified_by_sequence_independent",
    "comparison_grid": "convention x n_samples: classification rates vs oracle, "
                       "separated envelope containment / share-conditional coverage / "
                       "joint coverage, width, descriptive bias/RMSE",
    "declared_before_outcomes": True,
}
CONVENTIONS = (("RNI", "normative_share_RNI"),
               ("NRI", "normative_share_NRI"),
               ("order_average", "normative_share_order_average"))
CONDITIONING_SCOPE_PLUGIN = "other_channels_fixed_at_plugin"
COVERAGE_SEMANTICS = {
    "logical_envelope_anchor_containment":
        "CONTAINMENT_DIAGNOSTIC_NOT_STATISTICAL_COVERAGE",
    "share_conditional_sampling_coverage":
        "CONDITIONAL_ON_OTHER_CHANNELS_FIXED_AT_PLUGIN",
    "joint_sampling_coverage":
        "SUPPLEMENTARY_JOINT_DIAGNOSTIC_NOT_CERTIFICATE_REPORTED_SEMANTICS",
    "no_combined_or_cross_kind_coverage_comparison": True,
    "undercoverage_causes": ["directed_information_plugin_bias",
                             "share_conditional_design_other_channels_fixed"],
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
            # Supplementary joint bootstrap (dedicated deterministic rng; does not
            # disturb the share-conditional sequence above).
            rng_joint = np.random.default_rng([seed, n_samples, 21])
            jb = joint_composite_bootstrap(config, operating, execution,
                                           n_bootstrap=grid["n_joint_bootstrap"], rng=rng_joint)
            joint_iv = jb["composite_intervals"]["registered"]
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
                jiv = joint_iv[convention]
                jbounds = jiv["percentile_95"] if jiv else None
                jcovers = (bool(jbounds[0] <= exact_c <= jbounds[1])
                           if jbounds is not None else None)
                plugin_composite = float(fn(plugin)) if fn else None
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
                    "joint_sampling_interval": jbounds,
                    "joint_sampling_covers_exact": jcovers,
                    "reported_width": (bounds[1] - bounds[0]) if bounds else None,
                    "joint_width": (jbounds[1] - jbounds[0]) if jbounds else None,
                    "share_interval_covers_exact_share":
                        bool(decision[0] <= exact_shares[convention] <= decision[1]),
                    "diagnostic_plugin_composite": plugin_composite,
                    "diagnostic_abs_error":
                        abs(plugin_composite - exact_c) if plugin_composite is not None else None,
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
            # Two-cause attribution for share-conditional (above-limit) conventions.
            sc_miss_joint_cover = sum(
                1 for r in sampling_rows
                if r["share_conditional_sampling_covers_exact"] is False
                and r["joint_sampling_covers_exact"] is True)
            both_miss = sum(
                1 for r in sampling_rows
                if r["share_conditional_sampling_covers_exact"] is False
                and r["joint_sampling_covers_exact"] is False)
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
                "joint_sampling_coverage_rate":
                    sum(r["joint_sampling_covers_exact"] for r in rows
                        if r["joint_sampling_covers_exact"] is not None) / count,
                "mean_reported_width":
                    math.fsum(r["reported_width"] for r in rows
                              if r["reported_width"] is not None) / count,
                "mean_joint_width":
                    math.fsum(r["joint_width"] for r in rows
                              if r["joint_width"] is not None) / count,
                "share_interval_coverage_rate":
                    sum(r["share_interval_covers_exact_share"] for r in rows) / count,
                "diagnostic_mean_bias":
                    math.fsum(p - exact_composites[convention] for p in plugins) / count
                    if plugins else None,
                "diagnostic_rmse":
                    math.sqrt(math.fsum(e * e for e in errors) / count) if errors else None,
                "undercoverage_attribution": {
                    "share_conditional_miss_joint_cover_count": sc_miss_joint_cover,
                    "both_miss_count": both_miss,
                    "n_share_conditional_cells": len(sampling_rows),
                    "note": ("share-conditional miss but joint cover -> conditional-design "
                             "attributable; both miss -> residual plug-in bias (descriptive)"),
                },
            }
    return {
        "artifact_version": "R21-detection-study-v1",
        "status": "INTERNAL_FINITE_SAMPLE_STUDY_NOT_EXTERNAL_NOT_POWER",
        "predeclared_grid": grid,
        "coverage_semantics": dict(COVERAGE_SEMANTICS),
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
            "supersedes": "R20 detection study (read-only; coverage semantics now separated "
                          "and a joint-bootstrap diagnostic added)",
        },
        "interpretation": ("Descriptive finite-sample behavior of the declared data-driven "
                           "detection rule on one registered instance. Logical-envelope anchor "
                           "containment is NOT statistical coverage and is never compared with "
                           "sampling coverage. Above-limit sampling coverage is share-conditional "
                           "(other channels fixed at points); its under-coverage reflects both "
                           "plug-in bias and the conditional design, quantified by the joint "
                           "bootstrap. The joint diagnostic does not remove plug-in bias. "
                           "INDETERMINATE is an honest outcome, not a failure. Coverage rates "
                           "describe this grid only, not a universal guarantee."),
    }


def validate_result(result: dict) -> None:
    """Structural/boundary/anchor/governance checks only; no empirical pass conditions."""
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
    if result["coverage_semantics"] != COVERAGE_SEMANTICS:
        raise ValueError("coverage semantics must separate containment from coverage")
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
                blo, bhi = row["reported_composite_interval"]
                if not 0.0 <= blo <= bhi <= 1.0:
                    raise ValueError("reported composite interval out of bounds")
            if row["joint_sampling_interval"] is not None:
                jlo, jhi = row["joint_sampling_interval"]
                if not 0.0 <= jlo <= jhi <= 1.0:
                    raise ValueError("joint composite interval out of bounds")
    for n_key, conventions in result["aggregates"].items():
        for convention, _ in CONVENTIONS:
            agg = conventions[convention]
            if abs(sum(agg["status_rates"].values()) - 1.0) > 1e-9:
                raise ValueError("status rates must sum to one")
            for rate in agg["oracle_comparison_rates"].values():
                if not 0.0 <= rate <= 1.0:
                    raise ValueError("comparison rate out of range")
            for key in ("joint_sampling_coverage_rate", "share_interval_coverage_rate"):
                if not 0.0 <= agg[key] <= 1.0:
                    raise ValueError("coverage rate out of range")
            for key in ("logical_envelope_anchor_containment_rate",
                        "share_conditional_sampling_coverage_rate"):
                if agg[key] is not None and not 0.0 <= agg[key] <= 1.0:
                    raise ValueError("separated rate out of range")
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
    parser.add_argument("--out", default=str(HERE / "analysis_r21_detection_study.json"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = compute()
    validate_result(result)
    if args.check:
        saved = json.loads(Path(args.out).read_text(encoding="utf-8"))
        from analysis_r15_x5c_paired import compare_replay_json
        comparison = compare_replay_json(saved, result)
        if not comparison["passed"]:
            raise SystemExit("R21 detection study check FAILED: "
                             + "; ".join(comparison["differences"][:8]))
        print("R21 detection study check OK: predeclared 16-seed x {2048,8192} grid, "
              "separated envelope containment / share-conditional / joint coverage, "
              "data-driven rule, oracle evaluation only; "
              f"max abs float diff={comparison['max_abs_float_difference']:.3e}")
        return 0
    Path(args.out).write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                              encoding="utf-8")
    print("R21 detection study PASS (internal descriptive finite-sample study)")
    for n_key, conventions in result["aggregates"].items():
        for convention, _ in CONVENTIONS:
            agg = conventions[convention]
            env = agg["logical_envelope_anchor_containment_rate"]
            sc = agg["share_conditional_sampling_coverage_rate"]
            print(f"  n={n_key} {convention}: indet={agg['indeterminate_rate']:.3f} "
                  f"false_below={agg['false_below_rate']:.3f} false_above={agg['false_above_rate']:.3f} "
                  f"envelope_containment={env if env is None else round(env,3)} "
                  f"share_cond_coverage={sc if sc is None else round(sc,3)} "
                  f"joint_coverage={agg['joint_sampling_coverage_rate']:.3f} "
                  f"sc_miss_joint_cover={agg['undercoverage_attribution']['share_conditional_miss_joint_cover_count']}")
    print("[out]", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())