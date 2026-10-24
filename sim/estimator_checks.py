#!/usr/bin/env python3
"""§13 数值记录产出（SPEC_estimators §14/E14.0）：每分量在合成配置上"真值=估计（容差内）"。

产出 runs/<date>_full/estimator_checks.json（或 --out 指定）；供 report.md §3.3 引用。
A_ref/Λ 事件级采样路径 v1 无日志载体（E14.0）——在此登记为显式缺口（非静默）。
"""
import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from autonomy_sim import components, di, interventions, propagate, simulate, wiring  # noqa: E402
from autonomy_sim.blackbox import a_exec_blackbox, a_org_interval, probe_flow_obs  # noqa: E402
from autonomy_sim.env0 import Env0Config, build_env0  # noqa: E402
from autonomy_sim.estimators import (  # noqa: E402
    estimate_epi_accuracy, estimate_g_mean, estimate_mi_action_obs, estimate_probe_flow,
    estimate_z_high,
)
from autonomy_sim.fixtures import toy_model  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out = args.out or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "runs",
        f"{time.strftime('%Y%m%d')}_full", "estimator_checks.json")

    records = {}

    # A_org（E14.1，toy fixture β_π 探针臂）
    m0 = toy_model()
    al = m0.alphabet
    script = np.tile(np.full(al.n_A, 1.0 / al.n_A), (al.n_S, 1))
    mp = interventions.apply_beta_pi(
        m0, interventions.BetaPiSpec.switch([script], flag_dist=(0.8, 0.2)))
    T = 3
    trajs = simulate.simulate_trajectories(mp, 910099, T, 4000,
                                           i_decoder=interventions.make_i_decoder(mp))
    est = estimate_probe_flow(trajs, n_I=2, n_A=al.n_A)
    f_obs_true = probe_flow_obs(mp, T)
    f_base = di.truth_F_int(m0, T)
    f_int_true = di.truth_F_int(mp, T)
    a_true = f_int_true / (f_int_true + f_obs_true)
    lo, hi = a_org_interval(f_base, 0.3, est.point)
    records["A_org"] = {
        "config": "toy + β_π 均匀探针臂（flag=0.2）", "T": T, "n_traj": 4000,
        "F_ext_obs_est": [est.point, est.half], "F_ext_obs_truth": f_obs_true,
        "abs_err": abs(est.point - f_obs_true), "mm_bias": est.diag["mm_bias"],
        "a_org_interval": [lo, hi], "a_true_observable": a_true,
        "interval_contains": bool(lo <= a_true <= hi),
    }

    # env0 基线两分量＋γ 臂精度（E14.2–E14.4）
    cfg = Env0Config()
    me = build_env0(cfg)
    mg = interventions.apply_gamma(me, interventions.GammaSpec.mix_constant(0.5, symbol=0))
    t0 = simulate.simulate_trajectories(me, 910098, 3, 2000)
    tg = simulate.simulate_trajectories(mg, 910098, 3, 2000)
    j0 = propagate.truth_step_joints(me, 3)

    est = estimate_z_high(t0, n_Z=me.alphabet.n_Z)
    truth = float(np.mean([aux["Z"][1] for aux in j0]))
    records["A_via"] = {"config": "env0 基线", "z_high_est": [est.point, est.half],
                        "z_high_truth": truth, "abs_err": abs(est.point - truth)}

    est = estimate_g_mean(t0, me.alphabet)
    s_fin = j0[-1]["S"].reshape(me.alphabet.n_G, -1).sum(axis=1)
    truth = float(np.dot(s_fin, np.arange(me.alphabet.n_G)))
    records["A_goal_input"] = {"config": "env0 基线", "u_eff_est": [est.point, est.half],
                               "u_eff_truth": truth, "abs_err": abs(est.point - truth),
                               "note": "MaxEnt-IRL 黑盒恢复（E4.3）属报告附栏，本条为白盒直读路径"}

    # A_epi（E14.4 精度化口径）：γ=0.5 臂日志直读命中率 vs 真值精度（同 κ）
    bmap = wiring.derive_bucket_map(mg)
    est = estimate_epi_accuracy(tg, bmap)
    truth = components.truth_A_epi_real(mg, 3, bmap).a_epi_real
    records["A_epi"] = {"config": "env0 γ=0.5 臂（日志直读精度；E5.1 精度化口径）",
                        "a_epi_est": [est.point, est.half], "a_epi_truth": truth,
                        "abs_err": abs(est.point - truth),
                        "a_epi_truth_baseline": components.truth_A_epi_real(me, 3, bmap).a_epi_real}

    # A_exec 黑盒观察量（E14.5，锐化温度臂——BB-1 ② 协议前提域）
    ms = build_env0(Env0Config(alpha_temp=0.05))
    ts = simulate.simulate_trajectories(ms, 910097, 3, 8000)
    est = estimate_mi_action_obs(ts, t=1, n_A=me.alphabet.n_A, n_O=me.alphabet.n_O)
    i_obs, i_cond = a_exec_blackbox(ms, t=1, policy_driven=True)
    records["A_exec_obs"] = {"config": "env0 锐化温度臂（α_temp=0.05，10.3 被动观察协议）",
                             "mi_est": [est.point, est.half], "mi_truth": i_obs,
                             "abs_err": abs(est.point - i_obs),
                             "mm_bias": est.diag["mm_bias"], "i_cond_truth": i_cond}

    # 显式缺口登记（E14.0：非静默）
    records["registered_gaps"] = [
        "A_ref：采样载体 defense_events 背书事件日志 v1 未承载（事件级细化），"
        "本条真值=估计记录暂缺——登记为报告局限节条目",
        "Λ：事件级（附录 §4.4）采样路径同上；v1 为律级/标记级操作化（P9.4/E12.6）",
    ]

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(records, fh, ensure_ascii=False, indent=2, sort_keys=True)
    print(f"[estimator_checks] -> {out}")
    for k, v in records.items():
        if k != "registered_gaps":
            print(f"  {k}: abs_err={v['abs_err']:.5f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
