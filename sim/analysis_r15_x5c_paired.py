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
import math
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


def compare_replay_json(saved: object, computed: object, *, rel_tol: float = 1e-12,
                        abs_tol: float = 1e-12,
                        field_tolerances: dict | None = None) -> dict:
    """Compare a deterministic replay without demanding bitwise float equality.

    JSON types, object keys, list lengths, statuses, seeds, counts, and hashes
    remain exact.  Only leaves already serialized as JSON floats use isclose;
    non-finite floats and numeric type changes fail closed.

    R19 addendum: ``field_tolerances`` maps path substrings to declared
    per-field absolute tolerances for *auxiliary numerical analysis outputs*
    whose coordinates are non-unique or ill-conditioned (e.g. capacity-
    achieving input distributions on a flat optimal face).  A float leaf whose
    path contains a registered substring uses that tolerance instead of the
    default; immutable raw-log hashes, counts, and statuses are never float
    leaves and remain byte-exact.  The default None preserves R15--R18
    behavior bit-for-bit.
    """
    if not math.isfinite(rel_tol) or not math.isfinite(abs_tol) \
            or rel_tol < 0.0 or abs_tol < 0.0:
        raise ValueError("replay tolerances must be finite and non-negative")
    field_tolerances = dict(field_tolerances or {})
    for pattern, tolerance in field_tolerances.items():
        if not isinstance(pattern, str) or not pattern:
            raise ValueError("field tolerance patterns must be nonempty strings")
        if not math.isfinite(tolerance) or tolerance < 0.0:
            raise ValueError("field tolerances must be finite and non-negative")
    differences = []

    def visit(old: object, new: object, path: str) -> float:
        if type(old) is not type(new):
            differences.append(f"{path}: JSON type {type(old).__name__} != {type(new).__name__}")
            return 0.0
        if isinstance(old, float):
            if not math.isfinite(old) or not math.isfinite(new):
                differences.append(f"{path}: non-finite float")
                return math.inf
            delta = abs(old - new)
            leaf_abs_tol = abs_tol
            for pattern, tolerance in field_tolerances.items():
                if pattern in path:
                    leaf_abs_tol = max(leaf_abs_tol, tolerance)
            if not math.isclose(old, new, rel_tol=rel_tol, abs_tol=leaf_abs_tol):
                differences.append(f"{path}: {old!r} != {new!r} (abs diff {delta:.3e})")
            return delta
        if isinstance(old, dict):
            if old.keys() != new.keys():
                differences.append(f"{path}: object keys differ")
                return 0.0
            return max((visit(old[key], new[key], f"{path}.{key}") for key in old),
                       default=0.0)
        if isinstance(old, list):
            if len(old) != len(new):
                differences.append(f"{path}: list lengths {len(old)} != {len(new)}")
                return 0.0
            return max((visit(a, b, f"{path}[{index}]")
                        for index, (a, b) in enumerate(zip(old, new))), default=0.0)
        if old != new:
            differences.append(f"{path}: {old!r} != {new!r}")
        return 0.0

    max_abs = visit(saved, computed, "$")
    return {"passed": not differences, "max_abs_float_difference": max_abs,
            "float_rel_tol": rel_tol, "float_abs_tol": abs_tol,
            "field_tolerances": field_tolerances,
            "exact_non_float_leaves": True, "differences": differences}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(HERE / "analysis_r15_x5c_paired.json"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = compute()
    if args.check:
        saved = json.loads(Path(args.out).read_text(encoding="utf-8"))
        comparison = compare_replay_json(saved, result)
        if not comparison["passed"]:
            details = "; ".join(comparison["differences"][:8])
            raise SystemExit("R15 paired X5-c check FAILED: " + details)
        print(f"R15 paired X5-c check OK: {len(result['crosschecks'])} strata, "
              f"{result['overall']}, max abs float diff="
              f"{comparison['max_abs_float_difference']:.3e}")
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
