#!/usr/bin/env python3
"""Deterministic R14 counterexample/optimization analysis (no simulation runs).

Writes analysis_r14_math.json.  These are algebraic witnesses and numerical
optimization cross-checks, not independent empirical data.
"""
import hashlib
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from autonomy_sim.attack import (grid_search_2d, linear_fraction_objective,
                                 solve_linear_fraction_attack,
                                 symbolic_symmetric_kkt_certificate)


def main():
    w = c = s = (0.5, 0.5)
    # The review example has c=s=(1,1); w=(0.5,0.5).
    c = s = (1.0, 1.0)
    B = 0.5
    exact = solve_linear_fraction_attack(w, c, s, B)
    grid = grid_search_2d(w, c, s, B, n=201)
    symbolic = symbolic_symmetric_kkt_certificate()
    var_theta, var_noise = 100.0, 0.01
    h = 0.5 * math.log(2.0 * math.pi * math.e * var_theta)
    mutual = 0.5 * math.log1p(var_theta / var_noise)
    x, y = (0.9, 0.2), (0.5, 0.6)
    result = {
        "meta": {"date": "2026-11-16", "spec": "SPEC_experiments v1.0 §10.1–10.2",
                 "evidence_type": "deterministic algebraic witnesses; not independent data"},
        "t1b_zero_lambda_ref": {"fidelity": 1.0, "endorsement_consistency": 1.0,
                                "lambda_ref": 0.0, "a_ref": 0.0, "composite": 0.0},
        "org_counterexample": {
            "before": {"f_int": 0.1, "f_ext": 1.0, "a_org": 0.1 / 1.1},
            "after": {"f_int": 1.0, "f_ext": 0.1, "a_org": 1.0 / 1.1},
            "correct_strict_loss_premise": "Fext_after/Fint_after > Fext_before/Fint_before",
        },
        "goal_counterexample": {"dc": 1.0, "d0": 0.8, "d1": 0.1,
                                "a_goal0": 0.2, "a_goal1": 0.9},
        "linear_fraction_attack": {
            "parameters": {"w": w, "c": c, "s": s, "B": B},
            "concentrated": {"x": (0.5, 0.0),
                             "objective": linear_fraction_objective((0.5, 0.0), w, s)},
            "spread": {"x": (0.25, 0.25),
                       "objective": linear_fraction_objective((0.25, 0.25), w, s)},
            "exact": {"x": exact["x"], "objective": exact["objective"],
                      "optimal_channels": exact["optimal_channels"],
                      "proof": exact["proof"]},
            "grid": grid,
            "symbolic": {"stationary_x": symbolic["stationary_x"],
                         "gradient": symbolic["gradient"],
                         "budget_multiplier": symbolic["budget_multiplier"],
                         "hessian_diagonal": symbolic["hessian_diagonal"],
                         "stationary_objective": symbolic["stationary_objective"],
                         "stationary_is_local_maximum": symbolic["stationary_is_local_maximum"]},
        },
        "continuous_entropy_exclusion": {
            "theta_variance": var_theta, "noise_variance": var_noise,
            "h_theta_nats": h, "I_M_theta_nats": mutual, "ratio": mutual / h,
            "conclusion": "finite discrete Shannon ensemble only; continuous I/h excluded",
        },
        "ratio_interpretation_counterexample": {
            "x": x, "y": y,
            "baseline": {"x": math.sqrt(x[0] * x[1]), "y": math.sqrt(y[0] * y[1])},
            "power_reparameterization": "x1 -> x1**2, x2 -> x2",
            "transformed": {"x": math.sqrt(x[0] ** 2 * x[1]),
                            "y": math.sqrt(y[0] ** 2 * y[1])},
            "order_flip": True,
        },
    }
    out = Path(__file__).resolve().parent / "analysis_r14_math.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result["analysis_r14_math_py_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    # Write once with source hash included; deterministic across reruns.
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("linear-fraction exact/grid:", exact["objective"], grid["objective"])
    print("continuous I/h:", mutual / h)
    print("scale baseline/transformed:", result["ratio_interpretation_counterexample"])
    print("[out]", out)


if __name__ == "__main__":
    main()
