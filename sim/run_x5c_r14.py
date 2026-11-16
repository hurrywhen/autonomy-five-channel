#!/usr/bin/env python3
"""Execute or check the preregistered R14 X5-c counterfactual-Lambda arms.

Initial generation:
    python3 run_x5c_r14.py --out runs/20261116_r14/x5c
Read-only deterministic replay:
    python3 run_x5c_r14.py --out runs/20261116_r14/x5c --check

The preregistration file is written before any outcome is computed.  Existing
nonempty output directories are never overwritten: --check recomputes in
memory and compares the numeric records instead.  No historical run is read or
modified.  This is an explicit-SCM implementation/sensitivity study, not an
independent-substrate or construct-validation experiment.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
from autonomy_sim.counterfactual import ThresholdEndorsementSCM, xor_endorsement_audit  # noqa: E402

DATE = "2026-11-16"
SPEC_VERSION = "SPEC_experiments v1.0 §10.3–10.4"
ARMS = {
    "no_surgery": {"surgery": 0, "b": 1.0},
    "history_without_output_effect": {"surgery": 1, "b": 0.0},
    "graded_weak": {"surgery": 1, "b": 0.35},
    "graded_strong": {"surgery": 1, "b": 1.0},
}
NOISES = {"gaussian": 910160, "logistic": 910161}
CROSSCHECK_SEEDS = {"gaussian": 910162, "logistic": 910163}
N_CONTEXTS = 20000
N_CROSSCHECK = 4000
A_COEFF = 0.35


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, obj) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2, allow_nan=False)
        fh.write("\n")


def compute_records():
    rows = []
    estimates = {}
    for noise, seed in NOISES.items():
        for arm, config in ARMS.items():
            scm = ThresholdEndorsementSCM(noise, a=A_COEFF, b=config["b"])
            x, z, j = scm.simulate_contexts(n_contexts=N_CONTEXTS,
                                            surgery=config["surgery"], seed=seed)
            estimate = scm.evaluate(x, z, j)
            estimates[(noise, arm)] = estimate
            rows.append({
                "noise": noise, "arm": arm, "a": A_COEFF, "b": config["b"],
                "surgery": config["surgery"], "n_contexts": N_CONTEXTS, "seed": seed,
                "lambda": estimate.lam, "mean_tv": estimate.mean_tv,
                "tv_se": estimate.tv_se, "normal_95_halfwidth": estimate.normal_95_halfwidth,
                "surgery_history": estimate.surgery_history,
            })
    xor_u = np.array([0, 1])
    xor = {
        "implanted": xor_endorsement_audit(xor_u, np.ones(2, dtype=int)),
        "endogenous": xor_endorsement_audit(xor_u, np.zeros(2, dtype=int)),
    }
    crosscheck = []
    for noise, seed in CROSSCHECK_SEEDS.items():
        scm = ThresholdEndorsementSCM(noise, a=A_COEFF, b=ARMS["graded_strong"]["b"])
        x, z, j = scm.simulate_contexts(n_contexts=N_CROSSCHECK, surgery=1, seed=seed)
        integrated = scm.evaluate(x, z, j)
        sampled = scm.shared_noise_disagreement(x, z, j, seed=seed + 100)
        combined_se = math.sqrt(integrated.tv_se ** 2 + sampled.tv_se ** 2)
        difference = abs(integrated.mean_tv - sampled.mean_tv)
        tolerance = max(4.0 * combined_se, 0.02)
        crosscheck.append({
            "noise": noise, "n_contexts": N_CROSSCHECK, "context_seed": seed,
            "downstream_seed": seed + 100,
            "integrated_lambda": integrated.lam, "sampled_lambda": sampled.lam,
            "integrated_tv_se": integrated.tv_se, "sampled_tv_se": sampled.tv_se,
            "abs_tv_difference": difference, "combined_se": combined_se,
            "tolerance": tolerance, "passed": difference <= tolerance,
        })
    criteria = {}
    criteria["C1_invariance_and_history_separation"] = all(
        abs(estimates[(noise, arm)].lam - 1.0) <= 1e-12
        for noise in NOISES for arm in ("no_surgery", "history_without_output_effect")
    ) and all(estimates[(noise, "history_without_output_effect")].surgery_history == 1
              for noise in NOISES)
    criteria["C2_graded_nondegenerate_and_ordered"] = all(
        0.0 < estimates[(noise, arm)].lam < 1.0
        for noise in NOISES for arm in ("graded_weak", "graded_strong")
    ) and all(estimates[(noise, "graded_strong")].lam
              <= estimates[(noise, "graded_weak")].lam + 1e-12 for noise in NOISES)
    criteria["C3_no_noise_model_direction_flip"] = all(
        estimates[(noise, "graded_strong")].lam
        <= estimates[(noise, "graded_weak")].lam + 1e-12 for noise in NOISES)
    criteria["C4_xor_analytic_boundary"] = (
        xor["implanted"].lam == 0.0 and xor["endogenous"].lam == 1.0
        and xor["implanted"].surgery_history == 1
        and xor["endogenous"].surgery_history == 0)
    criteria["C5_independent_shared_noise_crosscheck"] = all(r["passed"] for r in crosscheck)
    verdict = "CONFIRMED" if all(criteria.values()) else "REFUTED"
    return rows, crosscheck, xor, estimates, criteria, verdict


def preregistration(root: Path) -> dict:
    spec = root.parents[2] / "SPEC_experiments.md"
    # When --out is the registered path, parents[2] is sim/.  Custom output
    # directories fall back to the script's own sim/ directory.
    if not spec.exists():
        spec = Path(__file__).resolve().parent / "SPEC_experiments.md"
    return {
        "type": "r14_x5c_preregistration",
        "date": DATE,
        "spec": SPEC_VERSION,
        "spec_sha256": sha256(spec),
        "structural_equations": {
            "X": "Bernoulli(0.5), independent across contexts",
            "Z": "a*X + b*J + U", "Y": "1{Z+V>=0}", "a": A_COEFF,
            "abduction": "U=Z-a*X-b*J", "action": "J=0; Z0=a*X+U",
            "prediction": "actual and no-surgery Bernoulli laws under shared V",
        },
        "noise_models": {"gaussian": "U,V iid N(0,1)",
                         "logistic": "U,V iid standard logistic"},
        "arms": ARMS, "noises_and_seeds": NOISES, "n_contexts_per_arm": N_CONTEXTS,
        "crosscheck": {"arm": "graded_strong", "n_contexts": N_CROSSCHECK,
                       "context_seeds": CROSSCHECK_SEEDS,
                       "downstream_seed_rule": "context_seed+100",
                       "tolerance": "max(4*sqrt(se_integrated^2+se_sampled^2),0.02)"},
        "xor_boundary": "Y=U xor J; U~Bernoulli(0.5); J in {0,1}",
        "criteria": {
            "C1": "no-surgery and history-without-output-effect Lambda=1 (tol 1e-12)",
            "C2": "graded Lambda in (0,1), strong<=weak within each noise model",
            "C3": "no strong/weak direction flip across either noise model",
            "C4": "XOR implanted/endogenous Lambda=0/1 with independent enumeration",
            "C5": "integrated/shared-noise TV agreement under registered tolerance",
        },
        "outcome_data_seen_before_registration": False,
        "scope": "explicit-SCM implementation and sensitivity only; no external validation",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/20261116_r14/x5c")
    ap.add_argument("--check", action="store_true", help="read-only deterministic replay")
    args = ap.parse_args()
    out = Path(args.out).resolve()
    if args.check:
        expected_rows = list(csv.DictReader((out / "results.csv").open(encoding="utf-8")))
        rows, crosscheck, xor, estimates, criteria, verdict = compute_records()
        for actual, saved in zip(rows, expected_rows):
            for key in ("lambda", "mean_tv", "tv_se", "normal_95_halfwidth"):
                if abs(actual[key] - float(saved[key])) > 1e-12:
                    raise AssertionError(f"replay mismatch {actual['noise']}/{actual['arm']}:{key}")
        saved_verdict = (out / "analysis.json").read_text(encoding="utf-8")
        if json.loads(saved_verdict)["overall_verdict"] != verdict:
            raise AssertionError("overall verdict mismatch")
        print(f"X5-c read-only replay OK: {len(rows)} arms, overall={verdict}")
        return 0
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty new-run directory: {out}")
    out.mkdir(parents=True, exist_ok=True)
    prereg = preregistration(out)
    write_json(out / "preregistration.json", prereg)  # before outcome computation

    rows, crosscheck, xor, estimates, criteria, verdict = compute_records()
    fields = list(rows[0])
    with (out / "results.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    with (out / "crosscheck_results.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(crosscheck[0]))
        writer.writeheader()
        writer.writerows(crosscheck)
    with (out / "verdict_table.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["criterion", "outcome", "evidence_type"])
        writer.writeheader()
        for name, passed in criteria.items():
            writer.writerow({"criterion": name,
                             "outcome": "CONFIRMED" if passed else "REFUTED",
                             "evidence_type": "explicit_SCM_implementation_check"})
        writer.writerow({"criterion": "OVERALL", "outcome": verdict,
                         "evidence_type": "explicit_SCM_implementation_check"})
    analysis = {
        "type": "r14_x5c_analysis", "date": DATE, "spec": SPEC_VERSION,
        "results": rows, "crosscheck": crosscheck,
        "xor": {k: vars(v) for k, v in xor.items()},
        "criteria": criteria, "overall_verdict": verdict,
        "noise_model_max_abs_lambda_difference_by_arm": {
            arm: max(abs(estimates[("gaussian", arm)].lam
                         - estimates[("logistic", arm)].lam) for _ in [0])
            for arm in ARMS
        },
        "independent_substrate_validation": False,
        "historical_archives_modified": False,
    }
    write_json(out / "analysis.json", analysis)
    baseline = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    source_paths = [Path(__file__).resolve(),
                    Path(__file__).resolve().parent / "src/autonomy_sim/counterfactual.py",
                    Path(__file__).resolve().parent / "src/autonomy_sim/rng.py"]
    manifest = {
        "type": "matrix_manifest", "matrix_id": "20261116_r14_x5c", "created": DATE,
        "spec_version": SPEC_VERSION, "git_commit_baseline": baseline,
        "frozen_release": False,
        "note": "baseline commit plus working-tree source hashes; not a frozen public release",
        "source_sha256": {str(p.relative_to(Path(__file__).resolve().parent)): sha256(p)
                          for p in source_paths},
        "preregistration_sha256": sha256(out / "preregistration.json"),
        "results_sha256": sha256(out / "results.csv"),
        "crosscheck_results_sha256": sha256(out / "crosscheck_results.csv"),
        "verdict_table_sha256": sha256(out / "verdict_table.csv"),
        "analysis_sha256": sha256(out / "analysis.json"),
        "n_contexts": sum(r["n_contexts"] for r in rows),
        "n_crosscheck_contexts": sum(r["n_contexts"] for r in crosscheck),
        "independent_random_units": "within-cell independent base X,U; cross-arm common random numbers; CDF-integrated downstream noise",
        "seed_rule": "registered PCG64 seeds in preregistration.json",
        "historical_4620_run_included": False,
    }
    write_json(out / "manifest.json", manifest)
    for row in rows:
        print(f"{row['noise']:8s} {row['arm']:31s} Lambda={row['lambda']:.9f} "
              f"SE(TV)={row['tv_se']:.6f}")
    print("Cross-check:", [(r["noise"], round(r["abs_tv_difference"], 6), r["passed"])
                           for r in crosscheck])
    print("Overall:", verdict)
    print("[out]", out)
    return 0 if verdict == "CONFIRMED" else 1


if __name__ == "__main__":
    sys.exit(main())
