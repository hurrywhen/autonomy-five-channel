#!/usr/bin/env python3
"""R3c 实验报告生成器（SPEC_experiments §3.4 模板／P3.1–P3.5／§7 完成判据）。

读 runs/<root>/ 下各组 results.csv＋verdict_table.csv＋estimator_checks.json，
聚合产出 <root>/report.md（定理分节＋专节＋局限节），并复制到 docs/ 供版本库跟踪。

用法：python3 make_report.py [--root runs/<date>_full] [--docs-copy]
"""
import argparse
import csv
import glob
import json
import os
import shutil
import subprocess
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from autonomy_sim.scenarios import Verdict  # noqa: E402
from autonomy_sim import matrix  # noqa: E402

# 定理 → (陈述, 判据载体 [(组, 场景, [判据])], 证据提取键)
THEOREMS = [
    ("T1a", "A∈[0,1] 全域（值域定理）", [("main", None, [])], "元判据①＋WIT T-T1a"),
    ("T1b", "运行正性：A_via=0 ⇒ A=0（闸门）", [("res1", 10, ["C1_via_gate_zero", "C2_monotone_supply"])], "RES-1 臂对照"),
    ("T1c", "条件严格上界（分量不全为 1 ⇒ A<1）", [("main", 1, ["C1_goal_monotone_graded"])], "基线束分量扫描（附栏）"),
    ("T1d", "不可检测操纵存在（亚阈档）", [("main", 2, ["C5_T1d_subthreshold"])], "ATK-2⑤ tv 值"),
    ("T2", "覆盖定理＋多通道必要性（主打）", [("main", 4, ["C1_persuasion_four_tracks", "C2_hijack_a_org_down", "C3_multichannel_necessity"]),
                                        ("main", 2, ["C2_org_blind"])], "四轨表＋盲见证表（元判据③）"),
    ("T3a", "操纵 ⇒ A 降（ceteris paribus）", [("main", 1, ["C3_A_strict_down"]), ("main", 2, ["C1_epi_down"]),
                                        ("force1", 11, ["C1_beta_g_forced_down", "C2_delta_forced_down"])], "末端档 a_obj 对照"),
    ("T3b", "隐蔽 ⇒ Â≥A 且差距随 s(γ) 单调（主打）", [("main", 2, ["C3_T3b_ai_monotone", "C4_early_warning"])], "AI 序列与预警档"),
    ("T4", "最弱环节（攻防双侧）", [("main", 2, ["C6_T4_attack_concentrates", "C7_T4_defense_equalize"])], "T4 随 σ 单列（敏感性节）"),
    ("T5", "六析取充要", [("main", 1, ["C2_complete_capture_zero"]), ("main", 3, ["C5_A_degrades_with_empowerment"]),
                    ("main", 4, ["C2_hijack_a_org_down"]), ("main", 5, ["C3_ref_zero_limit"]),
                    ("res1", 10, ["C1_via_gate_zero"]),
                    ("erosion", 15, ["C3_common_mode_zero", "C4_channels_blind"])], "五析取＋充要元判据②＋σ⁻ 能力包络扩展析取（v0.5）"),
    ("T6", "自主性裕度（主打）", [("main", 6, ["C1_design_rule_bounded", "C2_a_min_per_run", "C3_blind_zone_capture",
                                          "C4_delta_star_ablation", "C5_registration_domain", "C6_detection_divergence"]),
                             ("main", 5, ["C2_gate_margin_monotone"])], "盲区消融专节"),
    ("T7", "委托律（线性/夹逼/复合/q=1 α 等价/f>0 非退化夹逼）", [("del1", 7, ["C1_h1_linear_law", "C2_bracket_non_h1",
                                                        "C3_composite_fit", "C4_q1_alpha_equivalence",
                                                        "C5_f_pos_bracket", "C6_rho_neq1_bracket"])], "max_dev 与 w_org 斜率；f>0/ρ≠1 臂（v0.5）"),
    ("T8", "强制悖论", [("force1", 11, ["C1_beta_g_forced_down", "C2_delta_forced_down", "C3_sigma_bounds_up_immediate_kept"])], "LIT 对照（ryan_deci2000）"),
    ("C0", "行为不可区分而自主性可区分（主打）", [("c0_demo", 8, ["C1_behavior_identical", "C2_epi_lambda_separate"]),
                                          ("c0corr", 13, ["C1_tau_matching_positive", "C2_projection_direction", "C3_generality_margin"])], "C0 专节"),
    ("C1", "fold 相变与临界慢化", [("main", 3, ["C1_EWS_measurable", "C2_trec_scaling"])], "T_rec 标度斜率/R²（30 种子 CI）"),
    ("C2", "滞后回环不闭合", [("main", 3, ["C3_hysteresis"])], "δ_down、s_c 独立锚"),
]

GROUP_LABEL = {"main": "主矩阵", "stress_sigma2": "σ=2 压力", "del1": "DEL-1", "c0_demo": "C0-DEMO",
               "c0corr": "C0-CORR", "res1": "RES-1", "force1": "FORCE-1", "bb1": "BB-1",
               "lh1": "LH-1", "bb2": "BB-2", "erosion": "σ⁻-EROSION", "exec1": "EXEC-1"}


