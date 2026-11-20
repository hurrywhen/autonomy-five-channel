#!/usr/bin/env python3
"""R17 exact log-domain weight regions for the geometric bookkeeping aggregate.

This is a read-only, post hoc descriptive analysis of historical component
bundles.  It does not turn normalized channels into ratio scales or causal
attributions.  The closed simplex is a sensitivity relaxation: the
representation theorem itself uses strictly positive weights.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "src"))

from analysis_weights_sigma import ORDER, load_arms  # noqa: E402
from analysis_r15_x5c_paired import compare_replay_json  # noqa: E402

TOL = 1e-12


def _unit(value: float, label: str) -> float:
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{label} must be finite and in [0,1]")
    return value


def _profile(components, a_via) -> tuple[tuple[float, ...], float]:
    values = tuple(_unit(value, "component") for value in components)
    if not values:
        raise ValueError("at least one component is required")
    return values, _unit(a_via, "a_via")


def geometric_log_bounds(components, a_via) -> dict:
    """Exact inf/sup of log(A) over the closed weight simplex, if all x_i>0.

    log A = log(v) + sum_i w_i log(x_i).  Linear functionals attain their
    closed-simplex extrema at vertices.  Zero coordinates are handled
    separately because the log domain is then undefined.
    """
    values, viability = _profile(components, a_via)
    if viability == 0.0 or any(value == 0.0 for value in values):
        return {"status": "ZERO_COMPONENT_OR_GATE_SEPARATE", "n": len(values)}
    logs = [math.log(value) for value in values]
    low = math.log(viability) + min(logs)
    high = math.log(viability) + max(logs)
    return {
        "status": "FINITE",
        "log_min": low,
        "log_max": high,
        "composite_min": math.exp(low),
        "composite_max": math.exp(high),
        "minimizing_vertex": logs.index(min(logs)),
        "maximizing_vertex": logs.index(max(logs)),
        "note": "closed-simplex sensitivity bounds; interior weights have the same inf/sup",
    }


def pairwise_log_damage(before_components, before_via,
                        after_components, after_via) -> dict:
    """Return the exact halfspace for log(A_before/A_after) and its bounds.

    D(w) = c + sum_i d_i w_i, c=log(v0/v1), d_i=log(x0_i/x1_i).
    Positive damage means that the after-profile has the smaller geometric
    bookkeeping composite.  No causal-intervention interpretation is attached.
    """
    before, v0 = _profile(before_components, before_via)
    after, v1 = _profile(after_components, after_via)
    if len(before) != len(after):
        raise ValueError("component lengths differ")
    if (v0 == 0.0 or v1 == 0.0
            or any(x == 0.0 for x in before + after)):
        return {"status": "ZERO_COMPONENT_OR_GATE_SEPARATE"}
    intercept = math.log(v0) - math.log(v1)
    slopes = tuple(math.log(x0) - math.log(x1) for x0, x1 in zip(before, after))
    vertices = tuple(intercept + slope for slope in slopes)
    low, high = min(vertices), max(vertices)
    if high - low <= TOL and abs(low) <= TOL:
        verdict = "TIED_ON_CLOSED_SIMPLEX"
    elif low > TOL:
        verdict = "POSITIVE_DAMAGE_FOR_ALL_WEIGHTS"
    elif high < -TOL:
        verdict = "NEGATIVE_DAMAGE_FOR_ALL_WEIGHTS"
    elif low >= -TOL:
        verdict = "NONNEGATIVE_DAMAGE_WITH_BOUNDARY_TIES"
    elif high <= TOL:
        verdict = "NONPOSITIVE_DAMAGE_WITH_BOUNDARY_TIES"
    else:
        verdict = "WEIGHT_DEPENDENT"
    return {
        "status": "FINITE",
        "intercept": intercept,
        "slopes": slopes,
        "vertex_damage_values": vertices,
        "damage_log_min": low,
        "damage_log_max": high,
        "verdict": verdict,
        "nonnegative_damage_region": {
            "weights": "w_i>=0, sum_i w_i=1 (closed sensitivity simplex)",
            "inequality": "intercept + sum_i slopes[i]*w_i >= 0",
            "representation_theorem_interior": "w_i>0, sum_i w_i=1",
        },
    }


def compute(root: Path) -> dict:
    arms = [a for a in load_arms(str(root))
            if a["group"] == "main" and a["sigma"] == 1.0]
    cells = {}
    for arm in arms:
        key = (arm["scenario"], arm["config"], arm["rep"])
        cells.setdefault(key, []).append(arm)

    comparisons = []
    zero_excluded = 0
    bound_rows = {}
    for (scenario, config, rep), rows in sorted(cells.items()):
        rows.sort(key=lambda row: row["arm"])
        for arm in rows:
            signature = (arm["scenario"], arm["comps"], arm["a_via"])
            if signature not in bound_rows:
                bound = geometric_log_bounds(arm["comps"], arm["a_via"])
                if bound["status"] == "FINITE":
                    bound_rows[signature] = {
                        "scenario": scenario, **bound,
                    }
                else:
                    zero_excluded += 1
        for before, after in zip(rows, rows[1:]):
            contrast = pairwise_log_damage(
                before["comps"], before["a_via"], after["comps"], after["a_via"])
            if contrast["status"] != "FINITE":
                zero_excluded += 1
                continue
            comparisons.append({
                "scenario": scenario, "config": config, "rep": rep,
                "before_arm": before["arm"], "after_arm": after["arm"],
                **contrast,
                "slopes": list(contrast["slopes"]),
                "vertex_damage_values": list(contrast["vertex_damage_values"]),
            })

    # Identical deterministic replays and equal-content cells share a contrast.
    unique = {}
    for row in comparisons:
        signature = (row["scenario"], row["intercept"], tuple(row["slopes"]))
        unique.setdefault(signature, row)
    unique_rows = list(unique.values())
    verdicts = {}
    for row in unique_rows:
        verdicts[row["verdict"]] = verdicts.get(row["verdict"], 0) + 1
    per_scenario = {}
    for row in unique_rows:
        scenario = row["scenario"]
        entry = per_scenario.setdefault(scenario, {})
        entry[row["verdict"]] = entry.get(row["verdict"], 0) + 1

    return {
        "artifact_version": "R17-weight-regions-v1",
        "analysis_status": "POST_HOC_DESCRIPTIVE_CLOSED_SIMPLEX_BOUNDS",
        "source_archive": "runs/20261017_full (read-only historical component bundles)",
        "external_construct_validation": False,
        "causal_attribution": False,
        "ratio_scale_established": False,
        "statistical_power_or_independent_replicates": False,
        "scope": {
            "aggregate": "sigma=1 geometric bookkeeping form only",
            "weight_domain": "closed simplex for sensitivity; strictly positive interior for representation theorem",
            "nested_and_deterministic_records": "deduplicated by scenario/intercept/slope for headline counts",
            "zero_components": "excluded from log-domain contrasts and counted separately",
        },
        "n_main_sigma1_arms": len(arms),
        "n_cells": len(cells),
        "n_finite_pairwise_comparisons_before_dedup": len(comparisons),
        "n_unique_component_bounds": len(bound_rows),
        "n_zero_or_log_undefined_exclusions": zero_excluded,
        "n_unique_contrasts": len(unique_rows),
        "unique_contrast_verdicts": verdicts,
        "unique_contrast_verdicts_by_scenario": per_scenario,
        "component_bounds": list(bound_rows.values()),
        "contrasts": unique_rows,
        "interpretation": (
            "Each nonnegative-damage region is an exact simplex-halfspace intersection. "
            "These are bookkeeping conclusions under the selected geometric aggregator, "
            "not ratio-scale, causal-attribution, or external-validation claims."
        ),
    }


def validate_result(result: dict) -> None:
    """Independent small anchors; a matching saved JSON alone is insufficient."""
    bounds = geometric_log_bounds((0.5, 0.25), 0.8)
    if not (math.isclose(bounds["composite_min"], 0.2, abs_tol=1e-14)
            and math.isclose(bounds["composite_max"], 0.4, abs_tol=1e-14)):
        raise ValueError("closed-simplex component bounds anchor failed")
    robust = pairwise_log_damage((0.8, 0.6), 1.0, (0.4, 0.5), 1.0)
    if robust["verdict"] != "POSITIVE_DAMAGE_FOR_ALL_WEIGHTS":
        raise ValueError("robust damage anchor failed")
    dependent = pairwise_log_damage((0.8, 0.2), 1.0, (0.4, 0.6), 1.0)
    if dependent["verdict"] != "WEIGHT_DEPENDENT":
        raise ValueError("weight-dependent anchor failed")
    zero = pairwise_log_damage((0.8, 0.0), 1.0, (0.4, 0.5), 1.0)
    if zero["status"] != "ZERO_COMPONENT_OR_GATE_SEPARATE":
        raise ValueError("zero-component fail-closed anchor failed")
    if result["n_unique_contrasts"] != sum(result["unique_contrast_verdicts"].values()):
        raise ValueError("contrast tally mismatch")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(HERE / "runs/20261017_full"))
    parser.add_argument("--out", default=str(HERE / "analysis_r17_weight_regions.json"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = compute(Path(args.root))
    validate_result(result)
    if args.check:
        saved = json.loads(Path(args.out).read_text(encoding="utf-8"))
        comparison = compare_replay_json(saved, result)
        if not comparison["passed"]:
            raise SystemExit("R17 weight-region check FAILED: "
                             + "; ".join(comparison["differences"][:8]))
        print(f"R17 weight-region check OK: {result['n_unique_contrasts']} unique contrasts, "
              f"{result['unique_contrast_verdicts']}; max abs float diff="
              f"{comparison['max_abs_float_difference']:.3e}")
        return 0
    Path(args.out).write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                              encoding="utf-8")
    print(f"R17 weight-region exact bounds PASS: {result['n_unique_contrasts']} unique contrasts")
    print("[out]", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
