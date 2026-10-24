#!/usr/bin/env python3
"""权重 w 与 CES 弹性 σ 的后验敏感性分析（2026-10-13 补充分析；SPEC_experiments §7；
2026-10-15 数据切到审稿修复批 runs/20261015_full）。

原理：主矩阵逐臂登记的六分量束为 σ-无关真值（M9.4 缓存语义），复合层
A = A_via·F_σ(components; w) 可任意重算——本脚本只读 runs/20261015_full 的
results.csv，不重新仿真。

分析项：
  W1 值域：全部重算 A ∈ [0,1]（T1a 在各权重/σ 下）
  W2 零歼灭：ATK-1 完全俘获档（a_goal=0）在 σ<1 任意权重下精确为 0
  W3 排序稳健性：等权基底下各 (场景,配置,σ,种子,臂) A 值排序 vs 备选权重的 Kendall τ
  W4 T4 攻击点：由 ATK-2 的 t4_ratio（=w_i·s_i/c_i，等权基准）重算各权重向量下的
     argmax 通道占比（T4 的 argmax 依赖 w 是定理内容本身，此处量化其敏感度）
  W5 A_min 两级陈述支持：按 ATK-6 的随机配置分布抽样，验证 A_min=0 当且仅当
     存在 κ_j = δ*_j（点态界 (1−δ_j/κ_j) 仍 >0 当 δ_j<κ_j）——修订后定理的两级语义
  S1 σ 扩展带：σ∈{0.25,0.5,0.75,1} 重算全部臂的 A（σ=2 压力臂保持单列对照），
     报告 T1a/T3a/基线锚稳定性与 ATK-1 η=1 档 A 值表
  S2 AHI 口径：phen 轨分量未入 CSV（仅终值）⇒ AI 序列仅在标定权重下报告，记为局限

用法：python3 analysis_weights_sigma.py [--root runs/20261015_full]
产出：analysis_weights_sigma.json（机读）+ stdout 摘要（make_report 补充节数据源）。
"""
import argparse
import csv
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from autonomy_sim.aggregate import composite_A  # noqa: E402
from autonomy_sim.dynamics import a_min, delta_star  # noqa: E402

# 通道顺序（wiring.comps5）：org, goal, exec, epi, ref
ORDER = ("org", "goal", "exec", "epi", "ref")

WEIGHT_CONFIGS = {
    "equal": (0.2, 0.2, 0.2, 0.2, 0.2),
    "org_heavy": (0.30, 0.175, 0.175, 0.175, 0.175),
    "goal_heavy": (0.175, 0.30, 0.175, 0.175, 0.175),
    "exec_heavy": (0.175, 0.175, 0.30, 0.175, 0.175),
    "epi_heavy": (0.175, 0.175, 0.175, 0.30, 0.175),
    "goal_extreme": (0.1375, 0.45, 0.1375, 0.1375, 0.1375),
}

SIGMA_EXT = (0.25, 0.5, 0.75, 1.0)

# ATK-6 的随机配置分布（scenario_atk6 ② 的构造参数）
AMIN_N = 400


def load_arms(root):
    """展开 results.csv 为逐臂记录：(组,场景,配置,σ,种子,臂id,强度,分量,av,lam)。"""
    arms = []
    for group in ("main", "stress_sigma2"):
        path = os.path.join(root, group, "results.csv")
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                m = json.loads(r["metrics_json"])
                rows = m.get("rows")
                if not rows:
                    continue
                for i, row in enumerate(rows):
                    b = row.get("bundle")
                    if not b:
                        continue
                    comps = tuple(float(b[k]) for k in ("a_org", "a_goal", "a_exec",
                                                        "a_epi", "a_ref"))
                    strength = row.get("eta", row.get("s", row.get("lam", i)))
                    arms.append({
                        "group": group, "scenario": r["scenario_code"], "name": r["name"],
                        "config": r["config_code"], "sigma": float(r["sigma"]),
                        "rep": int(r["rep"]), "arm": i, "strength": float(strength),
                        "comps": comps, "a_via": float(b["a_via"]), "lam": float(b["lam"]),
                        "a_obj": float(b["a_obj"]),
                    })
    return arms