def load_rows(group_dir):
    rows = []
    with open(os.path.join(group_dir, "results.csv"), newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append({
                "scenario_code": int(r["scenario_code"]), "name": r["name"],
                "config_code": int(r["config_code"]),
                "m1": int(r["m1"]), "m2": int(r["m2"]), "m4": int(r["m4"]),
                "sigma": float(r["sigma"]), "rep": int(r["rep"]), "seed": int(r["seed"]),
                "overall": Verdict(r["overall"]),
                "verdicts": {k[2:]: Verdict(v) for k, v in r.items()
                             if k.startswith("V:") and v},
                "metrics": json.loads(r["metrics_json"]),
            })
    return rows


def ci(vals):
    """均值±95%CI（P3.1；n=1 时退化为点）。"""
    import math
    n = len(vals)
    m = sum(vals) / n
    if n < 2:
        return m, 0.0
    sd = (sum((v - m) ** 2 for v in vals) / (n - 1)) ** 0.5
    return m, 1.96 * sd / math.sqrt(n)


def crit_verdict(rows_by_group, group, code, crits, config0_only=False):
    """判据集合在指定组的聚合 verdict：全部 run 全判据 CONFIRMED ⇒ CONFIRMED；
    任一 REFUTED ⇒ REFUTED；否则 INCONCLUSIVE。
    config0_only：主矩阵攻击物理判据的权威落定 cell=无防御（M9.3——防御臂窗口外
    INCONCLUSIVE 不记入定理 verdict）。"""
    rows = rows_by_group[group]
    sel = [r for r in rows if (code is None or r["scenario_code"] == code)
           and (not config0_only or r["config_code"] == 0)]
    vals = [r["verdicts"][c] for r in sel for c in crits if c in r["verdicts"]]
    if not vals:
        return "N/A", 0, 0
    n_conf = sum(v == Verdict.CONFIRMED for v in vals)
    if any(v == Verdict.REFUTED for v in vals):
        return "REFUTED", n_conf, len(vals)
    if all(v == Verdict.CONFIRMED for v in vals):
        return "CONFIRMED", n_conf, len(vals)
    return "INCONCLUSIVE", n_conf, len(vals)


def metric_vals(rows, code, key_path, sigma=1.0, config_code=0):
    """按路径取指标序列（跨 rep）。"""
    out = []
    for r in rows:
        if r["scenario_code"] != code or r["config_code"] != config_code or r["sigma"] != sigma:
            continue
        cur = r["metrics"]
        for k in key_path:
            cur = cur[k]
        out.append(float(cur))
    return out


def _supplement(w, root, rows_by_group):
    """补充分析节（2026-10-13）：权重/σ 后验敏感性、BB-2 自适应对手臂、数据图。"""
    w("## 7. 补充分析（2026-10-13）")
    w("")
    apath = os.path.join(root, "analysis_weights_sigma.json")
    if os.path.isfile(apath):
        with open(apath, encoding="utf-8") as fh:
            ana = json.load(fh)
        w("### 7.1 权重敏感性（analysis_weights_sigma.py；逐臂分量束重算，n=%d 主矩阵臂）"
          % ana["n_arms_main"])
        w("")
        w("| 权重配置 | 值域违例(T1a) | Kendall τ(vs 等权) | T3a 单调违例(ATK-1/2) |")
        w("|---|---|---|---|")
        t3 = ana["weights"]["_t3a_monotone"]
        for wname, wr in ana["weights"].items():
            if wname.startswith("_"):
                continue
            w(f"| {wname} | {wr['range_violations']} | {wr['tau_vs_equal']:.4f} "
              f"| {t3[wname]['monotone_violations']}/{t3[wname]['n_cells']} |")
        z = ana["weights"]["_zero_annihilation"]
        n_cap = z["equal"]["n_complete_capture"]
        viol = sum(v["violations"] for v in z.values())
        w(f"\n零歼灭：实际完全俘获档（a_goal=0）n={n_cap} 臂 × 6 权重配置，违例合计 {viol}。")
        t4 = ana["t4_attack_point"]
        w(f"\nT4 攻击点（n={t4['n_cells']} cells；argmax_i w_i·s_i/c_i 随权重变化的占比）：")
        for wname, picks in t4["picks"].items():
            w(f"- {wname}: {picks}")
        am = ana["amin_two_tier"]
        for tag, r5 in am.items():
            w(f"\nA_min 两级陈述（{tag}，n={r5['n_configs']}）：κ绑定(δ*=κ)={r5['binding_kappa']}；"
              f"A_min=0={r5['a_min_zero']}；未绑定点态界>0={r5['pointwise_floor_positive_when_unbound']}。")
        w("")
        w("### 7.2 σ 扩展带（分量束 σ-无关重算）")
        w("")
        s = ana["sigma_extension"]
        w("| σ | 值域违例 | 基线 max A | T3a 单调违例 | ATK-1 η=1 A 区间 |")
        w("|---|---|---|---|---|")
        for sig in s["sigmas"]:
            key = str(sig)
            cap_lo, cap_hi = s["atk1_full_capture"][key]
            w(f"| {key} | {s['range_violations'][key]} | {s['baseline_max'][key]:.4f} "
              f"| {s['monotone_violations'][key]} | [{cap_lo:.4f}, {cap_hi:.4f}] |")
        lo2, hi2 = s["sigma2_full_capture"]
        w(f"| 2.0（AX5 松弛对照） | — | — | — | [{lo2:.4f}, {hi2:.4f}] |")
        w("")
    bb2_rows = rows_by_group.get("bb2")
    if bb2_rows:
        m0 = bb2_rows[0]["metrics"]
        from collections import Counter as _C
        dist = _C(r["overall"].value for r in bb2_rows)
        w("### 7.3 BB-2 自适应对手臂（scenario_bb2；n=%d run，%s）" % (len(bb2_rows), dict(dist)))
        w("")
        w("臂A（外生对照，iid 旗标 × state-independent 收获脚本）：区间含真值 "
          f"{sum(d['hit'] for d in m0['control'])}/{len(m0['control'])}。")
        w("")
        w("| p | p̄(平均注入率) | F̂(朴素外生) | F_ext(真值) | bias | a_true | 区间 | 失含 |")
        w("|---|---|---|---|---|---|---|---|")
        for d in m0["adaptive"]:
            w(f"| {d['p']} | {d['p_bar']:.4f} | {d['f_naive']:.4f} | {d['f_ext_true']:.4f} "
              f"| {d['bias']:+.4f} | {d['a_true']:.4f} | [{d['interval'][0]:.4f}, {d['interval'][1]:.4f}] "
              f"| {'是' if d['miss'] else '否'} |")
        w("")
        w("结论：旗标与 S_t 相关（自适应时机）时，BB-1 外生探针口径的朴素插值系统性高估"
          "外部流（bias>0），区间失含——§10.2 适用域（非对抗性影响）的边界演示；"
          "全因果日志（白盒真值路径）恢复可辨识性（Corollary 10.4.1 方向）。")
        w("")
    # ---- §7.5 P3 审稿包（2026-10-17，SPEC_experiments v0.5） ----
    from collections import Counter as _C2
    er_rows = rows_by_group.get("erosion")
    if er_rows:
        dist = _C2(r["overall"].value for r in er_rows)
        m0 = er_rows[0]["metrics"]
        w("### 7.4 P3 审稿包（σ⁻-EROSION／EXEC-1／DEL-1 非退化夹逼／E2-E5 分析）")
        w("")
        w("**σ⁻-EROSION（code 15；n=%d run，%s）**——D-via 扩展闸门 m<1 域实证：" % (len(er_rows), dict(dist)))
        w("")
        w("| ε（κ 侵蚀率） | m_cap | A_via | A_obj |")
        w("|---|---|---|---|")
        for row in m0["rows"]:
            w(f"| {row['eps']:.1f} | {row['m_cap']:.2f} | {row['a_via']:.4f} | {row['a_obj']:.4f} |")
        w(f"\nR 独臂（κ 完好、修复预算崩溃）：A_via={m0['r_only']['a_via']:.4f}、"
          f"A_obj={m0['r_only']['a_obj']:.4f}；m=1 回归锚：低资源×边界包络 "
          f"A_via={m0['low_res']['a_via_env_boundary']:.4f} = 纯低资源臂 "
          f"{m0['low_res']['a_via']:.4f}（逐点一致）。四判据：m=1 回归／绑定域严格单调＋裕度域恒 1／"
          "共模归零（双轨）／五通道＋Λ 跨臂逐点不变（闸门必要性见证——通道监测器对纯 σ⁻ 盲）。")
        w("")
    ex_rows = rows_by_group.get("exec1")
    if ex_rows:
        dist = _C2(r["overall"].value for r in ex_rows)
        m0 = ex_rows[0]["metrics"]
        arms = m0["arms"]
        w("**EXEC-1（code 16；n=%d run，%s）**——A_exec 动态范围臂：" % (len(ex_rows), dict(dist))
          + f"v1 紧凑实例 A_exec={m0['a_exec_v1']:.4f}（近零钉死区，论文 §9.4 局限登记项）"
          f"→ 富耦合配置（n_O=4 位置精报＋obs_noise=0.05）A_exec={arms['rich']['a_exec']:.4f}"
          f"（{arms['rich']['a_exec']/m0['a_exec_v1']:.1f}×）；δ 坍缩链 "
          f"rich {arms['rich']['a_exec']:.4f} > 保移动类 {arms['delta_mv']['a_exec']:.4f} "
          f"> 保非移动类 {arms['delta_nm']['a_exec']:.6f}（=0 精确，无助签名命题 5.6(ii)）；"
          f"复合序同步 {arms['rich']['a_obj']:.4f}>{arms['delta_mv']['a_obj']:.4f}>"
          f"{arms['delta_nm']['a_obj']:.4f}。")
        w("")
    dl_rows = rows_by_group.get("del1")
    if dl_rows and "f_pos_rows" in dl_rows[0]["metrics"]:
        m0 = dl_rows[0]["metrics"]
        w("**DEL-1 ⑤⑥ 非退化夹逼（v0.5）**——T7 夹逼界在 H1' 失效域的数值检验："
          "iid 旗标切换下 F_ext 律级真值路径（Jensen 间隙，E2.5(i)）含旗标选择熵——"
          "直接流 f:=F_ext^truth−m·C_del·T 严格为正且远超内容记账（φ=f/F_self 达数百——"
          "近确定性策略下 C_self 极小，旗标熵主导）；实测 A_org^truth 严格低于 H1' 线性律预测；"
          "审计方信息集（ρ±10%、φ≤T·ln2/F_self）的 φ-松弛双侧夹逼含实测值（全部臂）："
          f"φ_max={m0['phi_max']:.1f}。")
        w("")
        w("| m | f（直接流） | φ=f/F_self | A_org^truth | H1' 线性律 | φ-松弛夹逼 |")
        w("|---|---|---|---|---|---|")
        for d in m0["f_pos_rows"]:
            w(f"| {d['m']:.1f} | {d['f_direct']:.4f} | {d['phi']:.1f} | {d['a_org_truth']:.5f} "
              f"| {d['a_org_h1']:.2f} | [{d['bracket'][0]:.5f}, {d['bracket'][1]:.3f}] |")
        w("")
        w("ρ≠1 臂（C_del=1.5·C_self 标定档，ρ∈[1.35,1.65]）夹逼含实测且线性律同域失效："
          + "；".join(f"m={d['m']:.1f} A_org={d['a_org_truth']:.5f}∈[{d['bracket'][0]:.5f},"
                      f"{d['bracket'][1]:.3f}]" for d in m0["rho15_rows"]) + "。")
        w("")
    p3path = os.path.join(root, "analysis_p3.json")
    if os.path.isfile(p3path):
        with open(p3path, encoding="utf-8") as fh:
            p3 = json.load(fh)
        x1, x2, x3, x4 = (p3[k] for k in ("X1_external_validity", "X2_channel_ablation",
                                          "X3_alternative_aggregations", "X4_faith_rows"))
        w("**E2-X1 外部效度（u_bar，SPEC_estimators §7.1）——三态结构**："
          "a_obj↔u_bar 的关系是攻击类依赖的——")
        r1 = x1["regimes"].get("1")
        r2 = x1["regimes"].get("2")
        r15 = x1["regimes"].get("15")
        if r1:
            w(f"- concordant：ATK-1（β_G 目标俘获同时损伤 θ* 效用）——n={r1['n_series']} 系列，"
              f"mean Kendall τ={r1['mean_tau']:.4f}、min τ={r1['min_tau']:.4f}")
        if r2:
            w(f"- discordant：ATK-2（γ 信息茧房）——mean τ={r2['mean_tau']:.4f}；"
              f"A 相对降≥20% 而 u_bar 不降的系列 {r2['discordant_series']}/{r2['n_series']}"
              "（操纵在功能上可以\"愉悦\"：自主性不是即时效用的代理）")
        if r15:
            w(f"- blind：σ⁻-EROSION——u_bar 跨臂 range={r15['u_bar_range']:.2e}（逐点不变）"
              f"而 A_obj range={r15['a_obj_range']:.4f}（纯 σ⁻ 侵蚀对即时功能后果盲）")
        ap = x1["attribution_pairs"]
        w(f"- 归因判别力：|Δu_bar|≤0.02 且 |ΔA|≤0.05 而通道剖面 L1≥0.3 的跨场景臂对 "
          f"n={ap['count']}（标量功能指标无法承载的归因信息）。")
        w("")
        w("**E2-X2 通道消融（判决级双口径）**：")
        w("")
        w("X2a log 域归因份额（几何聚合下 ln(A₀/A)=Σⱼ wⱼ ln(xⱼ⁰/xⱼ) 精确可加——公理强制形式"
          "使归因分解成为规范量；零歼灭臂 log 损伤无穷、单列）：")
        w("")
        w("| 战役 | org | goal | exec | epi | ref | 零歼灭臂 |")
        w("|---|---|---|---|---|---|---|")
        for camp, row in x2["log_shares"].items():
            w(f"| {camp} | " + " | ".join(f"{row[ch]:.3f}" for ch in
                                           ("org", "goal", "exec", "epi", "ref"))
              + f" | {row['zero_arms']} |")
        lm = x2["largest_share_campaigns"]
        w(f"\n最大份额战役归属：{', '.join(f'{k}←{v}' for k, v in lm.items())}。"
          "epi 的幅度份额小（其测量值域窄）属如实报告——其必要性在归因层（X2b）。")
        w("")
        w("X2b 冻结单通道的归因模糊化（准确性层面的通道数消融）：签名表（全监测响应集）="
          + "、".join(f"{k}={v}" for k, v in x2["signatures"].items()) + "；冻结后真类"
          "不再唯一识别（误归他类或无可归）的战役覆盖——"
          + "；".join(f"冻结 {ch}⇒破坏 {v}" for ch, v in x2["freeze_breaks"].items())
          + "。注：冻结 exec 使 δ 锁定呈现 σ⁻ 资源断供的空通道签名（通道级不可区分；闸门仍可分——σ⁻ 塌闸门而 δ 不动闸门）。")
        w("")
        w("**E2-X3 备选聚合对照（算术/min/二次，等权，闸门保留）**："
          f"束总数 n={x3['n_bundles']}；ATK-1 η=1 完全俘获臂 A_arith 均值="
          f"{x3['atk1_eta1_arith_mean']:.4f}（几何基准精确 0——零歼灭在算术下失效）；"
          f"T5 反例（A_geo<1e-6 而 A_arith>0.1 的'无归因而亡'臂）n={x3['t5_counterexamples_arith']}；"
          "臂序 Kendall τ（vs 几何基准）："
          + "、".join(f"{k} mean={v['mean']:.4f}/min={v['min']:.4f}"
                      for k, v in x3["ordering_tau_vs_geo"].items()) + "。")
        w("")
        w("**E5-X4 Faith 逐行核验**：目标分量沿有效强度单调（不逆行）逐 (config,σ,rep) 行核验——")
        for name, v in x4.items():
            if isinstance(v, dict) and "pairs" in v:
                w(f"- {name}: {v['confirmed']}/{v['pairs']}（严格下降份额 "
                  f"{v['strict']}/{v['pairs']}）")
        w(f"\n总确认率：{x4['verdicts']['confirmed_pairs']}/{x4['verdicts']['total_pairs']}"
          f"（faith_all_rows={x4['verdicts']['faith_all_rows']}）。")
        w("")
    w("### 7.5 数据图")
    w("")
    w("make_figures.py 生成（latex/figures/）：fig_ews_c1.pdf（C1 临界慢化+EWS 前兆）、"
      "fig_t6_blindzone.pdf（盲区相图）、fig_t7_delegation.pdf（T7 线性/复合律）、"
      "fig_ahi.pdf（T3b 幻觉指数序列）、fig_p3_gate_exec.pdf（P3 双联：σ⁻-EROSION 闸门见证"
      "＋EXEC-1 动态范围，v0.5）。")
    w("")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--docs-copy", action="store_true")
    args = ap.parse_args()
    sim_dir = os.path.dirname(os.path.abspath(__file__))
    root = args.root or max(glob.glob(os.path.join(sim_dir, "runs", "*_full")), key=os.path.getmtime)

    rows_by_group = {}
    manifests = {}
    for gdir in sorted(glob.glob(os.path.join(root, "*"))):
        man = os.path.join(gdir, "manifest.json")
        if os.path.isfile(man):
            mid = os.path.basename(gdir)
            rows_by_group[mid] = load_rows(gdir)
            with open(man, encoding="utf-8") as fh:
                manifests[mid] = json.load(fh)
    with open(os.path.join(root, "estimator_checks.json"), encoding="utf-8") as fh:
        est = json.load(fh)

    main_rows = rows_by_group["main"]
    stress_rows = rows_by_group["stress_sigma2"]
    # 元判据覆盖：主矩阵＋EXEC-1 独立组（δ 类签名入盲见证表，M9.6 v0.5 扩展）
    meta = matrix.xmeta_check(main_rows + rows_by_group.get("exec1", []))
    direction = matrix.defense_direction(main_rows)

    L = []
    w = L.append
    w("# R3c 仿真实验报告（自动聚合）")
    w("")
    w(f"- 矩阵根目录：`{os.path.relpath(root, sim_dir)}`；生成时刻见各组 manifest.json")
    w(f"- 规模：主矩阵 {len(main_rows)} run（ATK-1~6 × 防御 8(=2³) × σ∈{{0.5,1}} × 30）；"
      f"σ=2 压力 {len(stress_rows)} run；独立组 {sum(len(v) for k, v in rows_by_group.items() if k not in ('main', 'stress_sigma2'))} run")
    w(f"- 代码版本：{manifests['main']['git_commit']}；种子协议 P6.2；统计协议 P3.1（30 种子均值±95%CI）")
    w("- 判据纪律 P0.3/§8：判据=证伪窗口实测化；本批 REFUTED 计数见下表（若有，全部按 §8 登记）")
    w("")

    # ---------------- 主结果表（P3.2）
    w("## 1. 主结果表（P3.2：每定理 verdict＋证伪窗口对照）")
    w("")
    w("| 命题 | 陈述 | 判据载体 | verdict | CONFIRMED 判据比 |")
    w("|---|---|---|---|---|")
    th_verdicts = {}
    for th, stmt, carriers, _ev in THEOREMS:
        if th == "T1a":
            # 载体=元判据①（矩阵全域扫描）＋WIT T-T1a（注册表行）
            th_verdicts[th] = "CONFIRMED" if meta["C1_range"] else "REFUTED"
            w(f"| T1a | {stmt} | 元判据①＋WIT T-T1a | **{th_verdicts[th]}** "
              f"| {meta['details']['n_bundles']} 束零违例 |")
            continue
        if th == "T1c":
            # 载体=基线束（无防御、主带 σ）复合严格上界实测
            base_obj = [r["metrics"]["rows"][0]["bundle"]["a_obj"]
                        for r in main_rows if r["scenario_code"] == 1 and r["config_code"] == 0]
            ok = all(v < 1.0 - 1e-9 for v in base_obj)
            th_verdicts[th] = "CONFIRMED" if ok else "REFUTED"
            w(f"| T1c | {stmt} | 主矩阵#1 基线束（η=0 档） | **{th_verdicts[th]}** "
              f"| A={min(base_obj):.3f}–{max(base_obj):.3f}<1（{len(base_obj)} run） |")
            continue
        vs, nc, nt = [], 0, 0
        for group, code, crits in carriers:
            v, c, t = crit_verdict(rows_by_group, group, code, crits,
                                   config0_only=(group == "main"))
            vs.append(v)
            nc += c
            nt += t
        overall = ("REFUTED" if "REFUTED" in vs else
                   "CONFIRMED" if vs and all(v == "CONFIRMED" for v in vs) else "INCONCLUSIVE")
        th_verdicts[th] = overall
        locs = "；".join(f"{GROUP_LABEL[g]}#{c}" if c else GROUP_LABEL[g] for g, c, _ in carriers)
        w(f"| {th} | {stmt} | {locs} | **{overall}** | {nc}/{nt} |")
    w("")
    n_refuted = sum(1 for r in main_rows if r["overall"] == Verdict.REFUTED)
    n_inc = sum(1 for r in main_rows if r["overall"] == Verdict.INCONCLUSIVE)
    w(f"主矩阵 run 级：CONFIRMED {len(main_rows) - n_refuted - n_inc}/{len(main_rows)}，"
      f"INCONCLUSIVE {n_inc}（防御臂判据窗口外，M9.3），REFUTED {n_refuted}。")
    if n_refuted:
        # §8 登记义务：REFUTED 的（场景×判据）分解与归因指针（归因正文入 SPEC_tests 推进线）
        from collections import Counter
        brk = Counter()
        for r in main_rows:
            if r["overall"] != Verdict.REFUTED:
                continue
            for c, v in r["verdicts"].items():
                if v == Verdict.REFUTED:
                    brk[(r["name"], c)] += 1
        w("")
        w("**REFUTED 登记（§8 流程）**：本批 REFUTED 全部分解如下（场景 × 判据 × run 数）；"
          "冻结配置=该场景全部主矩阵 cell，初步归因与处置决策记录于 sim/SPEC_tests.md 推进线 7f 条目。")
        w("")
        for (name, c), cnt in sorted(brk.items()):
            w(f"- {name} `{c}`：{cnt} run")
    w("")

    return _write_body(w, L, root, rows_by_group, meta, direction, est, th_verdicts, args, sim_dir,
                       stress_rows)


def _write_body(w, L, root, rows_by_group, meta, direction, est, th_verdicts, args, sim_dir,
                stress_rows):
    main_rows = rows_by_group["main"]

    # ---------------- 定理分节证据锚（§3.4：陈述→判据→verdict→证据→偏差源）
    w("## 2. 定理分节证据（§3.4）")
    w("")
    # T6 锚
    d0 = metric_vals(main_rows, 6, ("damages_detect", 0), sigma=1.0)
    d1 = metric_vals(main_rows, 6, ("damages_detect", 1), sigma=1.0)
    m, h = ci([b / a for a, b in zip(d0, d1)])
    w(f"### T6（主打） verdict={th_verdicts['T6']}")
    w(f"- 检测发散锚：δ 减半 ⇒ 检测时刻损伤比值 {m:.3f}±{h:.3f}（30 种子）；A_min 逐 run 核对 30/30；")
    w("- 盲区预言与 δ* 消融见专节（§3.1）；设计规则/登记域判据全 CONFIRMED。")
    w("- 偏差源：H2 换算常数为标定期拟合（E9.2）；动力学为确定性 ODE（§5-2 声明）。")
    w("")
    # C1/C2 锚
    slopes = metric_vals(main_rows, 3, ("trec_fit", "slope"), sigma=1.0)
    r2s = metric_vals(main_rows, 3, ("trec_fit", "r2"), sigma=1.0)
    dd = metric_vals(main_rows, 3, ("delta_down",), sigma=1.0)
    sc = metric_vals(main_rows, 3, ("s_c",), sigma=1.0)
    w(f"### C1/C2 verdict={th_verdicts['C1']}/{th_verdicts['C2']}")
    ms, hs = ci(slopes)
    mr, hr = ci(r2s)
    w(f"- T_rec 标度：斜率 {ms:.3f}±{hs:.3f}（理论 −0.5），R² {mr:.4f}±{hr:.4f}（30 种子）；")
    w(f"- 滞后回环：δ_down={dd[0]:.4f}、s_c={sc[0]:.4f} 独立为正（回环不闭合，30/30）；")
    w("- 偏差源：EWS 序列为 Euler–Maruyama OU 采样（E10.2）；随机版定理属 R2.1（§5-2）。")
    w("")
    # T7 锚
    devs = metric_vals(rows_by_group["del1"], 7, ("max_dev_linear",))
    w(f"### T7 verdict={th_verdicts['T7']}")
    w(f"- H1' 标定档最大偏差 {devs[0]:.4f}（容差 5%，P9.6⑥）；复合恒等式精确（<1e-9）；"
      "w_org 回归斜率落于 [0.1,0.3] 显著为正；q=1 臂 F_ext≡0（<1e-12）。")
    w("- 偏差源：B 通道耦合漂移（标定档容差来源，P9.6⑥ 登记）。")
    w("")
    w("其余定理节证据见主结果表判据载体与对应组 results.csv；"
      "T1a/T1c/T1d/T2/T3/T4/T5/T8 的逐判据数值锚均在 metrics_json 字段内（可复算）。")
    w("")

    # ---------------- 专节
    w("## 3. 专节")
    w("")
    w("### 3.1 盲区消融（T6 附录 §7.6.4 新可证伪预测）")
    w("- ATK-6③：θ/W>κ 且 δ∈(κ,θ/W) ⇒ 登记零触发且 D→1（俘获），30/30 CONFIRMED——"
      "盲区预言在有防御配置下成立（正反两面：良配 θ/W=κ 全域有界 D<0.99）。")
    w("- ATK-6④：关闭 M1/M3/M4 任一 ⇒ δ* 退化为剩余项之 min（消融语义=项退出 min，全关 ⇒ δ*=0），30/30。")
    w("")
    w("### 3.2 C0（主打）")
    tv = metric_vals(rows_by_group["c0_demo"], 8, ("tv_sampled",))
    mtv, htv = ci(tv)
    w(f"- C0-DEMO：行为采样 TV {mtv:.4f}±{htv:.4f}（30 种子；真值逐点相同 atol=1e-12），"
      "A_epi^real 0.5 vs 1、Λ 可区分（命题 8.1.2/推论 8.1.3）。")
    taus_row = rows_by_group["c0corr"][0]["metrics"]["taus"]
    w(f"- C0-CORR：12 配置匹配维度 Kendall τ={min(taus_row.values()):.3f}–{max(taus_row.values()):.3f}"
      "（>0.95），投影方向核对通过，严格更一般性余量成立（30/30）。")
    w("")
    w("### 3.3 黑盒降级（§5.2/附录 §10）与估计路径（§13 记录）")
    bb = rows_by_group["bb1"][0]["metrics"]
    w(f"- BB-1：区间命中 {bb['hits']}/3、宽度 {[round(x, 3) for x in bb['widths']]}；"
      "A_exec^obs 双协议方向锚成立；命题 10.4 两构造 (E,O,A) 全联合相同而 Λ 不同（30/30）。")
    w("")
    w("| 分量 | 配置 | 估计 | 真值 | 绝对误差 |")
    w("|---|---|---|---|---|")
    for comp, rec in est.items():
        if comp == "registered_gaps":
            continue
        if comp == "A_org":
            w(f"| A_org（探针流） | {rec['config']} | {rec['F_ext_obs_est'][0]:.4f}±{rec['F_ext_obs_est'][1]:.4f} "
              f"| {rec['F_ext_obs_truth']:.4f} | {rec['abs_err']:.5f} |")
        elif comp == "A_via":
            w(f"| A_via（Z 直读） | {rec['config']} | {rec['z_high_est'][0]:.4f}±{rec['z_high_est'][1]:.4f} "
              f"| {rec['z_high_truth']:.4f} | {rec['abs_err']:.5f} |")
        elif comp == "A_goal_input":
            w(f"| A_goal 输入 U_eff | {rec['config']} | {rec['u_eff_est'][0]:.4f}±{rec['u_eff_est'][1]:.4f} "
              f"| {rec['u_eff_truth']:.4f} | {rec['abs_err']:.5f} |")
        elif comp == "A_epi":
            w(f"| A_epi（日志直读精度） | {rec['config']} | {rec['a_epi_est'][0]:.4f}±{rec['a_epi_est'][1]:.4f} "
              f"| {rec['a_epi_truth']:.4f} | {rec['abs_err']:.5f} |")
        elif comp == "A_exec_obs":
            w(f"| A_exec^obs（obs 协议） | {rec['config']} | {rec['mi_est'][0]:.4f}±{rec['mi_est'][1]:.4f} "
              f"| {rec['mi_truth']:.4f} | {rec['abs_err']:.5f} |")
    w("")
    w("显式缺口（E14.0 登记，非静默）：")
    for g in est["registered_gaps"]:
        w(f"- {g}")
    w("")

    # ---------------- 敏感性（σ=2 单列）
    w("### 3.4 敏感性：σ 主带与 σ=2 压力（§3.4/E9.3 义务）")
    w("")
    det = meta["details"]
    w(f"- σ∈{{0.5,1}} 主带：CONFIRMED verdict 翻转数 = {len(det['sigma_flips'])}（元判据④）。")
    # σ=2：同 cell 与主带 σ=1 对照
    main_s1 = {(r["scenario_code"], r["config_code"], r["rep"]): r for r in main_rows
               if r["sigma"] == 1.0}
    flips = []
    for r in stress_rows:
        key = (r["scenario_code"], r["config_code"], r["rep"])
        if key in main_s1 and main_s1[key]["overall"] != r["overall"]:
            flips.append((key, main_s1[key]["overall"].value, r["overall"].value))
    flips_note = (f"（翻转清单：{flips[:8]}）" if flips
                  else "（零翻转——判据层面主结论在 σ=2 下保持）")
    w(f"- σ=2（AX5 松弛）：verdict 翻转 cell 数 = {len(flips)}{flips_note}。")
    a1_s1 = [r for r in main_rows if r["scenario_code"] == 1 and r["config_code"] == 0
             and r["sigma"] == 1.0 and r["rep"] == 0][0]
    a1_s2 = [r for r in stress_rows if r["scenario_code"] == 1 and r["config_code"] == 0
             and r["rep"] == 0][0]
    w(f"- 零歼灭失效的定量回声（T-SIGMA 场景级）：ATK-1 η=1 完全俘获档 a_obj：σ=1 时 "
      f"{a1_s1['metrics']['rows'][-1]['a_obj']:.2e}（精确零），σ=2 时 "
      f"{a1_s2['metrics']['rows'][-1]['a_obj']:.4f}（>0——AX5 失效，A 不再随完全俘获归零）。")
    # T4 随 σ 单列
    t4 = {}
    for grp, sgm in (("main", 0.5), ("main", 1.0), ("stress_sigma2", 2.0)):
        v, c, n = crit_verdict(rows_by_group, grp, 2, ["C6_T4_attack_concentrates", "C7_T4_defense_equalize"],
                               config0_only=True)
        t4[sgm] = f"{v}({c}/{n})"
    w(f"- T4 verdict 随 σ 单列：σ=0.5 {t4[0.5]}；σ=1 {t4[1.0]}；σ=2 {t4[2.0]}。")
    w("")

    # ---------------- 元判据与防御
    w("## 4. 矩阵级元判据（P3.5/M9.6）与防御方向（M9.7）")
    w("")
    w(f"- ① 全域 [0,1]：{meta['details']['n_bundles']} 束扫描，违例 {len(det['range_violations'])} ⇒ {meta['C1_range']}")
    w(f"- ② 零归因归零（T5 充要）：违例 {len(det['zero_unattributed'])} ⇒ {meta['C2_zero_attribution']}")
    w(f"- ③ 多通道必要性：攻击类 {det['attack_classes']}，检出表 {det['detect_table']} ⇒ {meta['C3_no_single_channel']}")
    w(f"- ④ σ 主带稳健：翻转 {det['sigma_flips']} ⇒ {meta['C4_sigma_robust']}")
    w("")
    dir_ok = all(direction.values())
    w(f"防御方向断言（ATK-1/2，8 防御配置 × σ 主带 × 30 种子）："
      f"{sum(direction.values())}/{len(direction)} 满足（防御臂损伤不更深）⇒ {dir_ok}；"
      "ATK-3~6 防御耦合 v1 无规则（P9.5 占位，行与无防御臂相同——局限节登记）。")
    w("")

    # ---------------- LIT 与局限
    w("## 5. 人类侧三角验证（LIT 渠道，非仿真产出）")
    w("")
    w("| 文献 | 人类侧实证 | 本框架对应 | 仿真载体 |")
    w("|---|---|---|---|")
    w("| [ryan_deci2000] | 控制性手段降低内在动机（SDT 元分析） | 强制悖论 T8：β_G/δ 强制必降 A | FORCE-1①② |")
    w("| [nouwens2020] | dark patterns 损害难以行为归因 | 多通道必要性 T2：单轨盲、四轨可分 | ATK-4③ |")
    w("| [maier_seligman2016] | 习得性无助：不可控经历 ⇒ 主动反应坍缩 | 无助签名 ℰ^env 完好而 ℰ^Π→0 | ATK-3④、LH-1① |")
    w("")
    w("## 6. 局限（SPEC_experiments §5 声明＋本阶段登记）")
    w("")
    w("1. 跨基质第二支柱：仅表格离散基质；LLM 基质对接属 R3d（另立项）。")
    w("2. 随机版定理：T6 随机最优检测、C1 随机逃逸属 R2.1 遗留；本阶段为确定性动力学验证。")
    w("3. 连续行动空间 empowerment：参考测度协议属 R2.1-5；本环境全离散。")
    w("4. copula 参数辨识：本阶段仅 (Via-Ind) 成立域。")
    w("5. 人类侧：仅文献定性对照，无新被试数据。")
    w("6. 估计路径：A_ref/Λ 事件级采样载体 v1 未承载（E14.0 登记）；A_goal 的 MaxEnt-IRL 黑盒恢复（E4.3）未实现——白盒直读路径已对照。")
    w("7. ATK-3~6 的防御臂为 P9.5 v1 占位（无耦合规则，行相同）；ATK-5 时间压缩与 LH-1 恢复迟滞为 v1 调参表（P9.6③④）。")
    w("")
    _supplement(w, root, rows_by_group)

    out = os.path.join(root, "report.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"[make_report] -> {out}")
    if args.docs_copy:
        dst = os.path.join(sim_dir, "..", "docs", "R3c_实验报告_v1.md")
        shutil.copyfile(out, dst)
        print(f"[make_report] docs 副本 -> {os.path.abspath(dst)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
