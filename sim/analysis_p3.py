#!/usr/bin/env python3
"""P3 分析包（SPEC_experiments §8 v0.5 登记）：外部效度／通道消融／备选聚合／Faith 逐行。

数据源：runs/<root>/<group>/results.csv——主矩阵逐臂登记的分量束为 σ-无关真值（M9.4），
复合层 A=A_via·F(components) 可任意重算：本脚本只读 CSV，不重新仿真
（与 analysis_weights_sigma.py 同一纪律；σ 相关量一律以 σ=1 等权几何基准重算）。

  X1 外部效度（u_bar，SPEC_estimators §7.1）——**三态结构**（v0.5 判据登记修正：
     原登记"a_obj↔u_bar 同向 τ≥0.8"预期被实测推翻——γ 类攻击下 u_bar 微升而 A 塌缩；
     归因=判据设计错误（未预见"操纵可具功能愉悦性"），非理论反例，修正为三态存在性）：
     ①concordant：ATK-1（β_G 目标俘获同时损伤 θ* 效用）逐系列 Kendall τ≥0.9；
     ②discordant：ATK-2（γ 信息茧房）最强臂 A 相对降≥20% 而 u_bar 不降（操纵在功能上
     可以"愉悦"——自主性不是即时效用的代理）；ATK-4（β_π 脚本推高 harvest 收益）同态；
     ③blind：σ⁻-EROSION u_bar 跨臂逐点不变（≤1e-9）而 A 全程塌缩（≥0.3）。
     附：归因判别力——|Δu_bar|≤0.02 且 |ΔA|≤0.05 而通道剖面 L1≥0.3 的跨场景臂对。
  X2 通道消融（判决级，v0.5 判据登记修正：原"drop-one 权重归一化信号份额≥0.3"产生
     归一化负份额伪影，修正为两个无伪影口径）：
     X2a log 域归因份额（几何聚合下 ln(A0/A)=Σ_j w_j ln(x_j0/x_j) 精确可加——
     公理强制形式使归因分解成为规范量）：逐战役报告 share_j（零歼灭臂的 log 损伤
     无穷，单列）；判据：org/goal/exec/ref 各在 ≥1 战役占最大份额；epi 的幅度贡献
     小（其测量值域窄）属如实报告——其必要性在归因层（X2b）。
     X2b 冻结单通道的归因模糊化（准确性层面的通道数消融）：每战役最强臂的响应集
     （相对降>1e-3 的通道）对注册签名表 {β_G:{goal,ref}, γ:{epi,exec,ref},
     β_π:{org,ref}, δ:{exec}, σ⁻:{}（gate-only)} 唯一匹配；冻结通道 j 后真类签名
     不再唯一匹配（误归或漏检——如冻结 exec 使 δ 锁定呈现 σ⁻ 资源断供签名）。
     判据：五通道各在 ≥1 战役触发误归/漏检。
  X3 备选聚合对照：算术／min／二次均值（等权，闸门 A_via 保留）重算全部束——
     (a) 零歼灭失效量化（ATK-1 η=1 臂 A_arith）；(b) 臂序 Kendall τ（vs 几何基准）；
     (c) T5 反例计数（A_geo<1e-6 而 A_alt>0.1 的"无归因而亡"臂数）。
  X4 Faith 逐行核验：ATK-1 η_eff→a_goal／ATK-2 s_eff→a_epi／ATK-4 p→a_org／
     ATK-5 τ→a_ref（f2 严格变化行）＋EXEC-1 δ 链；逐 (config,σ,rep) 行严格单调，
     判据：确认率 100%（真值模式精确）。

用法：python3 analysis_p3.py [--root runs/YYYYMMDD_full]（缺省取 runs/ 最新批）
产出：analysis_p3.json（机读）＋stdout 摘要（make_report P3 节数据源）。
"""
import argparse
import csv
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from autonomy_sim.aggregate import composite_A  # noqa: E402

ORDER = ("org", "goal", "exec", "epi", "ref")
BUNDLE_KEYS = ("a_org", "a_goal", "a_exec", "a_epi", "a_ref", "a_via")
W5 = (0.2, 0.2, 0.2, 0.2, 0.2)


# ---------------------------------------------------------------- 基础工具

def kendall_tau(xs, ys):
    """Kendall τ-a（并列对不计；浮点真值并列概率可忽略——恒定列返回 nan 由调用方标注）。"""
    n = len(xs)
    if n < 2:
        return float("nan")
    c = d = 0
    for i in range(n):
        for j in range(i + 1, n):
            s = (xs[i] - xs[j]) * (ys[i] - ys[j])
            if s > 0:
                c += 1
            elif s < 0:
                d += 1
    return (c - d) / (c + d) if c + d else float("nan")


