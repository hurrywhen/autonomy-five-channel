#!/usr/bin/env python3
"""R15 read-only reporting audit: tau-b, ties, scenario strata and SESOI scale.

No historical manifest/result/verdict is modified.  The script recomputes only
composite values from saved component bundles and writes a new R15 artifact.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))

from autonomy_sim.aggregate import composite_A  # noqa: E402
from autonomy_sim.stats import kendall_tau_b  # noqa: E402
from analysis_weights_sigma import WEIGHT_CONFIGS, load_arms  # noqa: E402


def _tau_payload(base, values):
    result = kendall_tau_b(base, values)
    result["interpretation"] = ("undefined_constant_or_zero_denominator"
                                if math.isnan(result["tau_b"]) else "descriptive_tau_b")
    return result


def compute(root: str) -> dict:
    arms = [a for a in load_arms(root) if a["group"] == "main"]
    base = [composite_A(a["a_via"], a["comps"], WEIGHT_CONFIGS["equal"], sigma=a["sigma"])
            for a in arms]
    weights = {}
    for name, weights_vector in WEIGHT_CONFIGS.items():
        values = [composite_A(a["a_via"], a["comps"], weights_vector, sigma=a["sigma"])
                  for a in arms]
        by_scenario = {}
        for scenario in sorted({a["scenario"] for a in arms}):
            indices = [i for i, a in enumerate(arms) if a["scenario"] == scenario]
            by_scenario[scenario] = _tau_payload([base[i] for i in indices],
                                                  [values[i] for i in indices])
        weights[name] = {"overall": _tau_payload(base, values),
                         "by_scenario": by_scenario}
    return {
        "artifact_version": "R15-statistics-v1",
        "source_archive": "runs/20261017_full (read-only historical component bundles)",
        "n_main_arms": len(arms),
        "statistic": "Kendall tau-b; exact ties in either coordinate; NaN for zero denominator",
        "weights": weights,
        "sesoi_error_scale": {
            "registered_numeric_sesoi": 0.01,
            "largest_reported_sample_mode_absolute_error": 0.0096,
            "ratio_sesoi_to_error": 0.01 / 0.0096,
            "interpretation": ("numeric decision threshold only; not an externally calibrated "
                               "domain-important effect or an independent error distribution"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=os.path.join(HERE, "runs", "20261017_full"))
    parser.add_argument("--out", default=os.path.join(HERE, "analysis_r15_statistics.json"))
    parser.add_argument("--check", action="store_true",
                        help="compare against --out without writing")
    args = parser.parse_args()
    result = compute(args.root)
    if args.check:
        with open(args.out, encoding="utf-8") as handle:
            saved = json.load(handle)
        if saved != result:
            raise SystemExit("R15 statistics read-only check FAILED")
        print(f"R15 statistics read-only check OK: {result['n_main_arms']} historical arms")
        return 0
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=1, allow_nan=True)
        handle.write("\n")
    for name, record in result["weights"].items():
        overall = record["overall"]
        scenario_values = [v["tau_b"] for v in record["by_scenario"].values()
                           if not math.isnan(v["tau_b"])]
        print(f"{name:12s} overall={overall['tau_b']:.6f} "
              f"scenario_min={min(scenario_values):.6f} ties_x={overall['ties_x_only']} "
              f"ties_y={overall['ties_y_only']} ties_both={overall['ties_both']}")
    print(f"[write] {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
