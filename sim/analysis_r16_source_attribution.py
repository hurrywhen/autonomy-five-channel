#!/usr/bin/env python3
"""Exact R16 source-order and T=2 closed-loop attribution audit.

The saved artifact is an analytic model guard, not an external experiment.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "src"))

from autonomy_sim.source_attribution import (  # noqa: E402
    flow_share, joint_directed_information_nats, nats_to_bits,
    ordered_attribution_nats, ordered_residual_di_nats,
    shapley_order_average_nats)
from analysis_r15_x5c_paired import compare_replay_json  # noqa: E402

R, N, I, A = 0, 1, 2, 3


def _bits(flows):
    return [nats_to_bits(value) for value in flows]


def _or_law():
    joint = np.zeros((2, 2, 2))
    for r, n in itertools.product((0, 1), repeat=2):
        joint[r, n, r | n] += 0.25
    return joint


def _action(policy, r, n):
    if policy == "pure_random":
        return r
    if policy == "pure_normative":
        return n
    if policy == "mixed_xor":
        return r ^ n
    raise ValueError(policy)


def _closed_loop_law(policy):
    joint = np.zeros((2,) * 8)
    for r1, r2, i1, i2 in itertools.product((0, 1), repeat=4):
        n1 = i1
        a1 = _action(policy, r1, n1)
        n2 = n1 ^ a1 ^ i2
        a2 = _action(policy, r2, n2)
        joint[r1, r2, n1, n2, i1, i2, a1, a2] += 1.0 / 16.0
    return joint


def _direct_bypass_law():
    joint = np.zeros((2,) * 8)
    for r1, r2, i1, i2 in itertools.product((0, 1), repeat=4):
        n1 = 0
        a1 = r1 ^ n1 ^ i1
        n2 = a1
        a2 = r2 ^ n2 ^ i2
        joint[r1, r2, n1, n2, i1, i2, a1, a2] += 1.0 / 16.0
    return joint


def _ordered_report(joint, horizon, action):
    rn = _bits(ordered_attribution_nats(joint, horizon=horizon,
                                       order=(R, N, I) if horizon == 2 else (R, N),
                                       action=action))
    nr = _bits(ordered_attribution_nats(joint, horizon=horizon,
                                       order=(N, R, I) if horizon == 2 else (N, R),
                                       action=action))
    grouped = nats_to_bits(joint_directed_information_nats(
        joint, horizon=horizon,
        sources=(R, N, I) if horizon == 2 else (R, N), action=action))
    if horizon == 2:
        average = {"R": 0.5 * (rn[0] + nr[1]),
                   "N": 0.5 * (rn[1] + nr[0]),
                   "I": 0.5 * (rn[2] + nr[2])}
        norm_rni, norm_nri = rn[1], nr[0]
        flows = {"RNI": rn, "NRI": nr}
    else:
        avg = shapley_order_average_nats(joint, horizon=1, sources=(R, N), action=action)
        average = {key: nats_to_bits(value) for key, value in
                   (("R", avg[R]), ("N", avg[N]))}
        norm_rni, norm_nri = rn[1], nr[0]
        flows = {"RN": rn, "NR": nr}
    return {"flows_bits": flows, "joint_di_bits": grouped,
            "normative_share_RNI": flow_share(norm_rni, grouped),
            "normative_share_NRI": flow_share(norm_nri, grouped),
            "order_averaged_flows_bits_I_last": average,
            "normative_share_order_average": flow_share(average["N"], grouped)}


def compute() -> dict:
    or_report = _ordered_report(_or_law(), 1, 2)
    closed = {}
    for policy in ("pure_random", "pure_normative", "mixed_xor"):
        joint = _closed_loop_law(policy)
        closed[policy] = {
            "positive_atoms": int(np.count_nonzero(joint)),
            "atom_probability": 1.0 / 16.0,
            **_ordered_report(joint, 2, A),
        }
    mediated_joint = _closed_loop_law("pure_normative")
    bypass_joint = _direct_bypass_law()
    mediated = {
        "external_only_di_bits": nats_to_bits(joint_directed_information_nats(
            mediated_joint, horizon=2, sources=(I,), action=A)),
        "residual_external_after_R_N_bits": nats_to_bits(ordered_residual_di_nats(
            mediated_joint, horizon=2, source=I, action=A, condition_on=(R, N))),
    }
    bypass_chain = _bits(ordered_attribution_nats(
        bypass_joint, horizon=2, order=(R, N, I), action=A))
    return {
        "artifact_version": "R16-source-attribution-v1",
        "analysis_status": "EXACT_ANALYTIC_MODEL_GUARD",
        "units": "bits",
        "external_construct_validation": False,
        "historical_results_modified": False,
        "model_definitions": {
            "OR": "independent fair R,N; A=R OR N; no I",
            "closed_loop": ("R1,R2,I1,I2 independent fair; N1=I1; "
                            "N2=N1 XOR A1 XOR I2; A_t=R_t, N_t, or R_t XOR N_t"),
            "direct_bypass": ("N1=0; N2=A1; A1=R1 XOR N1 XOR I1; "
                              "A2=R2 XOR N2 XOR I2"),
        },
        "OR_counterexample": or_report,
        "semantic_swap_note": ("With RNI held fixed, swapping the N/R semantic labels in the "
                               "symmetric OR model interchanges the two ordered normative shares; "
                               "order averaging does not solve semantic relabeling."),
        "closed_loop_T2": closed,
        "mediated_external_witness": mediated,
        "direct_bypass_witness": {
            "RNI_flows_bits": bypass_chain,
            "joint_di_bits": nats_to_bits(joint_directed_information_nats(
                bypass_joint, horizon=2, sources=(R, N, I), action=A)),
        },
        "interpretation": ("Ordered residual attribution and the I-last two-order average are "
                           "sensitivity descriptors, not unique causal or PID decompositions."),
    }


def validate_result(result: dict) -> None:
    """Independent closed-form anchors; fail even if a saved artifact agrees."""
    or_result = result["OR_counterexample"]
    entropy = 2.0 - 0.75 * math.log2(3.0)
    expected_or = {
        "joint_di_bits": entropy,
        "normative_share_RNI": 0.5 / entropy,
        "normative_share_NRI": (entropy - 0.5) / entropy,
        "normative_share_order_average": 0.5,
    }
    for key, expected in expected_or.items():
        if not math.isclose(or_result[key], expected, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError(f"OR analytic anchor failed: {key}")
    expected_flows = {
        "pure_random": ((2.0, 0.0, 0.0), (0.0, 2.0, 0.0)),
        "pure_normative": ((0.0, 2.0, 0.0), (2.0, 0.0, 0.0)),
        "mixed_xor": ((0.0, 2.0, 0.0), (0.0, 2.0, 0.0)),
    }
    for policy, (rn, nr) in expected_flows.items():
        row = result["closed_loop_T2"][policy]
        np.testing.assert_allclose(row["flows_bits"]["RNI"], rn, atol=2e-12, rtol=0.0)
        np.testing.assert_allclose(row["flows_bits"]["NRI"], nr, atol=2e-12, rtol=0.0)
        if not math.isclose(row["joint_di_bits"], 2.0, abs_tol=2e-12):
            raise ValueError(f"joint DI anchor failed: {policy}")
    mediated = result["mediated_external_witness"]
    if not (math.isclose(mediated["external_only_di_bits"], 2.0, abs_tol=2e-12)
            and math.isclose(mediated["residual_external_after_R_N_bits"], 0.0,
                             abs_tol=2e-12)):
        raise ValueError("mediation witness failed")
    if not math.isclose(result["direct_bypass_witness"]["RNI_flows_bits"][2], 2.0,
                        abs_tol=2e-12):
        raise ValueError("direct bypass witness failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(HERE / "analysis_r16_source_attribution.json"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = compute()
    validate_result(result)
    if args.check:
        saved = json.loads(Path(args.out).read_text(encoding="utf-8"))
        comparison = compare_replay_json(saved, result)
        if not comparison["passed"]:
            raise SystemExit("R16 source-attribution check FAILED: "
                             + "; ".join(comparison["differences"][:8]))
        print("R16 source-attribution check OK: OR + three T=2 policies + mediation/bypass; "
              f"max abs float diff={comparison['max_abs_float_difference']:.3e}")
        return 0
    Path(args.out).write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                              encoding="utf-8")
    print("R16 source-attribution exact analytic guards PASS")
    print("[out]", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