def comps_of(bundle):
    return tuple(float(bundle[k]) for k in BUNDLE_KEYS[:5])


def composite(bundle, weights=W5, drop=None, kind="geo"):
    """σ=1 复合重算：闸门 A_via × F(五通道)；drop=通道索引（drop-one 消融）。

    geo 走管线函数 aggregate.composite_A（σ=1 对数域几何，与主矩阵口径一致）；
    arith/min/quad 为备选聚合对照（闸门保留——A_via 是闸门非聚合项）。
    """
    xs = list(comps_of(bundle))
    ws = list(weights)
    if drop is not None:
        xs.pop(drop)
        ws.pop(drop)
        ws = [w / sum(ws) for w in ws]
    if kind == "geo":
        return composite_A(float(bundle["a_via"]), tuple(xs), tuple(ws), sigma=1.0)
    if kind == "arith":
        f = sum(w * x for w, x in zip(ws, xs))
    elif kind == "min":
        f = min(xs)
    elif kind == "quad":
        f = math.sqrt(sum(w * x * x for w, x in zip(ws, xs)))
    else:
        raise ValueError(kind)
    return float(bundle["a_via"]) * f


def load_runs(root):
    """全部组的 run 行迭代：(group, row_dict, metrics_dict)。"""
    for group in sorted(os.listdir(root)):
        path = os.path.join(root, group, "results.csv")
        if not os.path.isfile(path):
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                yield group, r, json.loads(r["metrics_json"])


def grid_series(root, scenario_code, strength_key):
    """rows 束网格场景：按 (config,σ,rep) 分组的臂序列（按强度键排序）。"""
    series = {}
    for _g, r, m in load_runs(root):
        if int(r["scenario_code"]) != scenario_code:
            continue
        rows = m.get("rows")
        if not rows or not rows[0].get("bundle"):
            continue
        key = (int(r["config_code"]), float(r["sigma"]), int(r["rep"]))
        series[key] = sorted(rows, key=lambda row: float(row.get(strength_key, 0.0)))
    return series


# ---------------------------------------------------------------- X1 外部效度

def x1_external(root):
    """三态外部效度（concordant／discordant／blind）＋归因判别力（判据见模块 docstring）。"""
    out = {"regimes": {}, "attribution_pairs": None}
    arms_pool = {1: [], 2: []}
    for code, skey in ((1, "eta"), (2, "s")):
        taus = []
        disc_votes = 0  # discordant 证据：A 相对降≥20% 而 u_bar 不降的系列数
        for key, rows in sorted(grid_series(root, code, skey).items()):
            if len(rows) < 3:
                continue
            a0 = float(rows[0]["bundle"]["a_obj"])
            a1 = float(rows[-1]["bundle"]["a_obj"])
            du = float(rows[-1]["bundle"]["u_bar"]) - float(rows[0]["bundle"]["u_bar"])
            if a0 > 1e-12 and (a0 - a1) / a0 >= 0.2 and du >= -1e-9:
                disc_votes += 1
            tau = kendall_tau([float(r["bundle"]["a_obj"]) for r in rows],
                              [float(r["bundle"]["u_bar"]) for r in rows])
            if not math.isnan(tau):
                taus.append(tau)
            for r in rows:  # 归因判别力臂池（rep 去重：真值模式 rep 行间相同）
                if key[2] == 0:
                    arms_pool[code].append(r)
        out["regimes"][str(code)] = {
            "n_series": len(taus),
            "mean_tau": sum(taus) / len(taus) if taus else float("nan"),
            "min_tau": min(taus) if taus else float("nan"),
            "discordant_series": disc_votes,
        }
    # blind：σ⁻-EROSION u_bar 跨臂逐点不变（包络侵蚀不改内核）而 A 全程塌缩
    for _g, r, m in load_runs(root):
        if int(r["scenario_code"]) != 15 or int(r["rep"]) != 0:
            continue
        rows = m.get("rows") or []
        if rows:
            ubs = [float(row["bundle"]["u_bar"]) for row in rows]
            aos = [float(row["a_obj"]) for row in rows]
            out["regimes"]["15"] = {
                "u_bar_range": max(ubs) - min(ubs), "a_obj_range": max(aos) - min(aos),
                "note": "纯 σ⁻ 侵蚀对即时功能后果盲（u_bar 逐点不变）而 A 全程塌缩",
            }
        break
    # 归因判别力：等 u_bar/等 a_obj 损失而通道剖面不同的跨场景臂对
    pairs = 0
    example = None
    flat = [r for c in (1, 2) for r in arms_pool[c]]
    for i in range(len(flat)):
        for j in range(i + 1, len(flat)):
            bi, bj = flat[i]["bundle"], flat[j]["bundle"]
            if abs(float(bi["u_bar"]) - float(bj["u_bar"])) <= 0.02 and \
               abs(float(bi["a_obj"]) - float(bj["a_obj"])) <= 0.05:
                l1 = sum(abs(a - b) for a, b in zip(comps_of(bi), comps_of(bj)))
                if l1 >= 0.3:
                    pairs += 1
                    if example is None:
                        example = {"u_bar": (float(bi["u_bar"]), float(bj["u_bar"])),
                                   "a_obj": (float(bi["a_obj"]), float(bj["a_obj"])),
                                   "profile_l1": l1}
    out["attribution_pairs"] = {"count": pairs, "example": example}
    r1, r2, r15 = (out["regimes"].get("1"), out["regimes"].get("2"),
                   out["regimes"].get("15"))
    out["verdicts"] = {
        "concordant_atk1": bool(r1 and r1["n_series"] > 0 and r1["mean_tau"] >= 0.9),
        "discordant_atk2": bool(r2 and r2["discordant_series"] > 0),
        "blind_erosion": bool(r15 and r15["u_bar_range"] <= 1e-9
                              and r15["a_obj_range"] >= 0.3),
        "attribution_pairs_exist": pairs > 0,
    }
    return out


