#!/usr/bin/env python3
"""X5 构造效度敏感性臂（2026-10-22，审稿 R8-1：threats (x) 三注册臂中成本最低的
前两臂——x-a 背书量化网格、x-b 认知粗粒化 κ——本修订直接运行；x-c Λ 反事实模型臂
保持注册未运行）。规约：SPEC_experiments v0.6 §8 X5；平台前提：SPEC_platform v0.3
（κ 细化感知派生 P2.4／endorse_step P3.2／植入目标与桶先验通用化 P9.3）。

与后验重算族（analysis_weights_sigma/analysis_exec1_weights）不同：X5 两臂为
**架构级重跑**（量化/κ 同时进入动力学与评分，非仅复合层重算），但真值模式
确定性 ⇒ 种子惰性（M9.1），秒级完成。默认档逐点还原 v0.2 ⇒ 与归档矩阵
（runs/<root>/main）交叉核对为零漂移回归钉。

X5-a 背书图量化（ATK-1 重跑，C1–C5 × 8 防御配置，σ=1）：
  档位 coarse（endorse_step=2：同 4 点网格、地板平台加倍 ⇒ Endorse 常值化于 θ*）／
  default（v0.2 表式）／fine（n_θ=7，k=2 索引细化，效用行线性插值——本臂登记建模
  选择；A_goal 读数纯由 G 链决定、与策略无关，插值不混杂目标通道结论）／
  finest（n_θ=13，k=4）。
  证伪器（threats (x-a) 注册文本）：verdict 翻转，或 dc-归一 A_goal 读数在细化
  方向超出注册容差——容差于执行时显式定为两把注册标尺：SESOI 0.01（绝对）与
  5%（相对，T7 标定带同型）；粗化方向偏移单列（量化 κ_grid 登记义务非空洞）。
  解析参照：连续收缩（c=0.5）平稳解闭式 A_goal^∞(η)=1−2η/(1+η)；默认网格与
  极限的间隙闭式 η(1−η)²/(2(1+η))，max≈0.0566——数值档须几何速率收敛（校验）。

X5-b κ 粗粒化（ATK-2 网格重评分，s(γ)∈{0,0.3,0.6,1.0} × 8 防御配置，σ=1）：
  档位 degenerate（n_B=1：κ≡0 ⇒ A_epi≡1 构造性无信息——边界见证，不入 verdict）／
  default（n_B=n_O=2 半环，v0.2 逐点还原）／fine（n_B=n_O=4 位置精确——κ 分辨率
  的可观测上限，u 不被观察）。
  证伪器（threats (x-b) 注册文本）：细化下 A_epi 对 s(γ) 的响应非单调或变号。
  档位间基线水平漂移如实报告——即 (eq:aepi) 的 κ 敏感性报告义务本身。

用法：python3 analysis_sensitivity_arms.py [--root runs/20261017_full]
产出：analysis_sensitivity_arms.json（机读归档）＋ stdout 摘要
（论文 threats (x) 改写与 §8.5 X5 段的数据源）。
"""
import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from autonomy_sim import interventions  # noqa: E402
from autonomy_sim.env0 import Env0Config, build_env0, refined_theta_table  # noqa: E402
from autonomy_sim.scenarios import defense_scaled_strength, scenario_atk1  # noqa: E402
from autonomy_sim.wiring import truth_bundle  # noqa: E402

ETAS = (0.0, 0.2, 0.5, 0.9, 1.0)          # ATK-1 强度网格（主矩阵同式）
S_GRID = (0.0, 0.3, 0.6, 1.0)              # ATK-2 强度网格（主矩阵同式）
DEFS = tuple((m1, m2, m4)
             for m1 in (0, 1) for m2 in (0, 1) for m4 in (0, 1))  # 8 防御配置
TOL_ABS = 0.01     # SESOI（论文 §8.2 注册最小效应）
TOL_REL = 0.05     # 5% 相对标尺（T7 标定带同型）
T = 2
T_STAT = 8   # 平稳补充视界：吸收瞬态在各档均已消失（隔离平稳量化间隙用）

