#!/usr/bin/env python3
"""EXEC-1 富耦合实例上的权重/弹性敏感性重跑（2026-10-21，审稿 R7-Major 第3条：
主矩阵默认实例 A_exec≈0.017 窄带使权重稳定性实为四通道意义——本脚本在第五通道
恢复动态范围（0.234，13.7×）的 EXEC-1 实例上重跑同一电池）。

原理（与 analysis_weights_sigma.py 同一纪律）：EXEC-1 逐臂登记的分量为 σ-无关
真值（truth mode，30 rep 逐比特一致），复合层 A=A_via·F_σ(components; w) 可任意
重算——本脚本只读 runs/<root>/exec1/results.csv，不重新仿真。

分析项：
  E1 权重敏感性：6 个权重向量（与 analysis_weights_sigma.WEIGHT_CONFIGS 相同）下
     δ-收缩链 rich > delta_mv > delta_nm 的 verdict 保持、复合水平区间、
     Kendall τ（对 equal；3 点链且一点被零歼灭钉死，如实标注为粗判据）；
  E2 弹性带：ς∈{0.25,0.5,0.75,1} 下链保持与 delta_nm 精确零；ς=2 压力臂的
     零歼灭失效回声（delta_nm 处 A>0，与主矩阵 0.1652 对照）。

用法：python3 analysis_exec1_weights.py [--root runs/20261017_full]
产出：analysis_exec1_weights.json（机读）＋ stdout 摘要（正文权重敏感性段数据源）。
"""
import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from autonomy_sim.aggregate import composite_A  # noqa: E402

ORDER = ("a_org", "a_goal", "a_exec", "a_epi", "a_ref")
ARMS = ("rich", "delta_mv", "delta_nm")

WEIGHT_CONFIGS = {
    "equal": (0.2, 0.2, 0.2, 0.2, 0.2),
    "org_heavy": (0.30, 0.175, 0.175, 0.175, 0.175),
    "goal_heavy": (0.175, 0.30, 0.175, 0.175, 0.175),
    "exec_heavy": (0.175, 0.175, 0.30, 0.175, 0.175),
    "epi_heavy": (0.175, 0.175, 0.175, 0.30, 0.175),
    "goal_extreme": (0.1375, 0.45, 0.1375, 0.1375, 0.1375),
}

SIGMA_BAND = (0.25, 0.5, 0.75, 1.0, 2.0)


def kendall_tau(xs, ys):
    n = len(xs)
    c = d = 0
    for i in range(n):
        for j in range(i + 1, n):
            s = (xs[i] - xs[j]) * (ys[i] - ys[j])
            if s > 0:
                c += 1
            elif s < 0:
                d += 1
    return (c - d) / (c + d) if c + d else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="runs/20261017_full")
    args = ap.parse_args()
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        args.root, "exec1", "results.csv")
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    # 确定性核验：30 rep 的三分量束须逐比特一致（truth mode 语义）
    bundles = []
    for r in rows:
        arms = json.loads(r["metrics_json"])["arms"]
        bundles.append(tuple(
            tuple(float(arms[a][c]) for c in ORDER) for a in ARMS))
        assert abs(float(arms["rich"]["a_via"]) - 1.0) < 1e-12
    assert len(set(bundles)) == 1, "EXEC-1 臂束跨 rep 不一致（truth-mode 语义破坏）"
    comps = dict(zip(ARMS, bundles[0]))
    a_via = 1.0

    out = {"root": args.root, "n_reps": len(rows), "arms": ARMS,
           "components": {a: list(comps[a]) for a in ARMS},
           "weights": {}, "sigma_band": {}}
    base = tuple(composite_A(a_via, comps[a], WEIGHT_CONFIGS["equal"], sigma=1.0)
                 for a in ARMS)
    for name, w in WEIGHT_CONFIGS.items():
        vals = tuple(composite_A(a_via, comps[a], w, sigma=1.0) for a in ARMS)
        out["weights"][name] = {
            "A": dict(zip(ARMS, vals)),
            "chain_preserved": bool(vals[0] > vals[1] > vals[2] == 0.0),
            "kendall_tau_vs_equal": kendall_tau(base, vals),
        }
    for s in SIGMA_BAND:
        vals = tuple(composite_A(a_via, comps[a], WEIGHT_CONFIGS["equal"], sigma=s)
                     for a in ARMS)
        out["sigma_band"][str(s)] = {"A": dict(zip(ARMS, vals))}

    dst = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "analysis_exec1_weights.json")
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("[E1] weight sensitivity on EXEC-1 (chain rich>delta_mv>delta_nm=0):")
    for name, rec in out["weights"].items():
        a = rec["A"]
        print(f"  {name:12s} rich={a['rich']:.4f} mv={a['delta_mv']:.4f} "
              f"nm={a['delta_nm']:.6f} tau={rec['kendall_tau_vs_equal']:.4f} "
              f"chain_ok={rec['chain_preserved']}")
    print("[E2] elasticity band (equal weights):")
    for s, rec in out["sigma_band"].items():
        a = rec["A"]
        print(f"  sigma={s:>4s} rich={a['rich']:.4f} mv={a['delta_mv']:.4f} "
              f"nm={a['delta_nm']:.6f}")
    print("[out]", dst)


if __name__ == "__main__":
    main()
