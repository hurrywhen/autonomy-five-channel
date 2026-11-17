"""全因果日志 schema（SPEC_platform §8，外部契约）。

P8.1 run 级 metadata、P8.2 步级记录（NDJSON）、P8.3 完整性校验。
文件格式：第 1 行 {"type":"meta", ...}；其后每行 {"type":"step","traj":i, ...步级字段}。
"""
import hashlib
import json
import math
import os
import re
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


R16_CHANNEL_SCHEMA_VERSION = "R16_CHANNEL_SCHEMA_V1"
R16_CERTIFICATE_FIELDS = (
    "layer", "construct_scope", "channel_schema_version", "org_mode",
    "goal_mode", "state_readiness_version", "model_hash", "evidence_hash",
    "state_autonomy", "viability_state", "defense_readiness",
    "surgery_history", "Lambda", "lambda_status", "source_registration",
    "registration_completeness", "mechanism_evidence", "evidence_ceiling",
    "external_construct_validation", "integrity_certificate",
)
# Retain the old public symbol while making its contents the current R16 schema.
R15_CERTIFICATE_FIELDS = R16_CERTIFICATE_FIELDS
_REGISTRATION_VALUES = {"COMPLETE", "INCOMPLETE", "UNKNOWN"}
_MECHANISM_VALUES = {"NONE", "SCM_AUDITED"}
_GOAL_MODES = {"STRUCTURAL_POINT", "IRL_INTERVAL"}
_LOWERCASE_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _is_finite_unit_number(value: object) -> bool:
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and 0.0 <= value <= 1.0 and math.isfinite(value))


def _is_artifact_hash(value: object) -> bool:
    return isinstance(value, str) and _LOWERCASE_SHA256.fullmatch(value) is not None


def validate_r15_certificate(cert: dict) -> list[str]:
    """Validate the R16 sidecar under the compatibility-named R15 API.

    This validator intentionally checks registration and mechanism evidence
    independently.  Complete fields never imply an SCM audit.  Schema and mode
    tags are checked exactly, and L1/L2 artifact hashes must be lowercase
    64-hex strings.  Hashes bind registered artifacts only: their syntax does
    not establish provenance, external truth, or construct validation.
    Legacy logs and historical result bundles are not modified.
    """
    errors = []
    for field in R16_CERTIFICATE_FIELDS:
        if field not in cert:
            errors.append(f"R16 certificate missing field: {field}")
    if errors:
        return errors

    layer = cert["layer"]
    if layer not in {"L0", "L1", "L2"}:
        errors.append("invalid layer")
    expected_scope = "internal_causal_only" if layer == "L0" else "normative_structure_required"
    if cert["construct_scope"] != expected_scope:
        errors.append("construct scope inconsistent with layer")
    if cert["channel_schema_version"] != R16_CHANNEL_SCHEMA_VERSION:
        errors.append(f"channel_schema_version must be {R16_CHANNEL_SCHEMA_VERSION}")
    expected_org_mode = "L0_INTERNAL" if layer == "L0" else "L1_NORMATIVE_NR"
    if cert["org_mode"] != expected_org_mode:
        errors.append(f"org_mode must be {expected_org_mode} for {layer}")
    if cert["goal_mode"] not in _GOAL_MODES:
        errors.append("goal_mode must be STRUCTURAL_POINT or IRL_INTERVAL")
    if cert["state_readiness_version"] != "R15_SPLIT":
        errors.append("state_readiness_version must be R15_SPLIT")

    model_hash_valid = _is_artifact_hash(cert["model_hash"])
    evidence_hash_valid = _is_artifact_hash(cert["evidence_hash"])
    for field, valid in (("model_hash", model_hash_valid),
                         ("evidence_hash", evidence_hash_valid)):
        if layer in {"L1", "L2"} and not valid:
            errors.append(f"{field} must be a lowercase 64-hex string for L1/L2")
        elif layer == "L0" and cert[field] is not None and not valid:
            errors.append(f"{field} must be null or a lowercase 64-hex string for L0")

    for field in ("state_autonomy", "viability_state", "defense_readiness"):
        if not _is_finite_unit_number(cert[field]):
            errors.append(f"{field} must be a finite number in [0,1]")
    # A_state = V_state * F with F in [0,1].  In particular, zero viability
    # cannot coexist with positive present-state autonomy or an audited ceiling.
    if (_is_finite_unit_number(cert["state_autonomy"])
            and _is_finite_unit_number(cert["viability_state"])
            and cert["state_autonomy"] > cert["viability_state"] + 1e-12):
        errors.append("state_autonomy must not exceed viability_state")
    if cert["surgery_history"] not in {0, 1, None}:
        errors.append("surgery_history must be 0, 1, or null")
    if cert["lambda_status"] not in {"DEFINED", "NOT_APPLICABLE", "UNKNOWN"}:
        errors.append("invalid lambda_status")
    if cert["lambda_status"] == "DEFINED":
        if not _is_finite_unit_number(cert["Lambda"]):
            errors.append("DEFINED Lambda requires a finite value in [0,1]")
    elif cert["Lambda"] is not None:
        errors.append("N/A or UNKNOWN Lambda must be null")
    if layer == "L2" and cert["lambda_status"] == "NOT_APPLICABLE":
        errors.append("L2 Lambda cannot be NOT_APPLICABLE")

    if cert["source_registration"] not in _REGISTRATION_VALUES:
        errors.append("invalid source_registration")
    if cert["registration_completeness"] not in _REGISTRATION_VALUES:
        errors.append("invalid registration_completeness")
    if cert["source_registration"] != cert["registration_completeness"]:
        errors.append("source_registration and registration_completeness must agree")
    mechanism = cert["mechanism_evidence"]
    if mechanism not in _MECHANISM_VALUES:
        errors.append("mechanism_evidence must be NONE or SCM_AUDITED")
    if mechanism == "SCM_AUDITED" and not (model_hash_valid and evidence_hash_valid):
        errors.append("SCM_AUDITED requires valid model_hash and evidence_hash bindings")

    unknown = (cert["surgery_history"] is None
               or cert["source_registration"] != "COMPLETE"
               or cert["registration_completeness"] != "COMPLETE"
               or cert["lambda_status"] == "UNKNOWN"
               or (layer == "L2" and cert["lambda_status"] != "DEFINED"))
    if mechanism in _MECHANISM_VALUES:
        if unknown:
            expected_ceiling = "LIMITED"
        elif mechanism == "SCM_AUDITED":
            expected_ceiling = "SCM_AUDITED"
        else:
            expected_ceiling = "REGISTERED_COMPLETE"
        if cert["evidence_ceiling"] != expected_ceiling:
            errors.append(f"evidence_ceiling must be {expected_ceiling}")
    if cert["external_construct_validation"] is not False:
        errors.append("external construct validation cannot be asserted")
    if cert["integrity_certificate"] is not False:
        errors.append("an R16 score is not an integrity certificate")
    return errors


def write_r15_certificate(path: str, cert: dict) -> None:
    """Fail-closed R16 writer retaining the historical R15 function name."""
    errors = validate_r15_certificate(cert)
    if errors:
        raise ValueError("invalid R16 certificate: " + "; ".join(errors))
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(cert, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


# Current-schema names; historical R15 symbols remain compatibility aliases.
validate_r16_certificate = validate_r15_certificate
write_r16_certificate = write_r15_certificate