# 归档锚（runs/20261017_full main，config 0，σ=1）：默认档必须逐点还原
ARCHIVE_AGOAL_UNDEF = [1.0, 0.72, 0.375, 0.055, 0.0]        # ATK-1 η 网格
ARCHIVE_AEPI_UNDEF = [0.811, 0.718, 0.625, 0.500]           # ATK-2 s 网格（论文 3 位舍入）


def xa_levels() -> dict:
    """X5-a 档位注册表（coarse/default/fine/finest）。"""
    return {
        "coarse": Env0Config(endorse_step=2),
        "default": Env0Config(),
        "fine": Env0Config(n_theta=7, theta_star=2, theta_table=refined_theta_table(2)),
        "finest": Env0Config(n_theta=13, theta_star=4, theta_table=refined_theta_table(4)),
    }


def a_goal_continuum(eta: float) -> float:
    """连续收缩（c=0.5）细化极限的平稳解：u−1=4η/(1+η) ⇒ A=1−2η/(1+η)。"""
    return 1.0 - 2.0 * eta / (1.0 + eta)


def a_goal_gap_closed_form(eta: float) -> float:
    """默认网格读数与连续极限的间隙：|(3η−η²)/2 − 2η/(1+η)| = η(1−η)²/(2(1+η))。"""
    return eta * (1.0 - eta) ** 2 / (2.0 * (1.0 + eta))


def a_goal_curve(cfg: Env0Config, etas, T: int) -> list:
    """A_goal(η) 曲线直读（纯 G 链：propagate 边缘 + truth_A_goal 评分）。

    与 wiring._truth_components_impl 的 A_goal 口径同式（np.dot 边缘均值 +
    endorse_fn 网格评分），但绕开 truth_bundle 的 DI/赋能枚举——后者随 T
    指数增长（历史树），大视界平稳补充只能走本直读路径（T=2 时二者一致，
    由主臂的归档回归钉保证）。
    """
    import numpy as np
    from autonomy_sim import propagate
    from autonomy_sim.components import truth_A_goal
    from autonomy_sim.env0 import endorse_table
    from autonomy_sim.scenarios import maximal_alienation_target
    m0 = build_env0(cfg)
    target = maximal_alienation_target(cfg)
    etab = endorse_table(cfg)
    endorse_fn = lambda u: float(etab[int(round(u))])
    out = []
    for eta in etas:
        mg = interventions.apply_beta_g(
            m0, interventions.BetaGSpec.plant(eta, target))
        al = mg.alphabet
        g_marg = propagate.truth_step_joints(mg, T)[-1]["S"].reshape(
            al.n_G, al.n_B, al.n_M, al.n_R).sum(axis=(1, 2, 3))
        u_eff = float(np.dot(g_marg, np.arange(al.n_G)))
        gres = truth_A_goal(u_eff, endorse_fn, [float(i) for i in range(al.n_G)])
        out.append(float(gres.point if not gres.degenerate else gres.hi))
    return out