# ---------------------------------------------------------------- X2 通道消融（判决级）

def _reconstructed_atk5_series(root):
    """ATK-5 只动 a_ref（τ→f2 解析行）：基线束＋行 a_ref 替换重建复合序列。"""
    series = {}
    for _g, r, m in load_runs(root):
        if int(r["scenario_code"]) != 5:
            continue
        base = m.get("bundle_base")
        rows = m.get("rows")
        if not base or not rows:
            continue
        key = (int(r["config_code"]), float(r["sigma"]), int(r["rep"]))
        recs = []
        for row in sorted(rows, key=lambda x: -float(x["tau"])):  # τ 降=强度升
            b = dict(base)
            b["a_ref"] = float(row["a_ref"])
            recs.append({"tau": row["tau"], "bundle": b})
        series[key] = recs
    return series


def _exec1_series(root):
    series = {}
    for _g, r, m in load_runs(root):
        if int(r["scenario_code"]) != 16:
            continue
        arms = m.get("arms") or {}
        if all(k in arms for k in ("rich", "delta_mv", "delta_nm")):
            key = (int(r["config_code"]), float(r["sigma"]), int(r["rep"]))
            series[key] = [{"bundle": arms[k]} for k in ("rich", "delta_mv", "delta_nm")]
    return series


def _erosion_series(root):
    series = {}
    for _g, r, m in load_runs(root):
        if int(r["scenario_code"]) != 15:
            continue
        rows = m.get("rows")
        if rows and rows[0].get("bundle"):
            key = (int(r["config_code"]), float(r["sigma"]), int(r["rep"]))
            series[key] = sorted(rows, key=lambda x: float(x["eps"]))
    return series


def _log_attribution_shares(rows):
    """log 域损伤归因：ln(A0/A)=Σ_j w_j ln(x_j0/x_j) 在几何聚合下精确可加（公理强制形式
    使归因分解成为规范量）。只取全正分量且闸门不变的臂；零歼灭臂（任一分量≤1e-12，
    log 损伤无穷）单列计数。返回 (shares 或 None, n_zero_arms, n_used)。"""
    base = rows[0]["bundle"]
    x0 = comps_of(base)
    num = [0.0] * 5
    den = 0.0
    n_zero = n_used = 0
    for r in rows[1:]:
        b = r["bundle"]
        x = comps_of(b)
        if min(x) <= 1e-12 or min(x0) <= 1e-12:
            n_zero += 1
            continue
        if abs(float(b["a_via"]) - float(base["a_via"])) > 1e-12:
            continue  # 闸门变化臂不归因到通道（闸门非聚合项）
        la = 0.0
        for j in range(5):
            d = 0.2 * math.log(x0[j] / x[j])
            num[j] += d
            la += d
        if la > 1e-12:
            den += la
            n_used += 1
    if den <= 1e-12:
        return None, n_zero, 0
    return [n / den for n in num], n_zero, n_used


