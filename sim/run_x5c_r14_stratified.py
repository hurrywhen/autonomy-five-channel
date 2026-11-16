#!/usr/bin/env python3
"""Canonical time-stratified R14 X5-c supplement; never overwrites the pooled run."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from autonomy_sim.counterfactual import (ThresholdEndorsementSCM,
                                         observation_equivalent_xor_witness,
                                         xor_endorsement_audit_from_observations)

ARMS = {"no_surgery": (0, 1.0), "history_without_output_effect": (1, 0.0),
        "graded_weak": (1, 0.35), "graded_strong": (1, 1.0)}
NOISE_SEEDS = {"gaussian": (910170, 910171, 910172),
               "logistic": (910180, 910181, 910182)}
CROSS_SEEDS = {"gaussian": 910190, "logistic": 910191}
T = 3
N_PER_T = 20000
N_CROSS = 4000
A = 0.35
SESOI = 0.01


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                          encoding="utf-8")


def compute():
    rows, estimates = [], {}
    for noise, seeds in NOISE_SEEDS.items():
        for arm, (surgery, b) in ARMS.items():
            for t, seed in enumerate(seeds, start=1):
                scm = ThresholdEndorsementSCM(noise, a=A, b=b)
                x, z, j = scm.simulate_contexts(n_contexts=N_PER_T, surgery=surgery, seed=seed)
                est = scm.evaluate(x, z, j)
                estimates[(noise, arm, t)] = est
                rows.append({"noise": noise, "arm": arm, "t": t, "a": A, "b": b,
                             "surgery": surgery, "n_contexts": N_PER_T, "seed": seed,
                             "lambda": est.lam, "mean_tv": est.mean_tv, "tv_se": est.tv_se,
                             "normal_95_halfwidth": est.normal_95_halfwidth,
                             "surgery_history": est.surgery_history})
    cross = []
    for noise, seed in CROSS_SEEDS.items():
        scm = ThresholdEndorsementSCM(noise, a=A, b=1.0)
        x, z, j = scm.simulate_contexts(n_contexts=N_CROSS, surgery=1, seed=seed)
        integrated = scm.evaluate(x, z, j)
        sampled = scm.shared_noise_disagreement(x, z, j, seed=seed + 100)
        combined = math.sqrt(integrated.tv_se ** 2 + sampled.tv_se ** 2)
        difference = abs(integrated.mean_tv - sampled.mean_tv)
        tolerance = max(4.0 * combined, 0.02)
        cross.append({"noise": noise, "t": 2, "n_contexts": N_CROSS,
                      "context_seed": seed, "downstream_seed": seed + 100,
                      "integrated_lambda": integrated.lam, "sampled_lambda": sampled.lam,
                      "abs_tv_difference": difference, "combined_se": combined,
                      "tolerance": tolerance, "passed": difference <= tolerance})
    criteria = {
        "C1_invariance_and_history_separation": all(
            abs(estimates[(n, arm, t)].lam - 1.0) <= 1e-12
            for n in NOISE_SEEDS for arm in ("no_surgery", "history_without_output_effect")
            for t in range(1, T + 1)),
        "C2_graded_range_and_order_identity": all(
            0.0 < estimates[(n, arm, t)].lam < 1.0
            for n in NOISE_SEEDS for arm in ("graded_weak", "graded_strong")
            for t in range(1, T + 1)) and all(
            estimates[(n, "graded_strong", t)].lam <= estimates[(n, "graded_weak", t)].lam + 1e-12
            for n in NOISE_SEEDS for t in range(1, T + 1)),
        "C5_independent_shared_noise_crosscheck": all(r["passed"] for r in cross),
    }
    noise_differences = []
    for arm in ARMS:
        for t in range(1, T + 1):
            noise_differences.append({"arm": arm, "t": t,
                "abs_lambda_difference": abs(estimates[("gaussian", arm, t)].lam
                                               - estimates[("logistic", arm, t)].lam)})
    d_noise = max(r["abs_lambda_difference"] for r in noise_differences)
    point_status = "MODEL_SENSITIVE" if d_noise > SESOI else "WITHIN_SESOI"
    witness = observation_equivalent_xor_witness((0, 1, 0, 1))
    criteria["C6_observationally_equivalent_scm_separation"] = (
        witness["identity_p_y1"] == witness["xor_p_y1"] == 0.5
        and witness["identity"].lam == 1.0 and witness["xor"].lam == 0.0
        and np.array_equal(witness["identity_passive_action"], witness["xor_passive_action"]))
    verdict = "CONFIRMED" if all(criteria.values()) else "REFUTED"
    return rows, cross, estimates, noise_differences, d_noise, point_status, witness, criteria, verdict


def prereg():
    return {
        "type": "r14_x5c_stratified_preregistration", "date": "2026-11-16",
        "spec": "SPEC_experiments v1.0 §10.6",
        "spec_sha256": sha(Path(__file__).resolve().parent / "SPEC_experiments.md"),
        "post_hoc_protocol_clarification": True,
        "reason": "pooled run lacked per-t records and nontrivial sensitivity consequence",
        "estimand_version": "R14-output-law-v1", "T": T, "n_contexts_per_t_arm_noise": N_PER_T,
        "audit_observation": "(X,Z,J); Y is not additionally conditioned on",
        "structural_equations": {"X": "Bernoulli(0.5)", "Z": "aX+bJ+U", "Y": "1{Z+V>=0}",
                                 "a": A, "abduction": "U=Z-aX-bJ", "action": "J=0"},
        "arms": ARMS, "noise_seeds": NOISE_SEEDS,
        "crosscheck": {"t": 2, "n": N_CROSS, "context_seeds": CROSS_SEEDS,
                       "downstream_seed_rule": "+100"},
        "noise_SESOI": SESOI,
        "sensitivity_consequence": "D_noise>SESOI => MODEL_SENSITIVE and report two-model band",
        "observation_equivalent_witness": "identity Y=U vs XOR Y=U xor 1; fair factual Y; fixed passive A",
        "outcome_scope": "explicit-SCM implementation check; no old ENV-0 or external validation upgrade",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/20261116_r14/x5c_stratified")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    out = Path(args.out).resolve()
    if args.check:
        rows, cross, estimates, differences, d_noise, status, witness, criteria, verdict = compute()
        saved_rows = list(csv.DictReader((out / "results.csv").open(encoding="utf-8")))
        assert len(rows) == len(saved_rows)
        for actual, saved in zip(rows, saved_rows):
            assert actual["noise"] == saved["noise"] and actual["arm"] == saved["arm"]
            assert actual["t"] == int(saved["t"])
            for key in ("lambda", "mean_tv", "tv_se", "normal_95_halfwidth"):
                assert abs(actual[key] - float(saved[key])) <= 1e-12
        analysis = json.loads((out / "analysis.json").read_text(encoding="utf-8"))
        assert analysis["overall_verdict"] == verdict and analysis["point_reading_status"] == status
        print(f"X5-c stratified replay OK: {len(rows)} rows, {verdict}, {status}, D={d_noise:.6f}")
        return 0
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite {out}")
    out.mkdir(parents=True, exist_ok=True)
    dump(out / "preregistration.json", prereg())  # before outcomes
    rows, cross, estimates, differences, d_noise, status, witness, criteria, verdict = compute()
    with (out / "results.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (out / "crosscheck_results.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(cross[0]))
        writer.writeheader()
        writer.writerows(cross)
    with (out / "verdict_table.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["criterion", "outcome", "evidence_type"])
        writer.writeheader()
        for name, passed in criteria.items():
            writer.writerow({"criterion": name, "outcome": "CONFIRMED" if passed else "REFUTED",
                             "evidence_type": "explicit_SCM_implementation_check"})
        writer.writerow({"criterion": "POINT_READING_SENSITIVITY", "outcome": status,
                         "evidence_type": "post_hoc_sensitivity_description"})
        writer.writerow({"criterion": "OVERALL_IMPLEMENTATION", "outcome": verdict,
                         "evidence_type": "explicit_SCM_implementation_check"})
    analysis = {
        "type": "r14_x5c_stratified_analysis", "date": "2026-11-16",
        "spec": "SPEC_experiments v1.0 §10.6", "estimand_version": "R14-output-law-v1",
        "T": T, "n_contexts_per_t_arm_noise": N_PER_T,
        "results": rows, "crosscheck": cross, "noise_differences": differences,
        "D_noise": d_noise, "noise_SESOI": SESOI, "point_reading_status": status,
        "observation_equivalent_witness": {
            "identity_lambda": witness["identity"].lam, "xor_lambda": witness["xor"].lam,
            "identity_p_y1": witness["identity_p_y1"], "xor_p_y1": witness["xor_p_y1"],
            "passive_actions_identical": True,
        },
        "criteria": criteria, "overall_verdict": verdict,
        "two_model_band_by_arm_t": [
            {"arm": arm, "t": t,
             "lambda_min": min(estimates[("gaussian", arm, t)].lam,
                               estimates[("logistic", arm, t)].lam),
             "lambda_max": max(estimates[("gaussian", arm, t)].lam,
                               estimates[("logistic", arm, t)].lam)}
            for arm in ARMS for t in range(1, T + 1)],
        "historical_archives_modified": False, "old_env0_upgraded": False,
        "external_construct_validation": False,
    }
    dump(out / "analysis.json", analysis)
    baseline = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip())
    source = [Path(__file__).resolve(),
              Path(__file__).resolve().parent / "src/autonomy_sim/counterfactual.py",
              Path(__file__).resolve().parent / "src/autonomy_sim/rng.py"]
    manifest = {
        "type": "matrix_manifest", "matrix_id": "20261116_r14_x5c_stratified",
        "created": "2026-11-16", "spec_version": "SPEC_experiments v1.0 §10.6",
        "estimand_version": "R14-output-law-v1", "audit_observation": "(X,Z,J)",
        "T": T, "n_contexts_per_t_arm_noise": N_PER_T,
        "n_contexts_total": sum(r["n_contexts"] for r in rows),
        "n_crosscheck_contexts": sum(r["n_contexts"] for r in cross),
        "git_commit_baseline": baseline, "git_dirty": dirty, "frozen_release": False,
        "source_sha256": {str(p.relative_to(Path(__file__).resolve().parent)): sha(p) for p in source},
        "preregistration_sha256": sha(out / "preregistration.json"),
        "results_sha256": sha(out / "results.csv"),
        "crosscheck_results_sha256": sha(out / "crosscheck_results.csv"),
        "verdict_table_sha256": sha(out / "verdict_table.csv"),
        "analysis_sha256": sha(out / "analysis.json"),
        "surgery_map": "J=1 any registered surgery; action removes all J and preserves U,V",
        "random_streams": "within-cell independent U/X per t; cross-arm common random numbers; independent downstream V stream seed+100",
        "historical_4620_run_included": False, "old_env0_upgraded": False,
        "pooled_run_rewritten": False, "external_construct_validation": False,
    }
    dump(out / "manifest.json", manifest)
    print(f"rows={len(rows)} D_noise={d_noise:.9f} point_status={status} overall={verdict}")
    for arm in ARMS:
        print(arm, [(r["arm"], r["t"], round(r["lambda_min"], 6), round(r["lambda_max"], 6))
                    for r in analysis["two_model_band_by_arm_t"] if r["arm"] == arm])
    print("[out]", out)
    return 0 if verdict == "CONFIRMED" else 1


if __name__ == "__main__":
    sys.exit(main())