def run_xa() -> dict:
    """X5-a：ATK-1 四档重跑（C1–C5 × 8 防御配置）＋解析极限校验。

    主臂在战役视界 T=2 上跑（与归档矩阵同口径，证伪器在此评估）；细化网格的
    背书吸收链更长（6→4→3→2 需 3 步；finest 需 4 步），T=2 截断吸收瞬态 ⇒
    另跑平稳补充（T=8，各档瞬态已消失）隔离"平稳量化间隙"与"瞬态"两个机制。
    """
    out = {"levels": {}, "tolerances": {"abs": TOL_ABS, "rel": TOL_REL}}
    curves = {}   # level -> {config: [a_goal per η]}（T=2 主臂）
    verdicts = {}  # level -> {config: {criterion: verdict}}
    stat_curves = {}  # level -> [a_goal per η]（T=8 平稳补充，无防御 cell）
    for name, cfg in xa_levels().items():
        per_cfg, per_verdict = {}, {}
        for d in DEFS:
            res = scenario_atk1(etas=ETAS, cfg=cfg, T=T, defense=d, sigma=1.0)
            per_cfg[str(d)] = [float(r["a_goal"]) for r in res.metrics["rows"]]
            per_verdict[str(d)] = {k: v.value for k, v in res.verdicts.items()}
        curves[name], verdicts[name] = per_cfg, per_verdict
        stat_curves[name] = a_goal_curve(cfg, ETAS, T_STAT)
        out["levels"][name] = {
            "cfg_delta": {k: v for k, v in (
                ("endorse_step", cfg.endorse_step), ("n_theta", cfg.n_theta),
                ("theta_star", cfg.theta_star))},
            "curve_undefended_T2": per_cfg[str((0, 0, 0))],
            "curve_undefended_T8_stationary": stat_curves[name],
        }
    # 归档回归钉：default 档无防御 cell 逐点还原归档矩阵值
    dflt = curves["default"][str((0, 0, 0))]
    archive_diff = max(abs(a - b) for a, b in zip(dflt, ARCHIVE_AGOAL_UNDEF))
    # verdict 翻转核验（逐 (config, criterion) 对 default 档）
    flips = []
    for d in DEFS:
        key = str(d)
        for crit, v in verdicts["default"][key].items():
            for name in curves:
                if name != "default" and verdicts[name][key][crit] != v:
                    flips.append({"level": name, "config": key, "criterion": crit,
                                  "default": v, "level_verdict": verdicts[name][key][crit]})
    # 读数偏移（逐档位对、逐配置、逐 η 的最大绝对偏移）
    def max_shift(lvl_a, lvl_b):
        best, at = 0.0, None
        for key in curves[lvl_a]:
            for i, (a, b) in enumerate(zip(curves[lvl_a][key], curves[lvl_b][key])):
                if abs(a - b) > best:
                    best, at = abs(a - b), {"config": key, "eta": ETAS[i],
                                            "from": a, "to": b}
        return {"abs_max": best, "at": at}
    shifts = {
        "coarse_vs_default": max_shift("default", "coarse"),
        "default_to_fine": max_shift("default", "fine"),
        "fine_to_finest": max_shift("fine", "finest"),
    }
    # 解析极限：闭式校验（平稳补充 T=8 上：数值档收敛 + 默认档间隙闭式逐点核对）
    etas_dense = [i / 200 for i in range(201)]
    gap_max = max(a_goal_gap_closed_form(e) for e in etas_dense)
    lim = [a_goal_continuum(e) for e in ETAS]
    gap_cf = [a_goal_gap_closed_form(e) for e in ETAS]
    conv = {}
    for name in ("default", "fine", "finest"):
        arr = stat_curves[name]
        conv[name] = float(max(abs(a - b) for a, b in zip(arr, lim)))
    default_gap_check = float(max(
        abs((stat_curves["default"][i] - lim[i]) - gap_cf[i]) for i in range(len(ETAS))))
    transient_T2 = {
        name: {"eta0_reading_T2": curves[name][str((0, 0, 0))][0],
               "eta0_reading_T8": stat_curves[name][0]}
        for name in ("default", "fine", "finest")}
    # 证伪器判定
    ref_dir = [shifts["default_to_fine"]["abs_max"], shifts["fine_to_finest"]["abs_max"]]
    out.update({
        "archive_reproduction": {"archived": ARCHIVE_AGOAL_UNDEF,
                                 "recomputed": [round(x, 6) for x in dflt],
                                 "max_abs_diff": archive_diff},
        "verdict_flips": flips,
        "shifts": shifts,
        "continuum_limit": {
            "formula": "A_goal_inf(eta) = 1 - 2*eta/(1+eta)",
            "gap_formula_default_grid": "eta*(1-eta)^2/(2*(1+eta))",
            "gap_closed_form_max": gap_max,
            "curve": [round(x, 6) for x in lim],
            "horizon": "T=8 stationary supplement (absorption transients gone at every level)",
            "default_gap_closed_form_pointwise_check": default_gap_check,
            "max_abs_dist_to_limit_stationary": conv,
            "convergence_ratios_stationary": {
                "fine/default": conv["fine"] / conv["default"] if conv["default"] else None,
                "finest/fine": conv["finest"] / conv["fine"] if conv["fine"] else None},
            "stationary_shifts": {
                "default_to_fine": float(max(abs(a - b) for a, b in zip(
                    stat_curves["default"], stat_curves["fine"]))),
                "fine_to_finest": float(max(abs(a - b) for a, b in zip(
                    stat_curves["fine"], stat_curves["finest"])))},
            "T2_absorption_transient": transient_T2,
        },
        "falsifier": {
            "verdict_disjunct_fired": bool(flips),
            "reading_disjunct_fired_abs": any(x > TOL_ABS for x in ref_dir),
            "reading_disjunct_fired_rel": None,  # 下方填充（相对标尺，基线≥0.05 档）
            "max_refinement_shift_abs": max(ref_dir),
        },
    })
    # 相对标尺（仅在 default 读数 ≥0.05 处有意义——近零端相对偏移无定义）
    rel_worst, rel_at = 0.0, None
    for key in curves["default"]:
        for i, (a, b) in enumerate(zip(curves["default"][key], curves["fine"][key])):
            if a >= 0.05 and abs(a - b) / a > rel_worst:
                rel_worst, rel_at = abs(a - b) / a, {"config": key, "eta": ETAS[i]}
    out["falsifier"]["reading_disjunct_fired_rel"] = rel_worst > TOL_REL
    out["falsifier"]["max_refinement_shift_rel"] = {"value": rel_worst, "at": rel_at}
    return out


