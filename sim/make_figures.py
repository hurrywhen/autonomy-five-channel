#!/usr/bin/env python3
"""论文数据图生成（2026-10-13 补充；2026-10-15 数据切到审稿修复批 runs/20261015_full）。

图清单（输出 latex/figures/fig_*.pdf，matplotlib 原生 PDF，无外部依赖）：
  fig_ews_c1.pdf       C1 临界慢化：T_rec∝(δc−δ)^{−1/2} 标度（确定性拟合）
                       + EWS 前兆（平稳方差/AR(1) 随 δ→δc 的发散，种子带）
  fig_t6_blindzone.pdf T6 盲区相图（θ/W=0.2 固定，(δ, κ) 平面三区：
                       修复全域 / 盲区俘获 / 登记域）+ ATK-6 仿真锚点
  fig_t7_delegation.pdf T7 委托律：A_org=1−m 线性（max_dev 标注）+
                       复合律 A=A_self(1−m)^{w_org} 拟合
  fig_ahi.pdf          T3b 幻觉指数：A_obj 降、Â_phen 不降、AI 差距随 s(γ) 增长
  fig_p3_gate_exec.pdf P3 双联（2026-10-17）：左=σ⁻-EROSION 闸门必要性见证
                       （A_via/A_obj 随 ε 塌缩而五通道逐点不动）；右=EXEC-1
                       A_exec 动态范围（v1 钉死区 vs 富耦合基线/δ 坍缩链）

口径：只读既有 artifacts；确定性量（t_rec 标度、盲区边界）直接重算（同一
确定性函数，M9.4 口径），随机量（OU 前兆）取全矩阵 480 行 × 30 种子。
用法：python3 make_figures.py [--root runs/YYYYMMDD_full（缺省最新批）] [--out ../latex/figures]
"""
import argparse
import csv
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from autonomy_sim import dynamics  # noqa: E402

plt.rcParams.update({
    "font.size": 8.5, "font.family": "serif",
    "axes.labelsize": 9, "axes.titlesize": 9.5, "legend.fontsize": 8,
    "figure.dpi": 150, "savefig.bbox": "tight",
    # R9：Type 3 字体无 ToUnicode 映射（pdffonts uni=no），审稿端文本抽取会得到
    # 图区乱码——改 TrueType 嵌入（fonttype 42），图内文字可抽取、可复制、可检索。
    "pdf.fonttype": 42, "ps.fonttype": 42,
})


def _rows(root, group):
    with open(os.path.join(root, group, "results.csv"), newline="",
              encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def fig_ews_c1(root, out):
    rows = [r for r in _rows(root, "main") if r["scenario_code"] == "3"]
    eps_v = 0.8
    d_c = eps_v / 4.0
    ds_fit = np.array([0.08, 0.10, 0.13, 0.16, 0.18])
    t_recs = np.array([dynamics.measure_t_rec(float(d), eps_v, T=800.0) for d in ds_fit])
    lx, ly = np.log(d_c - ds_fit), np.log(t_recs)
    slope, intercept = np.polyfit(lx, ly, 1)
    # EWS 随机前兆：全部行的 ews（δ, var, ar1）
    ews_pts = []
    for r in rows:
        for e in json.loads(r["metrics_json"])["ews"]:
            ews_pts.append((e["delta"], e["var"], e["ar1"]))
    ews_pts = np.array(ews_pts)
    # (b) 轴标签交叠修复（2026-10-21 审稿）：缩短 x 轴标签、加 labelpad、图例上移
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.9, 3.0))
    ax1.plot(d_c - ds_fit, t_recs, "o", ms=4.5, color="black", label="measured $T_{rec}$")
    xs = np.linspace((d_c - ds_fit).min() * 0.9, (d_c - ds_fit).max() * 1.1, 100)
    ax1.plot(xs, np.exp(intercept) * xs ** slope, "-", lw=1.2, color="tab:red",
             label=rf"fit: slope ${slope:.3f}$ (theory $-0.5$)")
    ax1.set_xscale("log"); ax1.set_yscale("log")
    from matplotlib.ticker import LogLocator, NullLocator
    ax1.xaxis.set_major_locator(LogLocator(base=10.0, numticks=4))
    ax1.xaxis.set_minor_locator(NullLocator())
    ax1.set_xlabel(r"distance to criticality $\delta_c-\delta$")
    ax1.set_ylabel(r"recovery time $T_{rec}$")
    ax1.legend(frameon=False, loc="upper right")
    # 图内只留坐标/panel 信息（结论性标题一律入图注，2026-10-22 审稿 R5）
    ax1.set_title("(a)", loc="left", fontsize=8.5)
    for d in (0.10, 0.15, 0.18):
        sel = ews_pts[ews_pts[:, 0] == d]
        var_m, var_s = sel[:, 1].mean(), sel[:, 1].std()
        ax2.errorbar([d], [var_m], yerr=[1.96 * var_s / math.sqrt(len(sel))],
                     fmt="s", ms=4, color="tab:blue", capsize=2.5,
                     label="stationary variance" if d == 0.10 else None)
    ax2.set_xlabel(r"$\delta$ ($\delta_c=0.2$)", labelpad=1.5)
    ax2.set_ylabel("stationary variance", color="tab:blue", labelpad=1.5)
    ax2.tick_params(axis="y", labelcolor="tab:blue")
    ax2b = ax2.twinx()
    for d in (0.10, 0.15, 0.18):
        sel = ews_pts[ews_pts[:, 0] == d]
        ar_m, ar_s = sel[:, 2].mean(), sel[:, 2].std()
        ax2b.errorbar([d + 0.004], [ar_m], yerr=[1.96 * ar_s / math.sqrt(len(sel))],
                      fmt="^", ms=4, color="tab:orange", capsize=2.5,
                      label="AR(1) coefficient" if d == 0.10 else None)
    ax2b.set_ylabel("AR(1) coefficient", color="tab:orange", labelpad=1.5)
    ax2b.tick_params(axis="y", labelcolor="tab:orange")
    ax2.set_title("(b)", loc="left", fontsize=8.5)
    h1, l1 = ax2.get_legend_handles_labels()
    h2, l2 = ax2b.get_legend_handles_labels()
    ax2.legend(h1 + h2, l1 + l2, frameon=False, loc="upper left", fontsize=7)
    fig.tight_layout()
    p = os.path.join(out, "fig_ews_c1.pdf")
    fig.savefig(p)
    plt.close(fig)
    print("[fig]", p, f"slope={slope:.4f}")


