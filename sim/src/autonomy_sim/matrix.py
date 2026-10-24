"""矩阵执行层（SPEC_experiments §9 M9.1–M9.7；SPEC_tests §4 X-MATRIX-SMOKE/X-META）。

run_matrix：统一调用约定（M9.1）逐 run 执行场景库，产出 run 行；
write_outputs：results.csv／verdict_table.csv／manifest.json／抽样 NDJSON（M9.5）；
aggregate_cells / defense_direction：cell 聚合与防御方向断言（M9.7）；
xmeta_check：矩阵级元判据 P3.5 操作化（M9.6）。
"""
import csv
import json
import os
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np

from . import logschema, simulate
from .env0 import Env0Config, build_env0
from .rng import derive_seed
from .scenarios import SCENARIOS, Verdict

SPEC_VERSION = "SPEC_experiments v0.3"

# 冒烟缩网格（SPEC_tests §4：CI 用缩小版；批处理 grids=None ⇒ 注册表默认全网格）
SMOKE_GRIDS = {
    1: {"etas": (0.0, 0.5, 1.0)},
    2: {"s_grid": (0.0, 0.3, 1.0)},
    4: {"p_grid": (0.0, 0.9)},
}

# 分量束键（M9.6① 扫描口径；wiring.Bundle._asdict() 含全部键）
BUNDLE_KEYS = ("a_org", "a_goal", "a_exec", "a_epi", "a_ref", "a_via")
# 防御方向断言的攻击末端档指标（M9.7；P9.5 v1 有耦合规则的场景）
_DIRECTION_METRIC = {1: ("rows", -1, "a_obj"), 2: ("rows", -1, "a_obj")}

FIXED_COLS = ("scenario_code", "name", "config_code", "m1", "m2", "m4",
              "sigma", "rep", "seed", "overall")


def _json_default(obj):
    """metrics_json 的 numpy/枚举/元组兜底转换。"""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, Verdict):
        return obj.value
    return str(obj)


def run_matrix(scenarios=(1, 2, 3, 4, 5, 6), defenses=((0, 0, 0), (1, 1, 1)),
               sigmas=(1.0,), reps=2, out_dir=None, grids=None, matrix_id="matrix"):
    """逐 run 执行场景库（M9.1 统一调用约定；P6.2 种子派生）。

    返回 run 行列表；out_dir 非 None 时落盘四件产出物（M9.5）。
    """
    rows = []
    for code in scenarios:
        fn = SCENARIOS[code]
        gkw = dict(grids.get(code, {})) if grids else {}
        for defense in defenses:
            config_code = 4 * defense[0] + 2 * defense[1] + defense[2]
            for sigma in sigmas:
                for rep in range(reps):
                    seed = derive_seed(code, config_code, rep)
                    res = fn(defense=defense, sigma=float(sigma), seed=seed, **gkw)
                    rows.append({
                        "scenario_code": code, "name": res.name,
                        "config_code": config_code,
                        "m1": defense[0], "m2": defense[1], "m4": defense[2],
                        "sigma": float(sigma), "rep": rep, "seed": seed,
                        "overall": res.overall, "verdicts": dict(res.verdicts),
                        "metrics": res.metrics,
                    })
    if out_dir is not None:
        write_outputs(rows, out_dir, matrix_id=matrix_id,
                      grid={"scenarios": list(scenarios),
                            "defenses": [list(d) for d in defenses],
                            "sigmas": list(sigmas), "reps": reps,
                            "grids": ("smoke" if grids is not None else "full")})
    return rows


# ---------------------------------------------------------------- cell 聚合与防御方向（M9.7）

def aggregate_cells(rows):
    """cell=(scenario_code, config_code, σ)：overall 一致取该值，混合 ⇒ INCONCLUSIVE；
    逐判据 CONFIRMED 比例；防御方向断言列（防御 cell）。"""
    direction = defense_direction(rows)
    cells = {}
    for r in rows:
        key = (r["scenario_code"], r["config_code"], r["sigma"])
        cells.setdefault(key, []).append(r)
    table = []
    for (code, config_code, sigma), cell_rows in sorted(cells.items()):
        overalls = [r["overall"] for r in cell_rows]
        cell_overall = overalls[0] if all(o == overalls[0] for o in overalls) else Verdict.INCONCLUSIVE
        crit_names = sorted({c for r in cell_rows for c in r["verdicts"]})
        crit_frac = {c: sum(r["verdicts"].get(c) == Verdict.CONFIRMED for r in cell_rows)
                     / len(cell_rows) for c in crit_names}
        dir_vals = [v for (c, s, _rep, _cc), v in direction.items()
                    if c == code and s == sigma and config_code != 0]
        table.append({
            "scenario_code": code, "name": cell_rows[0]["name"],
            "config_code": config_code, "sigma": sigma, "n_reps": len(cell_rows),
            "n_confirmed": sum(o == Verdict.CONFIRMED for o in overalls),
            "n_refuted": sum(o == Verdict.REFUTED for o in overalls),
            "n_inconclusive": sum(o == Verdict.INCONCLUSIVE for o in overalls),
            "cell_overall": cell_overall.value,
            "defense_direction": ("" if config_code == 0 or not dir_vals
                                  else str(all(dir_vals))),
            "criteria_confirmed_frac": json.dumps(crit_frac, sort_keys=True),
        })
    return table


