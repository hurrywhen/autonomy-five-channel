#!/usr/bin/env python3
"""R15 paired-difference audit of the two R14 X5-c stratified cross-checks.

The R14 artifacts are read-only.  This new artifact preserves their numerical
estimates but supersedes the unpaired combined-SE interpretation for current
reporting: integrated and sampled values share X,Z,J, so their per-context
differences determine the SE.  Only downstream V uses a new seed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "src"))

from autonomy_sim.counterfactual import ThresholdEndorsementSCM  # noqa: E402
from autonomy_sim.stats import paired_mean_se  # noqa: E402
from run_x5c_r14_stratified import A, CROSS_SEEDS, N_CROSS  # noqa: E402


def compute() -> dict:
    rows = []
    for noise, seed in CROSS_SEEDS.items():
        scm = ThresholdEndorsementSCM(noise, a=A, b=1.0)
        x, z, j = scm.simulate_contexts(n_contexts=N_CROSS, surgery=1, seed=seed)
        integrated_values = scm.tv_per_context(x, z, j)
        sampled_values = scm.shared_noise_disagreement_per_context(x, z, j, seed=seed + 100)
        paired = paired_mean_se(integrated_values - sampled_values)
        integrated = scm.evaluate(x, z, j)
        sampled = scm.shared_noise_disagreement(x, z, j, seed=seed + 100)
        tolerance = max(4.0 * paired["paired_se"], 0.02)
        rows.append({"noise": noise, "n_contexts": N_CROSS,
                     "context_seed": seed, "downstream_seed": seed + 100,
                     "integrated_lambda": integrated.lam, "sampled_lambda": sampled.lam,
                     **paired, "tolerance": tolerance,
                     "passed": paired["abs_mean_difference"] <= tolerance})
    return {
        "artifact_version": "R15-x5c-paired-v1",
        "analysis_status": "POST_HOC_SUPERSEDED_REPORTING_AUDIT",
        "preregistered": False,
        "source_protocol": "R14 x5c_stratified contexts and downstream seeds; current-source recomputation",
        "context_relationship": "integrated and sampled estimates share X,Z,J; only downstream V is independent",
        "se_method": "sample standard error of per-context integrated-TV minus sampled-|Y-Y0| differences",
        "tolerance_status": "post hoc inherited 4*SE form and 0.02 floor after paired-SE correction; not a preregistered R15 criterion",
        "historical_r14_files_modified": False,
        "legacy_combined_se_status": "retained in R14 artifacts but superseded for R15 inferential reporting",
        "external_construct_validation": False,
        "crosschecks": rows,
        "overall": "POST_HOC_PASS" if all(row["passed"] for row in rows) else "POST_HOC_FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(HERE / "analysis_r15_x5c_paired.json"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = compute()
    if args.check:
        saved = json.loads(Path(args.out).read_text(encoding="utf-8"))
        if saved != result:
            raise SystemExit("R15 paired X5-c check FAILED")
        print(f"R15 paired X5-c check OK: {len(result['crosschecks'])} strata, {result['overall']}")
        return 0
    Path(args.out).write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                              encoding="utf-8")
    for row in result["crosschecks"]:
        print(row["noise"], "abs_diff=", row["abs_mean_difference"],
              "paired_se=", row["paired_se"], "tolerance=", row["tolerance"],
              "passed=", row["passed"])
    print("[out]", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
