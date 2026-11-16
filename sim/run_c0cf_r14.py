#!/usr/bin/env python3
"""Generate/read-only-check the R14 same-environment C0-CF evidence package."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from autonomy_sim.c0_witness import evaluate_same_environment_c0


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/20261116_r14/c0cf_v2")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    out = Path(args.out).resolve()
    result = evaluate_same_environment_c0()
    if args.check:
        saved = json.loads((out / "analysis.json").read_text(encoding="utf-8"))
        assert saved == result, "C0-CF replay mismatch"
        print("C0-CF read-only replay OK:", result["overall_verdict"])
        return 0
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite {out}")
    out.mkdir(parents=True, exist_ok=True)
    prereg = {
        "type": "r14_c0cf_preregistration", "date": "2026-11-17",
        "spec": "SPEC_experiments v1.0 §10.7",
        "spec_sha256": sha(Path(__file__).resolve().parent / "SPEC_experiments.md"),
        "post_hoc_correction_after_math_review": True,
        "reason": "initial c0cf violated AX0, zero empowerment, degenerate goal space, and per-time-only law check",
        "scope": "nondegenerate same-environment full-trajectory constructive check; not legacy C0-DEMO and not external validation",
        "criteria": ["identical full (E,O,A) law", "Aepi=1 vs 0.5",
                     "positive composite separation", "observation-equivalent XOR Lambda=1 vs 0"],
        "T": 3, "w_epi": 0.2,
    }
    dump(out / "preregistration.json", prereg)
    dump(out / "analysis.json", result)
    with (out / "results.csv").open("w", newline="", encoding="utf-8") as fh:
        fields = ["arm", "a_via", "a_org", "a_goal", "a_exec", "a_epi", "composite",
                  "factual_p_y1", "lambda", "surgery_history"]
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerow({"arm": "faithful_plus_identity_endorsement", "a_via": result["a_via"],
                         "a_org": result["a_org_z1"], "a_goal": result["a_goal"],
                         "a_exec": result["a_exec_z1"], "a_epi": result["a_epi_z1"],
                         "composite": result["composite_z1"], "factual_p_y1": 0.5,
                         "lambda": 1.0, "surgery_history": 1})
        writer.writerow({"arm": "pinned_belief_plus_xor_endorsement", "a_via": result["a_via"],
                         "a_org": result["a_org_z2"], "a_goal": result["a_goal"],
                         "a_exec": result["a_exec_z2"], "a_epi": result["a_epi_z2"],
                         "composite": result["composite_z2"], "factual_p_y1": 0.5,
                         "lambda": 0.0, "surgery_history": 1})
    with (out / "verdict_table.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["criterion", "outcome", "evidence_type"])
        writer.writeheader()
        for name, passed in result["criteria"].items():
            writer.writerow({"criterion": name, "outcome": "CONFIRMED" if passed else "REFUTED",
                             "evidence_type": "constructive_implementation_check"})
        writer.writerow({"criterion": "OVERALL", "outcome": result["overall_verdict"],
                         "evidence_type": "constructive_implementation_check"})
    baseline = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip())
    manifest = {
        "type": "matrix_manifest", "matrix_id": "20261116_r14_c0cf_v2", "created": "2026-11-17",
        "spec_version": "SPEC_experiments v1.0 §10.7", "estimand_version": "R14-output-law-v1",
        "git_commit_baseline": baseline, "git_dirty": dirty, "frozen_release": False,
        "source_sha256": {"run_c0cf_r14.py": sha(Path(__file__).resolve()),
                          "src/autonomy_sim/c0_witness.py": sha(Path(__file__).resolve().parent / "src/autonomy_sim/c0_witness.py"),
                          "src/autonomy_sim/counterfactual.py": sha(Path(__file__).resolve().parent / "src/autonomy_sim/counterfactual.py")},
        "preregistration_sha256": sha(out / "preregistration.json"),
        "results_sha256": sha(out / "results.csv"),
        "verdict_table_sha256": sha(out / "verdict_table.csv"),
        "analysis_sha256": sha(out / "analysis.json"),
        "legacy_c0_demo_modified": False, "historical_4620_run_included": False,
        "supersedes": "runs/20261116_r14/c0cf (invalid nondegenerate-composite claims retained as a counterexample)",
        "external_construct_validation": False,
    }
    dump(out / "manifest.json", manifest)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("[out]", out)
    return 0 if result["overall_verdict"] == "CONFIRMED" else 1


if __name__ == "__main__":
    sys.exit(main())