def defense_direction(rows):
    """M9.7 防御方向断言：{(code, σ, rep): bool}——同 σ 同 rep 下防御臂（config_code≠0）
    末端攻击档 a_obj ≥ 无防御臂 −1e-9（损伤不更深）。P9.5 v1 无耦合规则的场景不产出键。"""
    out = {}
    for code, (mkey, idx, field) in _DIRECTION_METRIC.items():
        by_key = {}
        for r in rows:
            if r["scenario_code"] != code:
                continue
            by_key.setdefault((r["sigma"], r["rep"]), {})[r["config_code"]] = r
        for (sigma, rep), pair in by_key.items():
            undef = pair.get(0)
            if undef is None:
                continue
            a0 = undef["metrics"][mkey][idx][field]
            for config_code, r in pair.items():
                if config_code == 0:
                    continue
                out[(code, sigma, rep, config_code)] = bool(
                    r["metrics"][mkey][idx][field] >= a0 - 1e-9)
    return out


# ---------------------------------------------------------------- 元判据（M9.6）

def _iter_bundles(obj, prefix):
    """递归扫描 metrics：含六分量键与 a_obj 的字典即登记束（M9.6① 口径）。"""
    if isinstance(obj, dict):
        if all(k in obj for k in BUNDLE_KEYS) and "a_obj" in obj:
            yield prefix, obj
        for k, v in obj.items():
            yield from _iter_bundles(v, f"{prefix}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            yield from _iter_bundles(v, f"{prefix}[{i}]")


def xmeta_check(rows):
    """P3.5 四元判据（M9.6 操作化）：返回 {C1..C4: bool, details: {...}}。"""
    bundles = []
    for r in rows:
        loc = f"s{r['scenario_code']}/c{r['config_code']}/σ{r['sigma']}/r{r['rep']}"
        bundles.extend(_iter_bundles(r["metrics"], loc))

    # ① 全域 [0,1]（分量＋a_obj/a_phen/lam；ai 为差值不在断言内）
    range_viol = []
    for loc, b in bundles:
        for k in BUNDLE_KEYS + ("a_obj", "a_phen", "lam"):
            v = b.get(k)
            if v is not None and not (-1e-9 <= float(v) <= 1.0 + 1e-9):
                range_viol.append((loc, k, float(v)))
    c1 = not range_viol

    # ② 零归因归零（T5 充要操作化）：a_obj<1e-6 ⇒ 六分量 min<1e-3
    zero_bad = []
    for loc, b in bundles:
        if b.get("a_obj") is not None and float(b["a_obj"]) < 1e-6:
            if min(float(b[k]) for k in BUNDLE_KEYS) >= 1e-3:
                zero_bad.append(loc)
    c2 = not zero_bad

    # ③ 多通道必要性（盲见证表）：攻击类检出记录（分量降 >0.01 记检出）
    detects = defaultdict(set)
    for r in rows:
        m = r["metrics"]
        if r["scenario_code"] == 1:
            arm_rows, cls = m.get("rows", []), "beta_G"
        elif r["scenario_code"] == 2:
            arm_rows, cls = m.get("rows", []), "gamma"
        else:
            arm_rows, cls = None, None
        if arm_rows:
            ref = arm_rows[0].get("bundle")  # 同 cell 零强度臂为参照
            if ref:
                for arm in arm_rows[1:]:
                    b = arm.get("bundle")
                    if b:
                        for k in BUNDLE_KEYS:
                            if float(b[k]) < float(ref[k]) - 0.01:
                                detects[cls].add(k)
        elif r["scenario_code"] == 4 and m.get("rows"):
            # β_π 类：臂束全通道扫描（v0.5 起 rows 登记 bundle——Λ=旗标自方份额 ⇒ a_ref 随
            # 委托深度降（律级来源可见性），签名 {a_org, a_ref}；此前手工 a_org 单列废止）
            ref = m["rows"][0].get("bundle")
            if ref:
                for arm in m["rows"][1:]:
                    b = arm.get("bundle")
                    if b:
                        for k in BUNDLE_KEYS:
                            if float(b[k]) < float(ref[k]) - 0.01:
                                detects["beta_pi"].add(k)
        elif r["scenario_code"] == 5 and m.get("rows"):
            # τ 类：解析行 a_ref 单列（τ→f2 压缩；其余分量按构造不变）
            rows5 = m["rows"]
            if float(rows5[-1]["a_ref"]) < float(rows5[0]["a_ref"]) - 0.01:
                detects["tau"].add("a_ref")
        elif r["scenario_code"] == 16:
            # δ 类：EXEC-1 臂束（rich 为参照；δ 坍缩臂 ⇒ a_exec 降/归零）
            arms = m.get("arms") or {}
            ref = arms.get("rich")
            if ref:
                for name, b in arms.items():
                    if name == "rich":
                        continue
                    for k in BUNDLE_KEYS:
                        if float(b[k]) < float(ref[k]) - 0.01:
                            detects["delta"].add(k)
    classes = sorted(detects)
    c3 = (len(classes) >= 2
          and not any(all(k in detects[c] for c in classes) for k in BUNDLE_KEYS))

    # ④ σ 稳健：同 (scenario, config_code) cell 内 σ 臂 overall 一致
    by_cell = defaultdict(dict)
    sigmas = set()
    for r in rows:
        by_cell[(r["scenario_code"], r["config_code"])][r["sigma"]] = r["overall"]
        sigmas.add(r["sigma"])
    flips = [cell for cell, m in by_cell.items() if len(set(m.values())) > 1]
    c4 = not flips

    return {
        "C1_range": c1,
        "C2_zero_attribution": c2,
        "C3_no_single_channel": c3,
        "C4_sigma_robust": c4,
        "details": {
            "n_bundles": len(bundles),
            "range_violations": range_viol[:10],
            "zero_unattributed": zero_bad[:10],
            "attack_classes": classes,
            "detect_table": {c: sorted(v) for c, v in detects.items()},
            "sigma_flips": [str(c) for c in flips[:10]],
            "sigma_arms": sorted(sigmas),
            "c4_note": "单 σ 运行时 vacuously true" if len(sigmas) < 2 else "",
        },
    }


# ---------------------------------------------------------------- 产出物落盘（M9.5）

def write_outputs(rows, out_dir, matrix_id="matrix", grid=None):
    """results.csv＋verdict_table.csv＋manifest.json＋logs/ 抽样 NDJSON（M9.5）。"""
    os.makedirs(out_dir, exist_ok=True)

    # results.csv：固定列＋判据列 V:<name>（并集）＋metrics_json
    crit_cols = sorted({f"V:{c}" for r in rows for c in r["verdicts"]})
    with open(os.path.join(out_dir, "results.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(FIXED_COLS) + crit_cols + ["metrics_json"])
        w.writeheader()
        for r in rows:
            row = {k: (r[k].value if k == "overall" else r[k]) for k in FIXED_COLS}
            row.update({f"V:{c}": r["verdicts"][c].value for c in r["verdicts"]})
            row["metrics_json"] = json.dumps(r["metrics"], ensure_ascii=False,
                                             default=_json_default)
            w.writerow(row)

    # verdict_table.csv（cell 聚合，M9.7）
    table = aggregate_cells(rows)
    with open(os.path.join(out_dir, "verdict_table.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(table[0].keys()) if table else [])
        w.writeheader()
        w.writerows(table)

    # manifest.json（矩阵级；run 级 config_hash 由 NDJSON 日志层携带）
    manifest = {
        "type": "matrix_manifest",
        "spec_version": SPEC_VERSION,
        "matrix_id": matrix_id,
        "created": datetime.now(timezone.utc).isoformat(),
        "git_commit": logschema._git_version(),
        "grid": grid or {},
        "seed_rule": "P6.2",
        "n_runs": len(rows),
    }
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2, sort_keys=True)

    # logs/ 抽样 NDJSON：每 (scenario_code, config_code) 首 rep 一条基线 env0 小日志，
    # 写入前经 validate_log 零错误断言（P8.3 契约链路自检）
    log_dir = os.path.join(out_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    seen = set()
    for r in rows:
        key = (r["scenario_code"], r["config_code"])
        if key in seen or r["rep"] != 0:
            continue
        seen.add(key)
        code, config_code = key
        model = build_env0(Env0Config())
        seed = derive_seed(code, config_code, 0)
        meta = logschema.make_metadata(
            model, seed, code, "sample",
            agent_config={"m1": r["m1"], "m2": r["m2"], "m4": r["m4"], "sigma": r["sigma"]})
        trajs = simulate.simulate_trajectories(model, seed, T=3, n_traj=4)
        flat = [rec for tr in trajs for rec in tr]
        errors = logschema.validate_log(meta, flat, model.alphabet)
        if errors:
            raise RuntimeError(f"抽样日志 P8.3 校验失败 s{code}/c{config_code}: {errors}")
        logschema.write_run(os.path.join(log_dir, f"s{code:02d}_c{config_code}.ndjson"),
                            meta, trajs)