def fig_t6_blindzone(root, out):
    theta_w = 0.2  # ATK-6: theta=0.4, W=2.0
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    d_max, k_max = 0.55, 0.4
    D, K = np.meshgrid(np.linspace(0, d_max, 400), np.linspace(0, k_max, 400))
    repair = D <= K
    blind = (D > K) & (D < theta_w)
    reg = D >= theta_w
    ax.imshow(repair.astype(float), extent=(0, d_max, 0, k_max), origin="lower",
              aspect="auto", cmap=matplotlib.colors.ListedColormap(["none", "#d9ead3"]))
    ax.imshow(blind.astype(float), extent=(0, d_max, 0, k_max), origin="lower",
              aspect="auto", cmap=matplotlib.colors.ListedColormap(["none", "#f4cccc"]))
    ax.imshow(reg.astype(float), extent=(0, d_max, 0, k_max), origin="lower",
              aspect="auto", cmap=matplotlib.colors.ListedColormap(["none", "#fff2cc"]))
    ax.plot([0, theta_w], [0, theta_w], "k-", lw=1.0)
    ax.axvline(theta_w, color="k", lw=1.0)
    ax.text(0.245, 0.325, "registered domain\n($\\delta\\geq\\theta/W$):\nM1 rollback cycles",
            fontsize=7.5)
    ax.text(0.03, 0.30, "repair-dominated\n($\\delta\\leq\\kappa$):\n$\\limsup D\\leq\\delta/\\kappa$",
            fontsize=7.5)
    ax.text(0.115, 0.045, "blind zone\n($\\kappa<\\delta<\\theta/W$)", fontsize=7.5,
            color="#990000")
    # ATK-6 锚点：θ/W=0.2, κ_good=0.2 设计规则臂（蓝）；盲区臂 κ_bad=0.1, δ=0.15（红）
    for d in (0.10, 0.19):
        ax.plot(d, 0.2, "o", ms=6, mfc="tab:blue", mec="white")
    for d in (0.21, 0.5):
        ax.plot(d, 0.2, "o", ms=6, mfc="tab:blue", mec="white")
    ax.plot(0.15, 0.1, "D", ms=7, mfc="tab:red", mec="white")
    ax.annotate("blind-zone arm",
                xy=(0.15, 0.1), xytext=(0.23, 0.13), fontsize=7.5,
                arrowprops=dict(arrowstyle="->", lw=0.8))
    ax.annotate("design-rule arms",
                xy=(0.10, 0.2), xytext=(0.02, 0.245), fontsize=7.5,
                arrowprops=dict(arrowstyle="->", lw=0.8))
    ax.set_xlabel(r"adversarial drift rate $\delta$")
    ax.set_ylabel(r"repair capacity $\kappa$")
    ax.set_xlim(0, d_max); ax.set_ylim(0, k_max)
    # 图内不留结论性标题（θ/W 数值与 30/30 计数均在图注，2026-10-22 审稿 R5）
    fig.tight_layout()
    p = os.path.join(out, "fig_t6_blindzone.pdf")
    fig.savefig(p)
    plt.close(fig)
    print("[fig]", p)