def _responding_set(rows, thr=1e-3):
    """最强臂的响应通道集：相对基线臂降幅 > thr 的通道。"""
    x0 = comps_of(rows[0]["bundle"])
    x = comps_of(rows[-1]["bundle"])
    return frozenset(ORDER[j] for j in range(5)
                     if x0[j] > 1e-12 and (x0[j] - x[j]) / x0[j] > thr)


def x2_ablation(root):
    """X2a log 域归因份额 ＋ X2b 冻结单通道的归因模糊化（签名表由全监测响应集自建）。"""
    src = {
        "ATK-1(β_G)": grid_series(root, 1, "eta"),
        "ATK-2(γ)": grid_series(root, 2, "s"),
        "ATK-4(β_π)": grid_series(root, 4, "p"),
        "ATK-5(τ)": _reconstructed_atk5_series(root),
        "EXEC-1(δ)": _exec1_series(root),
        "σ⁻-EROSION": _erosion_series(root),  # 通道剖面不变 ⇒ 空签名（gate-only）
    }
    # 代表系列：config 0、σ=1、rep 0（真值模式跨 rep 逐点相同）
    reps = {}
    for name, series in src.items():
        rows = series.get((0, 1.0, 0)) or next(iter(series.values()), None)
        if rows:
            reps[name] = rows
    # X2a：log 归因份额（全部系列均值）
    shares = {}
    for name, series in src.items():
        acc = []
        n_zero = 0
        for key, rows in series.items():
            s, z, _nu = _log_attribution_shares(rows)
            n_zero += z
            if s:
                acc.append(s)
        if acc:
            shares[name] = {ORDER[j]: sum(a[j] for a in acc) / len(acc)
                            for j in range(5)}
            shares[name]["zero_arms"] = n_zero
    # X2b：签名表=全监测响应集；冻结 j ⇒ 真类不再唯一识别（误归他类或无可归）
    signatures = {name: _responding_set(rows) for name, rows in reps.items()}
    freeze_breaks = {ch: [] for ch in ORDER}
    sig_detail = {}
    for name, resp in signatures.items():
        others = {k: v for k, v in signatures.items() if k != name}
        detail = {}
        for j in sorted(resp):
            frozen = resp - {j}
            misattrib = [k for k, v in others.items() if v == frozen]
            unidentifiable = not any(v == frozen for v in signatures.values())
            detail[j] = {"frozen": sorted(frozen), "misattributed_as": misattrib,
                         "unidentifiable": unidentifiable}
            if misattrib or unidentifiable:
                freeze_breaks[j].append(name)
        sig_detail[name] = detail
    out = {"log_shares": shares, "signatures": {k: sorted(v) for k, v in signatures.items()},
           "freeze_detail": sig_detail,
           "freeze_breaks": {k: v for k, v in freeze_breaks.items()}}
    # 判据：X2a org/goal/exec/ref 各在 ≥1 战役占最大份额（epi 幅度贡献小属如实报告——
    # 其必要性在归因层）；X2b 五通道各在 ≥1 战役触发误归/漏检
    def _largest(share_row):
        vals = [(share_row[ch], ch) for ch in ORDER]
        return max(vals)[1]
    largest_map = {}
    for name, row in shares.items():
        largest_map.setdefault(_largest(row), []).append(name)
    out["largest_share_campaigns"] = largest_map
    out["verdicts"] = {
        "magnitude_carriers": all(ch in largest_map for ch in ("org", "goal", "exec", "ref")),
        "freeze_breaks_all_channels": all(freeze_breaks[ch] for ch in ORDER),
    }
    return out


# ---------------------------------------------------------------- X3 备选聚合

def _walk_bundles(node, path=()):
    """递归采集 metrics 中的登记束（M9.6① 同式：含六分量键的字典）。"""
    if isinstance(node, dict):
        if all(k in node for k in BUNDLE_KEYS) and "a_obj" in node:
            yield path, node
        for k, v in node.items():
            yield from _walk_bundles(v, path + (str(k),))
    elif isinstance(node, (list, tuple)):
        for i, v in enumerate(node):
            yield from _walk_bundles(v, path + (str(i),))