def kendall_tau(xs, ys):
    """O(n log n) Kendall τ（无并列处理——浮点 A 值并列概率可忽略；并列时返回近似）。"""
    n = len(xs)
    if n < 2:
        return 1.0
    order = sorted(range(n), key=lambda i: xs[i])
    ranks = [0] * n
    for pos, i in enumerate(order):
        ranks[i] = pos
    # 归并排序计逆序对
    arr = [ranks[i] for i in sorted(range(n), key=lambda i: ys[i])]
    inv = 0

    def ms(a):
        nonlocal inv
        if len(a) <= 1:
            return a
        mid = len(a) // 2
        l, rr = ms(a[:mid]), ms(a[mid:])
        out, i, j = [], 0, 0
        while i < len(l) and j < len(rr):
            if l[i] <= rr[j]:
                out.append(l[i]); i += 1
            else:
                out.append(rr[j]); j += 1
                inv += len(l) - i
        return out + l[i:] + rr[j:]
    ms(arr)
    return 1.0 - 4.0 * inv / (n * (n - 1.0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "runs", "20261015_full"))
    args = ap.parse_args()
    arms = load_arms(args.root)
    main_arms = [a for a in arms if a["group"] == "main"]
    print(f"[load] arms: total={len(arms)} main={len(main_arms)}")

    out = {"n_arms_total": len(arms), "n_arms_main": len(main_arms)}

    # ---------- W1/W2/W3：权重扫描 ----------
    w_res = {}
    base_vals = [composite_A(a["a_via"], a["comps"], WEIGHT_CONFIGS["equal"], sigma=a["sigma"])
                 for a in main_arms]
    for wname, w in WEIGHT_CONFIGS.items():
        vals = [composite_A(a["a_via"], a["comps"], w, sigma=a["sigma"]) for a in main_arms]
        range_viol = sum(1 for v in vals if not (-1e-9 <= v <= 1 + 1e-9))
        w_res[wname] = {"range_violations": range_viol,
                        "tau_vs_equal": kendall_tau(base_vals, vals)}
    # 零歼灭：实际完全俘获档（分量 a_goal≈0；名义 η=1 但防御压缩的窗口外臂不计入）
    cap = [a for a in main_arms if a["scenario"] == "1" and a["comps"][1] <= 1e-9]
    zero_ok = {}
    for wname, w in WEIGHT_CONFIGS.items():
        bad = sum(1 for a in cap
                  if composite_A(a["a_via"], a["comps"], w, sigma=a["sigma"]) > 1e-9)
        zero_ok[wname] = {"n_complete_capture": len(cap), "violations": bad}
    # T3a 单调性（ATK-1 η 网格 / ATK-2 s 网格，同 cell 内按臂序）
    def monotone_violations(arms_sub, w, sigmas):
        viol = 0
        cells = {}
        for a in arms_sub:
            if sigmas and a["sigma"] not in sigmas:
                continue
            key = (a["scenario"], a["config"], a["sigma"], a["rep"])
            cells.setdefault(key, []).append(a)
        for key, lst in cells.items():
            lst.sort(key=lambda a: a["arm"])
            vs = [composite_A(a["a_via"], a["comps"], w, sigma=a["sigma"]) for a in lst]
            viol += sum(1 for x, y in zip(vs, vs[1:]) if y > x + 1e-9)
        return viol, len(cells)
    t3_res = {}
    atk12 = [a for a in main_arms if a["scenario"] in ("1", "2")]
    for wname, w in WEIGHT_CONFIGS.items():
        v, ncells = monotone_violations(atk12, w, None)
        t3_res[wname] = {"monotone_violations": v, "n_cells": ncells}
    w_res["_zero_annihilation"] = zero_ok
    w_res["_t3a_monotone"] = t3_res
    out["weights"] = w_res

    # ---------- W4：T4 攻击点 ----------
    t4_rows = []
    path = os.path.join(args.root, "main", "results.csv")
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["scenario_code"] != "2":
                continue
            m = json.loads(r["metrics_json"])
            ratio = m.get("t4_ratio")
            if ratio:
                t4_rows.append({"config": r["config_code"], "sigma": float(r["sigma"]),
                                "rep": int(r["rep"]), "ratio": ratio,
                                "pick": m.get("t4_pick")})
    t4_res = {"n_cells": len(t4_rows), "picks": {}}
    for wname, w in WEIGHT_CONFIGS.items():
        picks = {k: 0 for k in ORDER}
        for tr in t4_rows:
            scaled = {ch: float(tr["ratio"][ch]) * w[i] / WEIGHT_CONFIGS["equal"][i]
                      for i, ch in enumerate(ORDER)}
            best = max(scaled, key=scaled.get)
            picks[best] += 1
        t4_res["picks"][wname] = picks
    out["t4_attack_point"] = t4_res

    # ---------- W5：A_min 两级陈述 ----------
    # 分布 A = scenario_atk6 ② 的原分布（κ∈[0.6,1]，κ 不绑定——与仿真一致，
    # A_min>0 恒成立）；分布 B = 加宽 κ∈[0.1,0.4]（θ/W、⌈(r+1)/2⌉c₀/W∈[0.1,0.3]（r=1），
    # κ 以正概率绑定 ⇒ 旧式 (11) 的 A_min=0 退化显形）。
    def amin_batch(kappa_lo, kappa_hi, n, tag):
        state = 20261013 if tag == "A" else 998244353
        res = {"n_configs": n, "binding_kappa": 0, "a_min_zero": 0,
               "pointwise_floor_positive_when_unbound": 0, "by_sigma": {}}
        for sig in SIGMA_EXT:
            res["by_sigma"][str(sig)] = {"positive": 0}
        for i in range(n):
            state = (1103515245 * state + 12345) % (2 ** 31)
            def u(lo, hi, shift):
                return lo + (hi - lo) * ((state >> shift) % 10000) / 10000.0
            kappas = tuple(u(kappa_lo, kappa_hi, 8 + 5 * j) for j in range(5))
            thetas = tuple(u(0.1, 0.3, 9 + 5 * j) for j in range(5))
            c0s = tuple(u(0.1, 0.3, 10 + 5 * j) for j in range(5))
            ds = tuple(delta_star(thetas[j], 1.0, kappas[j], 1.0, c0s[j]) for j in range(5))
            abase = tuple(u(0.5, 1.0, 11 + j) for j in range(5))
            w = WEIGHT_CONFIGS["equal"]
            bound = any(abs(ds[j] - kappas[j]) < 1e-12 for j in range(5))
            res["binding_kappa"] += int(bound)
            for sig in SIGMA_EXT:
                val = a_min(0.9, abase, w, ds, kappas, sigma=sig)
                if val <= 1e-12:
                    res["a_min_zero"] += 1
                else:
                    res["by_sigma"][str(sig)]["positive"] += 1
                    res["pointwise_floor_positive_when_unbound"] += int(not bound)
        return res
    amin_res = {"dist_A_scenario_distribution": amin_batch(0.6, 1.0, AMIN_N, "A"),
                "dist_B_kappa_binding": amin_batch(0.1, 0.4, AMIN_N, "B")}
    out["amin_two_tier"] = amin_res

    # ---------- S1：σ 扩展带 ----------
    s_res = {"sigmas": list(SIGMA_EXT), "range_violations": {}, "baseline_max": {},
             "monotone_violations": {}, "atk1_full_capture": {}}
    for sig in SIGMA_EXT:
        vals = [composite_A(a["a_via"], a["comps"], WEIGHT_CONFIGS["equal"], sigma=sig)
                for a in main_arms]
        s_res["range_violations"][str(sig)] = sum(1 for v in vals
                                                  if not (-1e-9 <= v <= 1 + 1e-9))
        base = [composite_A(a["a_via"], a["comps"], WEIGHT_CONFIGS["equal"], sigma=sig)
                for a in main_arms if a["arm"] == 0]
        s_res["baseline_max"][str(sig)] = max(base)
        v, _ = monotone_violations(atk12, WEIGHT_CONFIGS["equal"], {sig})
        s_res["monotone_violations"][str(sig)] = v
        capv = [composite_A(a["a_via"], a["comps"], WEIGHT_CONFIGS["equal"], sigma=sig)
                for a in cap]
        s_res["atk1_full_capture"][str(sig)] = (min(capv), max(capv))
    # σ=2 对照（压力臂）
    cap2 = [a for a in arms if a["group"] == "stress_sigma2"
            and a["scenario"] == "1" and a["comps"][1] <= 1e-9]
    s_res["sigma2_full_capture"] = [min(a["a_obj"] for a in cap2), max(a["a_obj"] for a in cap2)]
    out["sigma_extension"] = s_res

    # ---------- 写盘 ----------
    out_path = os.path.join(args.root, "analysis_weights_sigma.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"[write] {out_path}")

    # ---------- 摘要 ----------
    print("\n== W1/W3 权重扫描（Kendall τ vs 等权；n=%d 臂）==" % len(main_arms))
    for wname in WEIGHT_CONFIGS:
        print(f"  {wname:12s} range违例={w_res[wname]['range_violations']} "
              f"τ={w_res[wname]['tau_vs_equal']:.4f}")
    print("== W2 零歼灭（ATK-1 完全俘获档，n=%d）==" % len(cap))
    for wname, z in zero_ok.items():
        print(f"  {wname:12s} 违例={z['violations']}")
    print("== W3' T3a 单调性违例（ATK-1/2）==")
    for wname, t in t3_res.items():
        print(f"  {wname:12s} {t['monotone_violations']}/{t['n_cells']} cells")
    print("== W4 T4 攻击点分布（n=%d cells）==" % t4_res["n_cells"])
    for wname, p in t4_res["picks"].items():
        print(f"  {wname:12s} {p}")
    print("== W5 A_min 两级（各 n=%d 随机配置）==" % AMIN_N)
    for tag, r5 in amin_res.items():
        print(f"  {tag}: κ绑定(δ*=κ)={r5['binding_kappa']}；A_min=0={r5['a_min_zero']}；"
              f"未绑定点态为正={r5['pointwise_floor_positive_when_unbound']}")
    print("== S1 σ 扩展带 ==")
    for sig in SIGMA_EXT:
        print(f"  σ={sig:<5} range违例={s_res['range_violations'][str(sig)]} "
              f"基线max={s_res['baseline_max'][str(sig)]:.4f} "
              f"单调违例={s_res['monotone_violations'][str(sig)]} "
              f"ATK-1η=1 A∈[{s_res['atk1_full_capture'][str(sig)][0]:.4f},"
              f"{s_res['atk1_full_capture'][str(sig)][1]:.4f}]")
    print(f"  σ=2 对照 ATK-1η=1 A∈[{s_res['sigma2_full_capture'][0]:.4f},"
          f"{s_res['sigma2_full_capture'][1]:.4f}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