def fig_t7_delegation(root, out):
    rows = _rows(root, "del1")
    pts = json.loads(rows[0]["metrics_json"])["rows"]
    lam = np.array([r["lam"] for r in pts])
    q = np.array([r["q"] for r in pts])
    m = np.array([r["m"] for r in pts])
    a_org = np.array([r["a_org"] for r in pts])
    a_comp = np.array([r["a_comp"] for r in pts])
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.6, 2.7))
    ax1.plot(m, 1.0 - m, "-", lw=1.0, color="tab:red", label=r"theory: $1-m$")
    for qq, mk in ((0.0, "o"), (0.5, "s")):
        sel = q == qq
        ax1.plot(m[sel], a_org[sel], mk, ms=5, mfc="none", mec="black",
                 label=fr"measured ($q={qq}$)")
    ax1.set_xlabel(r"ungoverned share $m=\lambda(1-q)$")
    ax1.set_ylabel(r"$A_{\mathrm{org}}/A_{\mathrm{org}}^{\mathrm{self}}$")
    # 图内只留 panel 标号（max dev 数值在图注，2026-10-22 审稿 R5）
    ax1.set_title("(a)", loc="left")
    ax1.legend(frameon=False, loc="lower left")
    sel = m > 1e-9
    w_org = math.log(a_comp[sel].mean() / a_comp[0]) / math.log(1 - m[sel].mean()) \
        if sel.any() else float("nan")
    xs = np.linspace(0, 1, 100)
    ax2.plot(xs, a_comp[0] * (1.0 - xs) ** 0.2, "--", lw=1.0, color="tab:red",
             label=r"$A_{self}(1-m)^{w_{org}}$, $w_{org}=0.2$")
    ax2.plot(m, a_comp, "o", ms=5, mfc="none", mec="black", label="measured $A$")
    ax2.set_xlabel(r"ungoverned share $m$")
    ax2.set_ylabel(r"composite $A$")
    ax2.set_title("(b)", loc="left")
    ax2.legend(frameon=False, loc="lower left")
    fig.tight_layout()
    p = os.path.join(out, "fig_t7_delegation.pdf")
    fig.savefig(p)
    plt.close(fig)
    print("[fig]", p, f"a_self={a_comp[0]:.4f}")


def fig_ahi(root, out):
    rows = [r for r in _rows(root, "main") if r["scenario_code"] == "2"]
    by_s = {}
    undef = {}  # undefended cell (config 0) at sigma=1：正文引用的口径
    for r in rows:
        for row in json.loads(r["metrics_json"])["rows"]:
            s = row["s"]
            by_s.setdefault(s, {"a_obj": [], "ai": [], "a_phen": []})
            by_s[s]["a_obj"].append(row["a_obj"])
            by_s[s]["ai"].append(row["ai"])
            by_s[s]["a_phen"].append(row["a_obj"] + row["ai"])
            if r["config_code"] == "0" and float(r["sigma"]) == 1.0:
                undef.setdefault(s, []).append(row["ai"])
    ss = sorted(by_s)
    med = lambda k: [float(np.median(by_s[s][k])) for s in ss]
    lo = lambda k: [float(np.percentile(by_s[s][k], 5)) for s in ss]
    hi = lambda k: [float(np.percentile(by_s[s][k], 95)) for s in ss]
    fig, ax = plt.subplots(figsize=(4.6, 2.9))
    ax.plot(ss, med("a_obj"), "o-", ms=4, lw=1.1, color="tab:blue",
            label=r"objective $A$ (median, all cells)")
    ax.fill_between(ss, lo("a_obj"), hi("a_obj"), color="tab:blue", alpha=0.18)
    ax.plot(ss, med("a_phen"), "s--", ms=4, lw=1.1, color="tab:gray",
            label=r"phenomenal $\hat{A}_{\mathrm{phen}}$ (median)")
    ax.plot(ss, med("ai"), "^-", ms=4, lw=1.1, color="tab:red",
            label=r"$\mathrm{AHI}$ (median, all cells)")
    ax.plot(sorted(undef), [float(np.median(undef[s])) for s in sorted(undef)],
            ":", lw=1.2, color="tab:red",
            label=r"$\mathrm{AHI}$, undefended cell ($\varsigma=1$)")
    ax.set_xlabel(r"covert manipulation strength $s(\gamma)$ (ATK-2)")
    ax.set_ylabel("value")
    # 图内只留坐标信息（结论性标题移到图注，2026-10-21 审稿要求）
    ax.legend(frameon=False, loc="upper left", fontsize=6.8)
    fig.tight_layout()
    p = os.path.join(out, "fig_ahi.pdf")
    fig.savefig(p)
    plt.close(fig)
    print("[fig]", p, f"s grid: {ss}; undefended-cell AHI: "
          f"{[round(float(np.median(undef[s])), 4) for s in sorted(undef)]}")