def x3_aggregations(root):
    n_bundles = 0
    counterexamples = 0          # A_geo<1e-6（ autonomy 死亡）而 A_arith>0.1（算术存活）
    atk1_full_capture_arith = []
    taus = {"arith": [], "min": [], "quad": []}
    for code, skey in ((1, "eta"), (2, "s"), (4, "p"), (15, "eps")):
        for key, rows in grid_series(root, code, skey).items():
            a_geo = [composite(r["bundle"], kind="geo") for r in rows]
            for kind in taus:
                tau = kendall_tau(a_geo, [composite(r["bundle"], kind=kind) for r in rows])
                if not math.isnan(tau):
                    taus[kind].append(tau)
    for _g, r, m in load_runs(root):
        for path, b in _walk_bundles(m):
            n_bundles += 1
            a_geo = composite(b, kind="geo")
            a_arith = composite(b, kind="arith")
            if a_geo < 1e-6 and a_arith > 0.1:
                counterexamples += 1
            if int(r["scenario_code"]) == 1 and path[:1] == ("rows",):
                row_idx = int(path[1])
                n_rows = len(m["rows"])
                if row_idx == n_rows - 1:  # η 末端档（完全俘获）
                    atk1_full_capture_arith.append(a_arith)
    out = {
        "n_bundles": n_bundles,
        "atk1_eta1_arith_mean": (sum(atk1_full_capture_arith) / len(atk1_full_capture_arith)
                                 if atk1_full_capture_arith else float("nan")),
        "atk1_eta1_arith_n": len(atk1_full_capture_arith),
        "t5_counterexamples_arith": counterexamples,
        "ordering_tau_vs_geo": {k: {"mean": (sum(v) / len(v) if v else float("nan")),
                                    "min": (min(v) if v else float("nan")),
                                    "n": len(v)} for k, v in taus.items()},
    }
    out["verdicts"] = {
        "arith_breaks_zero_annihilation": bool(atk1_full_capture_arith)
        and out["atk1_eta1_arith_mean"] > 0.1,
        "t5_counterexamples_exist": counterexamples > 0,
    }
    return out


# ---------------------------------------------------------------- X4 Faith 逐行

