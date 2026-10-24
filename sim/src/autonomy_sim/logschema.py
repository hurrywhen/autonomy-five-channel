"""全因果日志 schema（SPEC_platform §8，外部契约）。

P8.1 run 级 metadata、P8.2 步级记录（NDJSON）、P8.3 完整性校验。
文件格式：第 1 行 {"type":"meta", ...}；其后每行 {"type":"step","traj":i, ...步级字段}。
"""
import hashlib
import json
import os
import subprocess

from .graph import Alphabet, CausalModel, _json_fallback

SPEC_VERSION = "SPEC_platform v0.1"

META_FIELDS = ("spec_version", "config_hash", "seed", "scenario_code", "mode")
STEP_FIELDS = ("t", "E_t", "O_t", "S_t", "A_t", "Z_t", "I_t", "defense_events", "damage_D")
I_CLASSES = ("sigma", "alpha", "beta", "gamma", "delta")
MODES = ("truth", "sample")


def make_metadata(model: CausalModel, seed: int, scenario_code: int, mode: str,
                  agent_config: dict | None = None) -> dict:
    """P8.1 metadata 构造。"""
    if mode not in MODES:
        raise ValueError(f"非法 mode: {mode}")
    return {
        "type": "meta",
        "spec_version": SPEC_VERSION,
        "config_hash": hashlib.sha1(
            json.dumps(model.to_dict(), sort_keys=True,
                       default=_json_fallback).encode()).hexdigest()[:12],
        "seed": int(seed),
        "scenario_code": int(scenario_code),
        "mode": mode,
        "agent_config": agent_config or {},
        "code_version": _git_version(),
    }


def _git_version() -> str:
    try:
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, cwd=root, timeout=10)
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def write_run(path: str, meta: dict, trajs: list) -> None:
    """写 NDJSON：meta 行＋逐条步级记录。"""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(meta, ensure_ascii=False, sort_keys=True) + "\n")
        for i, traj in enumerate(trajs):
            for rec in traj:
                row = {"type": "step", "traj": i, **rec}
                fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def read_run(path: str):
    """读 NDJSON，返回 (meta, trajs)。"""
    meta, trajs = None, []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if row.get("type") == "meta":
                meta = row
            elif row.get("type") == "step":
                i = row.pop("traj")
                row.pop("type", None)
                while len(trajs) <= i:
                    trajs.append([])
                trajs[i].append(row)
    return meta, trajs


def validate_log(meta: dict, records: list, alphabet: Alphabet) -> list:
    """P8.3 完整性校验：返回错误列表（空=通过）。未知字段忽略，必填缺失/越界/不归一拒绝。"""
    errors = []
    for f in META_FIELDS:
        if f not in meta:
            errors.append(f"metadata 缺字段: {f}")
    if "mode" in meta and meta["mode"] not in MODES:
        errors.append(f"metadata.mode 非法: {meta['mode']}")
    al = alphabet
    bounds = {"E_t": al.n_E, "O_t": al.n_O, "A_t": al.n_A, "Z_t": al.n_Z}
    s_bounds = {"G": al.n_G, "B": al.n_B, "M": al.n_M, "R": al.n_R}
    for idx, rec in enumerate(records):
        for f in STEP_FIELDS:
            if f not in rec:
                errors.append(f"record[{idx}] 缺字段: {f}")
        if errors and not all(f in rec for f in ("E_t", "S_t", "A_t")):
            continue  # 关键字段缺失时跳过后续类型检查
        if not isinstance(rec.get("t"), int) or rec["t"] < 0:
            errors.append(f"record[{idx}].t 非法")
        for f, n in bounds.items():
            v = rec.get(f)
            if f in rec and (not isinstance(v, int) or not (0 <= v < n)):
                errors.append(f"record[{idx}].{f} 越界: {v} (字母表大小 {n})")
        s = rec.get("S_t", {})
        if isinstance(s, dict):
            for f, n in s_bounds.items():
                v = s.get(f)
                if not isinstance(v, int) or not (0 <= v < n):
                    errors.append(f"record[{idx}].S_t.{f} 越界: {v} (字母表大小 {n})")
        else:
            errors.append(f"record[{idx}].S_t 非对象")
        it = rec.get("I_t", {})
        if isinstance(it, dict):
            for c in I_CLASSES:
                v = it.get(c)
                if not isinstance(v, (int, float)) or v < 0:
                    errors.append(f"record[{idx}].I_t.{c} 非法: {v}")
        else:
            errors.append(f"record[{idx}].I_t 非对象")
        bd = rec.get("belief_dist")
        if bd is not None:
            ok = (isinstance(bd, list) and len(bd) == al.n_B
                  and all(isinstance(x, (int, float)) and x >= 0 for x in bd))
            if not ok:
                errors.append(f"record[{idx}].belief_dist 结构非法")
            elif abs(sum(bd) - 1.0) > 1e-6:
                errors.append(f"record[{idx}].belief_dist 不归一: sum={sum(bd)}")
    return errors