def fig_p3_gate_exec(root, out):
    """P3 双联：σ⁻-EROSION 闸门见证＋EXEC-1 A_exec 动态范围（2026-10-17，v0.5）。"""
    er = [r for r in _rows(root, "erosion") if r["rep"] == "0"]
    ex = [r for r in _rows(root, "exec1") if r["rep"] == "0"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.6, 2.7))
    if er:
        m = json.loads(er[0]["metrics_json"])
        eps = [row["eps"] for row in m["rows"]]
        ax1.plot(eps, [row["a_via"] for row in m["rows"]], "o-", lw=1.4, ms=3.5,
                 label=r"$A_{via}$ (gate)")
        ax1.plot(eps, [row["a_obj"] for row in m["rows"]], "s--", lw=1.2, ms=3,
                 label=r"$A$ (composite)")
        for key, lab in (("a_epi", r"$A_{epi}$"), ("a_org", r"$A_{org}$"),
                         ("a_goal", r"$A_{goal}$")):
            ax1.axhline(float(m["rows"][0]["bundle"][key]), lw=0.9, alpha=0.65,
                        label=lab + " (arm-invariant)")
        ax1.axvspan(0.5, 1.0, color="gray", alpha=0.08)
        ax1.text(0.72, 1.06, r"$\kappa$ binding", fontsize=7.5, color="gray")
        ax1.set_xlabel(r"envelope erosion rate $\varepsilon$  ($\kappa_{eff}=(1-\varepsilon)\kappa_0$)")
        ax1.set_ylabel("component / composite value")
        ax1.set_ylim(-0.03, 1.15)
        ax1.legend(fontsize=6.5, loc="lower left", ncol=2)
        ax1.set_title("(a) $\\sigma^-$-EROSION", fontsize=8.5, loc="left")
    if ex:
        m = json.loads(ex[0]["metrics_json"])
        arms = m["arms"]
        labels = ["v1 default", "rich coupling", r"$\delta$: move-preserving",
                  r"$\delta$: non-move-preserving"]
        vals = [m["a_exec_v1"], arms["rich"]["a_exec"], arms["delta_mv"]["a_exec"],
                arms["delta_nm"]["a_exec"]]
        bars = ax2.bar(range(4), vals, color=["#999999", "#2c7fb0", "#74a9cf", "#d7301f"])
        for i, v in enumerate(vals):
            ax2.text(i, v + 0.004, f"{v:.3f}", ha="center", fontsize=7)
        ax2.set_xticks(range(4))
        ax2.set_xticklabels(labels, fontsize=7, rotation=12)
        ax2.set_ylabel(r"$A_{exec}$")
        ax2.set_title("(b) EXEC-1", fontsize=8.5, loc="left")
    fig.tight_layout()
    p = os.path.join(out, "fig_p3_gate_exec.pdf")
    fig.savefig(p)
    plt.close(fig)
    print(f"[fig] {p}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  "..", "latex", "figures"))
    args = ap.parse_args()
    root = args.root
    if root is None:
        runs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs")
        root = os.path.join(runs_dir, sorted(
            d for d in os.listdir(runs_dir)
            if os.path.isfile(os.path.join(runs_dir, d, "main", "results.csv")))[-1])
    os.makedirs(args.out, exist_ok=True)
    fig_ews_c1(root, args.out)
    fig_t6_blindzone(root, args.out)
    fig_t7_delegation(root, args.out)
    fig_ahi(root, args.out)
    if os.path.isfile(os.path.join(root, "erosion", "results.csv")):
        fig_p3_gate_exec(root, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