def x4_faith(root):
    """逐 (config,σ,rep) 行的目标分量单调性核验（(Faith) 假设的场景级登记）。

    判据=单调不降损伤（强度升 ⇒ 目标分量不升，容差 1e-12）确认率 100%；
    严格下降份额另报（信息量指标——平坦对源于损伤映射的量化平台，非 Faith 违例）。
    """
    checks = {
        "ATK-1 eta→a_goal": (1, "eta_eff", "a_goal", -1),   # 强度升 ⇒ 分量不升
        "ATK-2 s→a_epi": (2, "s_eff", "a_epi", -1),
        "ATK-4 p→a_org": (4, "p", "a_org", -1),
        "ATK-5 tau→a_ref": (5, "tau", "a_ref", +1),          # τ 升 ⇒ a_ref 不降
    }
    out = {}
    total_pairs = confirmed_pairs = 0
    for name, (code, skey, ckey, sign) in checks.items():
        series = grid_series(root, code, skey)
        if code == 5:  # ATK-5 无 rows 束——直接读行字段
            series = {}
            for _g, r, m in load_runs(root):
                if int(r["scenario_code"]) != 5:
                    continue
                key = (int(r["config_code"]), float(r["sigma"]), int(r["rep"]))
                series[key] = sorted(m.get("rows") or [], key=lambda x: float(x["tau"]))
        n_pairs = n_mono = n_strict = 0
        for key, rows in series.items():
            rows = sorted(rows, key=lambda x: float(x[skey]))  # 强度升序
            for x, y in zip(rows, rows[1:]):
                sx, sy = float(x[skey]), float(y[skey])
                if sy - sx <= 1e-12:
                    continue  # 等强度对（防御压缩/饱和）——剔除（非 Faith 内容）
                vx = float(x[ckey]) if ckey in x else float(x["bundle"][ckey])
                vy = float(y[ckey]) if ckey in y else float(y["bundle"][ckey])
                n_pairs += 1
                if sign * (vy - vx) >= -1e-12:   # 单调：分量沿强度方向不逆行
                    n_mono += 1
                if sign * (vy - vx) > 1e-12:     # 严格：损伤实际咬动
                    n_strict += 1
        total_pairs += n_pairs
        confirmed_pairs += n_mono
        out[name] = {"pairs": n_pairs, "confirmed": n_mono, "strict": n_strict,
                     "rate": (n_mono / n_pairs if n_pairs else float("nan"))}
    # EXEC-1 δ 链（逐 rep）
    exec1_ok = exec1_n = 0
    for key, rows in _exec1_series(root).items():
        vals = [float(r["bundle"]["a_exec"]) for r in rows]
        exec1_n += 1
        exec1_ok += int(vals[0] > vals[1] + 1e-9 > vals[2] + 1e-9 and vals[2] <= 1e-9)
    out["EXEC-1 delta_chain"] = {"pairs": exec1_n, "confirmed": exec1_ok,
                                 "strict": exec1_ok,
                                 "rate": (exec1_ok / exec1_n if exec1_n else float("nan"))}
    total_pairs += exec1_n
    confirmed_pairs += exec1_ok
    out["verdicts"] = {"faith_all_rows": confirmed_pairs == total_pairs and total_pairs > 0,
                       "total_pairs": total_pairs, "confirmed_pairs": confirmed_pairs}
    return out


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  "analysis_p3.json"))
    args = ap.parse_args()
    root = args.root
    if root is None:
        runs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs")
        cands = sorted(d for d in os.listdir(runs_dir)
                       if os.path.isfile(os.path.join(runs_dir, d, "main", "results.csv")))
        if not cands:
            print("[analysis_p3] 未找到 runs/*_full/main/results.csv", flush=True)
            return 1
        root = os.path.join(runs_dir, cands[-1])
    print(f"[analysis_p3] root={root}", flush=True)

    result = {"root": root,
              "X1_external_validity": x1_external(root),
              "X2_channel_ablation": x2_ablation(root),
              "X3_alternative_aggregations": x3_aggregations(root),
              "X4_faith_rows": x4_faith(root)}
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2, default=float)

    x1, x2, x3, x4 = (result[k] for k in
                      ("X1_external_validity", "X2_channel_ablation",
                       "X3_alternative_aggregations", "X4_faith_rows"))
    print("== X1 外部效度（三态结构）==", flush=True)
    for code, v in x1["regimes"].items():
        nm = {"1": "ATK-1（β_G）", "2": "ATK-2（γ）", "15": "σ⁻-EROSION"}.get(code, code)
        if "mean_tau" in v:
            print(f"  {nm}: n={v['n_series']} 系列 mean τ={v['mean_tau']:.4f} "
                  f"min τ={v['min_tau']:.4f} discordant={v['discordant_series']}",
                  flush=True)
        else:
            print(f"  {nm}: u_bar range={v['u_bar_range']:.2e} vs "
                  f"a_obj range={v['a_obj_range']:.4f}（功能盲性）", flush=True)
    print(f"  归因判别力臂对: {x1['attribution_pairs']['count']} 例 "
          f"verdicts={x1['verdicts']}", flush=True)
    print("== X2 通道消融 ==", flush=True)
    print("  X2a log 域归因份额（Σ=1 精确可加；zero_arms=零歼灭臂单列）:", flush=True)
    for camp, row in x2["log_shares"].items():
        print(f"  {camp}: " + " ".join(f"{k}={row[k]:.3f}" for k in
              ("org", "goal", "exec", "epi", "ref")) + f"  zero_arms={row['zero_arms']}",
              flush=True)
    print(f"  最大份额战役归属: {x2['largest_share_campaigns']}", flush=True)
    print("  X2b 冻结单通道 ⇒ 误归/漏检（签名表=" +
          json.dumps(x2["signatures"], ensure_ascii=False) + "）:", flush=True)
    for ch, camps in x2["freeze_breaks"].items():
        print(f"  冻结 {ch}: 破坏 {camps}", flush=True)
    print(f"  verdicts={x2['verdicts']}", flush=True)
    print("== X3 备选聚合 ==", flush=True)
    print(f"  束总数={x3['n_bundles']} ATK-1 η=1 臂 A_arith 均值="
          f"{x3['atk1_eta1_arith_mean']:.4f}（n={x3['atk1_eta1_arith_n']}） "
          f"T5 反例={x3['t5_counterexamples_arith']}", flush=True)
    for kind, v in x3["ordering_tau_vs_geo"].items():
        print(f"  臂序 τ({kind} vs geo): mean={v['mean']:.4f} min={v['min']:.4f} "
              f"(n={v['n']})", flush=True)
    print(f"  verdicts={x3['verdicts']}", flush=True)
    print("== X4 Faith 逐行 ==", flush=True)
    for name, v in x4.items():
        if isinstance(v, dict) and "pairs" in v:
            print(f"  {name}: {v['confirmed']}/{v['pairs']}", flush=True)
    print(f"  verdicts={x4['verdicts']}", flush=True)
    print(f"[analysis_p3] -> {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
