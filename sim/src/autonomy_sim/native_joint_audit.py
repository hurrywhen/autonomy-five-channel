"""R18 native joint-log end-to-end audit (internal concept validation).

R18 answer to the R17 review: the R17-native benchmark was a shared-config
compositional fixture with per-object sampling streams.  This module instead
generates ONE joint operating-log batch from ONE registered SCM under ONE log
schema, and estimates every operating-side estimand from that same batch:

* source attribution (RNI/NRI/order average and the alternative semantic
  partition) from the logged (R^T,N^T,I^T,A^T) trajectories;
* epistemic accuracy from the logged (B_t,E_t) pairs;
* reflection fidelity from logged normative-update endorsement events
  (theta_t, self-report M_t), endorsement consistency from logged event
  counts, and Lambda from logged surgery-context (U,Y) pairs;
* viability and defense readiness from logged resource/defense records.

The execution channel is audited on a SEPARATE precommitted open-loop
intervention stream generated from the SAME environment law and logged under
the same schema.  That separation is required by the estimand: an open-loop
execution audit cannot be read off operating-policy logs, because the
operating policy is reactive.  The goal channel remains a registered
structural white-box read plus a caller-registered IRL interval (no generic
MaxEnt-IRL solver).  All channels feed one R18 full-profile certificate.

This is internal joint-log concept validation on a small registered instance,
not external construct validation, and it does not rewrite the read-only
R17-native artifact.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math

import numpy as np

from .native_benchmark import (NativeConfig, _operating_step, _share_report,
                               exact_bundle, goal_report)
from .open_loop_execution import open_loop_execution_score
from .r15_guards import state_defense_split

OPERATING_STREAM = "OPERATING_JOINT_LOG"
EXECUTION_STREAM = "OPEN_LOOP_EXECUTION_AUDIT"
LOG_SCHEMA_VERSION = "R18_JOINT_LOG_SCHEMA_V1"
STEP_FIELDS = ("t", "E", "O", "B", "N", "R", "I", "A", "G", "M", "Z", "D")
EVENT_TYPES = ("NORMATIVE_UPDATE", "SURGERY_CONTEXT")
ALTERNATIVE_PARTITION_NAME = "R_as_normative_memory"


def _canonical_hash(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def generate_operating_logs(config: NativeConfig, *, n_trajectories: int, rng) -> list[dict]:
    """One joint batch: every operating-side carrier is logged per trajectory."""
    config.validate()
    horizon = config.horizon
    defense = min(config.defense_margins)
    logs = []
    for k in range(n_trajectories):
        x = int(rng.integers(0, 2))
        r = tuple(int(v) for v in rng.integers(0, 2, size=horizon))
        i = tuple(int(v) for v in rng.integers(0, 2, size=horizon))
        v = tuple(int(bit) for bit in (rng.random(horizon) < config.p_obs))
        rr, nn, ii, aa, ee, oo, bb = _operating_step(config, x, r, i, v)
        steps, events = [], []
        for t in range(horizon):
            theta = nn[t]
            self_report = theta ^ int(rng.random() < config.q_self)
            steps.append({"t": t, "E": ee[t], "O": oo[t], "B": bb[t], "N": nn[t],
                          "R": rr[t], "I": ii[t], "A": aa[t], "G": 1, "M": self_report,
                          "Z": float(config.resource_ratios[t]), "D": float(defense)})
            events.append({"type": "NORMATIVE_UPDATE", "t": t, "theta": theta,
                           "self_report": self_report, "endorsed": True})
        u = int(rng.integers(0, 2))
        y = u ^ config.surgery
        events.append({"type": "SURGERY_CONTEXT", "U": u, "Y": y, "J": config.surgery})
        logs.append({"stream": OPERATING_STREAM, "trajectory_id": k,
                     "exogenous": {"x": x, "r": list(r), "i": list(i), "v": list(v)},
                     "steps": steps, "events": events})
    return logs


def generate_execution_logs(config: NativeConfig, *, n_samples: int, rng) -> list[dict]:
    """Separate precommitted open-loop stream from the same environment law.

    Registered state E_1=0, N_1=0, B_1=0; do(A_1=a_1, A_2=a_2).  Intermediate
    observations are logged for provenance but the audit reads ONLY the
    terminal observation O_3; later actions never condition on them.
    """
    config.validate()
    logs = []
    for seq_index, (a1, a2) in enumerate(itertools.product((0, 1), repeat=2)):
        for k in range(n_samples):
            e = 0
            steps = []
            for t, action in ((1, a1), (2, a2)):
                e = e ^ action if config.action_effect else e
                noise = int(rng.random() < config.p_obs)
                steps.append({"t": t + 1, "E": e, "O": e ^ noise, "A": action})
            logs.append({"stream": EXECUTION_STREAM, "trajectory_id": k,
                         "sequence_index": seq_index, "sequence": [a1, a2],
                         "registered_state": {"E_1": 0, "N_1": 0, "B_1": 0},
                         "steps": steps,
                         "terminal_observation": steps[-1]["O"],
                         "uses_intermediate_observations": False})
    return logs


def _joint_counts_from_logs(logs: list[dict], horizon: int, *,
                            alternative: bool = False) -> np.ndarray:
    counts = np.zeros((2,) * (4 * horizon))
    for log in logs:
        steps = log["steps"]
        rr = tuple(step["R"] for step in steps)
        nn = tuple(step["N"] for step in steps)
        ii = tuple(step["I"] for step in steps)
        aa = tuple(step["A"] for step in steps)
        if alternative:
            # Preregistered semantic sensitivity: R reclassified into normative
            # memory; the alternative R register is empty.
            n_alt = tuple(nv ^ rv for nv, rv in zip(nn, rr))
            counts[(0,) * horizon + n_alt + ii + aa] += 1.0
        else:
            counts[rr + nn + ii + aa] += 1.0
    return counts


def _fidelity_from_events(event_pairs: list[tuple[int, int]]) -> float:
    joint = np.zeros((2, 2))
    for theta, report in event_pairs:
        joint[theta, report] += 1.0
    total = joint.sum()
    if total <= 0:
        return 0.0
    joint /= total
    pt = joint.sum(axis=1)
    pm = joint.sum(axis=0)
    mi = 0.0
    for tval in range(2):
        for mval in range(2):
            p = joint[tval, mval]
            if p > 0:
                mi += p * math.log(p / (pt[tval] * pm[mval]))
    h_theta = -float(np.sum(pt[pt > 0] * np.log(pt[pt > 0])))
    return float(mi / h_theta) if h_theta > 0 else 0.0


def estimate_from_logs(config: NativeConfig, operating_logs: list[dict],
                       execution_logs: list[dict], *, n_bootstrap: int = 100,
                       rng) -> dict:
    """Estimate every operating-side channel from the SAME joint log batch."""
    horizon = config.horizon
    n_traj = len(operating_logs)
    if n_traj < 2:
        raise ValueError("joint audit requires at least two operating trajectories")

    counts = _joint_counts_from_logs(operating_logs, horizon)
    empirical_joint = counts / counts.sum()
    registered = _share_report(empirical_joint, horizon)
    alt_counts = _joint_counts_from_logs(operating_logs, horizon, alternative=True)
    alternative = _share_report(alt_counts / alt_counts.sum(), horizon)

    # Epistemic: trajectory-block means (steps are nested within trajectories).
    per_traj_hits = np.asarray([
        np.mean([step["B"] == step["E"] for step in log["steps"]])
        for log in operating_logs])
    epi_mean = float(per_traj_hits.mean())
    epi_se = float(per_traj_hits.std(ddof=1) / math.sqrt(n_traj))

    # Reflection carriers from logged events on the same trajectories.
    event_pairs = [(event["theta"], event["self_report"])
                   for log in operating_logs for event in log["events"]
                   if event["type"] == "NORMATIVE_UPDATE"]
    updates = len(event_pairs)
    endorsements = sum(1 for log in operating_logs for event in log["events"]
                       if event["type"] == "NORMATIVE_UPDATE" and event["endorsed"])
    contexts = [(event["U"], event["Y"])
                for log in operating_logs for event in log["events"]
                if event["type"] == "SURGERY_CONTEXT"]
    fidelity = _fidelity_from_events(event_pairs)
    consistency = endorsements / updates if updates else 0.0
    lambda_sample = 1.0 - float(np.mean([y != u for u, y in contexts])) if contexts else 0.0

    # Viability/defense from logged records.
    viability = min(step["Z"] for log in operating_logs for step in log["steps"])
    defense = min(step["D"] for log in operating_logs for step in log["steps"])

    # Execution kernels from the separate open-loop stream's terminal observations.
    kernels = np.zeros((4, 2))
    kernel_counts = np.zeros((4, 2))
    for log in execution_logs:
        if log["uses_intermediate_observations"]:
            raise ValueError("execution audit must not read intermediate observations")
        kernel_counts[log["sequence_index"], log["terminal_observation"]] += 1.0
    kernels = kernel_counts / kernel_counts.sum(axis=1, keepdims=True)
    exec_score = open_loop_execution_score(kernels, n_actions=2, action_alphabet_size=2)

    # Trajectory-level bootstrap for the plug-in source shares and fidelity.
    boot = {key: [] for key in ("normative_share_RNI", "normative_share_NRI",
                                 "normative_share_order_average", "joint_di_bits")}
    boot_alt = {key: [] for key in boot}
    fidelity_boot = []
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n_traj, size=n_traj)
        resampled_counts = np.zeros_like(counts)
        resampled_alt = np.zeros_like(counts)
        pairs = []
        for j in idx:
            log = operating_logs[int(j)]
            steps = log["steps"]
            rr = tuple(step["R"] for step in steps)
            nn = tuple(step["N"] for step in steps)
            ii = tuple(step["I"] for step in steps)
            aa = tuple(step["A"] for step in steps)
            resampled_counts[rr + nn + ii + aa] += 1.0
            n_alt = tuple(nv ^ rv for nv, rv in zip(nn, rr))
            resampled_alt[(0,) * horizon + n_alt + ii + aa] += 1.0
            pairs.extend((event["theta"], event["self_report"])
                         for event in log["events"] if event["type"] == "NORMATIVE_UPDATE")
        report = _share_report(resampled_counts / resampled_counts.sum(), horizon)
        report_alt = _share_report(resampled_alt / resampled_alt.sum(), horizon)
        for key in boot:
            boot[key].append(report[key])
            boot_alt[key].append(report_alt[key])
        fidelity_boot.append(_fidelity_from_events(pairs))

    def _interval(values):
        arr = np.asarray(values, dtype=float)
        return {"bootstrap_se": float(arr.std(ddof=1)),
                "percentile_95": [float(np.percentile(arr, 2.5)),
                                  float(np.percentile(arr, 97.5))]}

    source_intervals = {key: _interval(values) for key, values in boot.items()}
    alternative_intervals = {key: _interval(values) for key, values in boot_alt.items()}
    fidelity_interval = _interval(fidelity_boot)

    z = 1.96
    n_exec = float(kernel_counts.sum(axis=1)[0])
    kernel_intervals = []
    for seq_index in range(4):
        p_hat = float(kernels[seq_index, 1])
        denom = 1 + z * z / n_exec
        center = (p_hat + z * z / (2 * n_exec)) / denom
        half = z * math.sqrt(p_hat * (1 - p_hat) / n_exec
                             + z * z / (4 * n_exec * n_exec)) / denom
        kernel_intervals.append([max(0.0, center - half), min(1.0, center + half)])

    a_org = registered["normative_share_RNI"]
    a_exec = float(exec_score["a_exec"])
    a_ref = fidelity * consistency * lambda_sample
    goal = goal_report()
    channels = {"a_org_RNI": a_org, "a_goal_structural": goal["structural_point"],
                "a_exec_open_loop": a_exec, "a_epi": epi_mean, "a_ref": a_ref}
    split = state_defense_split(1.0, resource_ratios=[viability],
                                defense_margins=[defense])
    return {
        "source": {"registered_partition": registered,
                   f"alternative_partition_{ALTERNATIVE_PARTITION_NAME}": alternative},
        "source_bootstrap_intervals": source_intervals,
        "alternative_bootstrap_intervals": alternative_intervals,
        "epistemic": {"sample_mean": epi_mean, "trajectory_block_se": epi_se,
                      "normal_95": [max(0.0, epi_mean - z * epi_se),
                                    min(1.0, epi_mean + z * epi_se)]},
        "reflection": {"fidelity": fidelity, "endorsement_consistency": consistency,
                       "Lambda": lambda_sample, "A_ref": a_ref,
                       "fidelity_bootstrap": fidelity_interval,
                       "event_counts": {"normative_update_events": updates,
                                        "endorsement_events": endorsements,
                                        "surgery_contexts": len(contexts)}},
        "execution_open_loop": {"sample_a_exec": a_exec,
                                "sequence_kernels": kernels.tolist(),
                                "kernel_wilson_95": kernel_intervals,
                                "score": exec_score,
                                "uses_intermediate_observations": False},
        "goal": goal,
        "viability_state": split["viability_state"],
        "defense_readiness": split["defense_readiness"],
        "channels": channels,
        "state_autonomy_RNI": split["state_autonomy"],
    }


def exact_event_counts(config: NativeConfig) -> dict:
    """Logged-carrier counts for the exact-enumeration certificate.

    The exact truth path enumerates every (x, r^T, i^T, v^T) assignment of the
    registered SCM; each enumerated trajectory carries T endorsed normative
    updates and one surgery context.  These are enumeration carriers, not
    sampled events, and are labeled as such.
    """
    config.validate()
    n_trajectories = 2 ** (1 + 3 * config.horizon)
    updates = n_trajectories * config.horizon
    return {"normative_update_events": updates,
            "endorsement_events": updates,
            "surgery_contexts": n_trajectories,
            "carrier": "EXACT_ENUMERATION_OF_REGISTERED_SCM"}


def run_joint_audit(*, n_samples: int = 8192, seed: int = 20261121,
                    n_bootstrap: int = 100) -> dict:
    config = NativeConfig(surgery=0)
    rng = np.random.default_rng(seed)
    operating_logs = generate_operating_logs(config, n_trajectories=n_samples, rng=rng)
    execution_logs = generate_execution_logs(config, n_samples=n_samples, rng=rng)
    sampled = estimate_from_logs(config, operating_logs, execution_logs,
                                 n_bootstrap=n_bootstrap, rng=rng)
    exact = exact_bundle(config)
    surgery_exact = exact_bundle(NativeConfig(surgery=1))
    decoupled_exact = exact_bundle(NativeConfig(action_effect=False))

    def _errors(sampled_report, exact_report):
        return {key: float(abs(sampled_report[key] - exact_report[key]))
                for key in ("normative_share_RNI", "normative_share_NRI",
                            "normative_share_order_average", "joint_di_bits")}

    exact_registered = exact["source"]["registered_partition"]
    exact_alternative = exact["source"][f"alternative_partition_{ALTERNATIVE_PARTITION_NAME}"]
    return {
        "artifact_version": "R18-native-joint-audit-v1",
        "status": "INTERNAL_JOINT_LOG_CONCEPT_VALIDATION_NOT_EXTERNAL",
        "config": {
            "horizon": config.horizon, "p_obs": config.p_obs, "q_self": config.q_self,
            "surgery": config.surgery, "action_effect": config.action_effect,
            "resource_ratios": list(config.resource_ratios),
            "defense_margins": list(config.defense_margins),
            "weights": list(config.weights),
        },
        "seed": seed,
        "n_samples_per_stream": n_samples,
        "n_bootstrap": n_bootstrap,
        "log_schema": {"version": LOG_SCHEMA_VERSION, "step_fields": list(STEP_FIELDS),
                       "event_types": list(EVENT_TYPES),
                       "streams": [OPERATING_STREAM, EXECUTION_STREAM]},
        "logs": {
            "operating_trajectories": len(operating_logs),
            "execution_trajectories": len(execution_logs),
            "operating_log_sha256": _canonical_hash(operating_logs),
            "execution_log_sha256": _canonical_hash(execution_logs),
            "operating_excerpt": operating_logs[0],
            "execution_excerpt": execution_logs[0],
        },
        "exact_truth": exact,
        "sampled": sampled,
        "sampling_errors": {
            "source_registered": _errors(sampled["source"]["registered_partition"],
                                         exact_registered),
            "source_alternative": _errors(
                sampled["source"][f"alternative_partition_{ALTERNATIVE_PARTITION_NAME}"],
                exact_alternative),
            "epistemic_abs": float(abs(sampled["epistemic"]["sample_mean"]
                                       - exact["epistemic"]["A_epi"])),
            "fidelity_abs": float(abs(sampled["reflection"]["fidelity"]
                                      - exact["reflection"]["fidelity"])),
            "Lambda_abs": float(abs(sampled["reflection"]["Lambda"]
                                    - exact["reflection"]["Lambda"])),
            "execution_abs": float(abs(sampled["execution_open_loop"]["sample_a_exec"]
                                       - exact["execution_open_loop"]["state_averaged_a_exec"])),
        },
        "surgery_arm_exact": surgery_exact,
        "action_decoupled_negative_control_exact": decoupled_exact,
        "scope": {
            "single_scm": True,
            "single_log_schema": True,
            "single_operating_batch_for": [
                "source_attribution", "epistemic", "reflection_fidelity",
                "endorsement_consistency", "Lambda", "viability", "defense_readiness"],
            "execution_audit": ("separate precommitted open-loop intervention stream "
                                "from the same environment law; required by the estimand "
                                "because the operating policy is reactive"),
            "goal_mode": "registered structural white-box read plus caller-registered IRL interval",
            "operating_policy": "reactive closed-loop A_t=N_t xor R_t xor B_t",
            "generic_MaxEnt_IRL_solver": False,
            "external_construct_validation": False,
            "supersedes": "R17-native compositional fixture (read-only, not rewritten)",
        },
        "interpretation": ("Finite-sample implementation agreement on one registered "
                           "instance from one joint log batch; not statistical consistency, "
                           "not a power claim, and not external construct validation."),
    }