def run_xb() -> dict:
    """X5-b：ATK-2 网格三档 κ 重评分（s × 8 防御配置）＋退化档边界见证。"""
    levels = {
        "degenerate": Env0Config(n_B=1),
        "default": Env0Config(),
        "fine": Env0Config(n_B=4, n_O=4),
    }
    out = {"levels": {}}
    series = {}  # level -> {config: [a_epi per s]}
    for name, cfg in levels.items():
        m0 = build_env0(cfg)
        per_cfg = {}
        for d in DEFS:
            vals = []
            for s in S_GRID:
                s_eff = defense_scaled_strength(s, d, gate_class=False)
                mg = interventions.apply_gamma(
                    m0, interventions.GammaSpec.mix_constant(s_eff, symbol=0))
                vals.append(float(truth_bundle(mg, T=T, baseline=m0, sigma=1.0).a_epi))
            per_cfg[str(d)] = vals
        series[name] = per_cfg
        base = per_cfg[str((0, 0, 0))]
        monotone = all(all(x >= y - 1e-9 for x, y in zip(v, v[1:]))
                       for v in per_cfg.values())
        strict = all(v[0] > v[-1] + 1e-9 for v in per_cfg.values())
        out["levels"][name] = {
            "kappa": {"degenerate": "kappa==0 (constant)", "default": "half-ring (n_B=2)",
                      "fine": "position-exact (n_B=4)"}[name],
            "curve_undefended": [round(x, 6) for x in base],
            "baseline_undefended": base[0],
            "deep_capture_undefended": base[-1],
            "monotone_non_increasing_all_configs": monotone,
            "strictly_down_all_configs": strict,
        }
    # 归档回归钉：default 档无防御 cell 还原论文归档系列（3 位舍入值）
    dflt = series["default"][str((0, 0, 0))]
    archive_diff = max(abs(a - b) for a, b in zip(dflt, ARCHIVE_AEPI_UNDEF))
    # 证伪器：细化档（default/fine）单调且不变号；退化档构造性无信息、不入 verdict
    fine_ok = (out["levels"]["fine"]["monotone_non_increasing_all_configs"]
               and out["levels"]["fine"]["strictly_down_all_configs"])
    dflt_ok = (out["levels"]["default"]["monotone_non_increasing_all_configs"]
               and out["levels"]["default"]["strictly_down_all_configs"])
    degen_flat = all(abs(v - 1.0) < 1e-12 for v in series["degenerate"][str((0, 0, 0))])
    out.update({
        "archive_reproduction": {"archived_rounded": ARCHIVE_AEPI_UNDEF,
                                 "recomputed": [round(x, 6) for x in dflt],
                                 "max_abs_diff_vs_rounded": archive_diff},
        "baseline_drift_across_levels": {
            name: out["levels"][name]["baseline_undefended"] for name in levels},
        "falsifier": {
            "fired": not (fine_ok and dflt_ok),
            "default_monotone_strict": dflt_ok,
            "fine_monotone_strict": fine_ok,
            "degenerate_witness": {
                "a_epi_identically_one": degen_flat,
                "status": "boundary witness only (channel uninformative by "
                          "construction); not a verdict row"},
        },
    })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None,
                    help="（可选）归档矩阵根目录，仅用于 JSON 元数据登记")
    args = ap.parse_args()
    result = {
        "meta": {
            "date": "2026-10-22",
            "spec": "SPEC_experiments v0.6 §8 X5; SPEC_platform v0.3",
            "review_item": "R8-1 (run the two low-cost registered sensitivity arms)",
            "archive_root": args.root or "(not read; deterministic truth-mode rerun)",
            "modes": "truth mode, deterministic; seed-inert (M9.1)",
            "tolerances": {"abs_SESOI": TOL_ABS, "rel": TOL_REL},
            "x_c_status": "registered, not run (deferred per reviewer R8-1)",
        },
        "x_a_endorsement_quantization": run_xa(),
        "x_b_kappa_refinement": run_xb(),
    }
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "analysis_sensitivity_arms.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    # stdout 摘要
    xa, xb = result["x_a_endorsement_quantization"], result["x_b_kappa_refinement"]
    print("== X5-a 背书量化（ATK-1 四档重跑）==")
    for name in ("coarse", "default", "fine", "finest"):
        lv = xa["levels"][name]
        print(f"  {name:8s} 无防御 a_goal(η) T=2 =",
              [round(x, 4) for x in lv["curve_undefended_T2"]])
        print(f"  {name:8s} 无防御 a_goal(η) T=8 =",
              [round(x, 4) for x in lv["curve_undefended_T8_stationary"]])
    cl = xa["continuum_limit"]
    print("  连续极限(T=8 参照) =", cl["curve"])
    print("  归档还原 max|diff| =", xa["archive_reproduction"]["max_abs_diff"])
    print("  verdict 翻转 =", len(xa["verdict_flips"]))
    print("  T=2 偏移:", {k: round(v["abs_max"], 4) for k, v in xa["shifts"].items()})
    print("  T=8 平稳偏移:", {k: round(v, 4) for k, v in cl["stationary_shifts"].items()})
    print("  平稳到极限距离:", {k: round(v, 4) for k, v in
                            cl["max_abs_dist_to_limit_stationary"].items()})
    print("  默认档间隙闭式逐点核对 max|diff| =",
          round(cl["default_gap_closed_form_pointwise_check"], 12),
          "; 闭式 max =", round(cl["gap_closed_form_max"], 4))
    print("  T=2 吸收瞬态(η=0):", {k: (round(v["eta0_reading_T2"], 4),
                                  round(v["eta0_reading_T8"], 4))
                                  for k, v in cl["T2_absorption_transient"].items()})
    print("  证伪器:", xa["falsifier"])
    print("== X5-b κ 细化（ATK-2 网格重评分）==")
    for name in ("degenerate", "default", "fine"):
        lv = xb["levels"][name]
        print(f"  {name:11s} ({lv['kappa']}): a_epi(s) =", lv["curve_undefended"],
              "单调严格降:", lv["strictly_down_all_configs"])
    print("  归档还原 max|diff|(vs 3位舍入) =",
          round(xb["archive_reproduction"]["max_abs_diff_vs_rounded"], 6))
    print("  证伪器:", xb["falsifier"])
    print("[out]", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
