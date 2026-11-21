"""R19 native joint-log audit (internal concept validation).

Supersedes the R18 joint audit (read-only, retained with its recorded
cross-environment replay failure).  R19 changes:

1. **Numerical reproducibility.**  The execution capacity optimizer's
   capacity-achieving input distribution is generally non-unique (the native
   parity kernel has a flat optimal face); raw solver coordinates drifted
   ~7.5e-10 across platforms and broke the R18 byte-level replay.  R19 uses
   the declared canonicalization rule (``canonicalize_input=True``) and binds
   ``evidence_hash`` to IMMUTABLE registered inputs (raw log hashes + config)
   only, never to iterative-optimizer auxiliary coordinates.
2. **Corrected state_autonomy_RNI.**  The R18 estimator passed a unit channel
   composite to ``state_defense_split``, so the returned field was only the
   resource gate (0.8).  R19 computes it from the actual five channels; a
   regression test asserts equality with the registered RNI certificate
   composite.
3. **Sampled negative controls.**  The surgery arm (Lambda=0) and the
   action-decoupled arm (zero execution) are now also generated and estimated
   through the same joint-log pipeline, not only by exact enumeration.
4. **Near-zero estimation semantics.**  Bootstrap bias-corrected shares,
   composite uncertainty propagation per convention, and a post hoc frozen
   internal detection limit for near-zero shares (below-limit conventions are
   reported with interval semantics, not high-confidence positive points).
5. **Degradation-aware reflection.**  Thin change logs and zero-entropy
   ensembles degrade the reflection channel to the paper's flagged interval
   instead of forcing a point.

This is internal joint-log concept validation on one small registered
instance, not external construct validation.
"""
from __future__ import annotations

import hashlib
import json
import math

import numpy as np

from .aggregate import composite_A
from .native_benchmark import NativeConfig, _share_report, exact_bundle, goal_report
from .native_joint_audit import (ALTERNATIVE_PARTITION_NAME, EXECUTION_STREAM,
                                 LOG_SCHEMA_VERSION, OPERATING_STREAM, STEP_FIELDS,
                                 EVENT_TYPES, _canonical_hash, _fidelity_from_events,
                                 _joint_counts_from_logs, generate_execution_logs,
                                 generate_operating_logs)
from .open_loop_execution import open_loop_execution_score

# Post hoc frozen internal reporting constants (NOT a domain SESOI, NOT
# preregistered before outcomes; frozen 2026-11-22 for future audits).
NRI_SHARE_DETECTION_LIMIT = 1e-6
MIN_REFLECTION_EVENTS = 30
R19_LOG_SCHEMA_VERSION = "R19_JOINT_LOG_SCHEMA_V1"


def _reflection_factors(event_pairs, updates: int, endorsements: int, contexts):
    """Paper D-ref degradation rules applied to logged carriers."""
    theta_values = {theta for theta, _ in event_pairs}
    zero_entropy = updates > 0 and len(theta_values) <= 1
    thin = 0 < updates < MIN_REFLECTION_EVENTS
    no_carriers = updates == 0
    fidelity = None if (no_carriers or zero_entropy) else _fidelity_from_events(event_pairs)
    consistency = None if (no_carriers or thin) else endorsements / updates
    lambda_sample = (None if not contexts else
                     1.0 - float(np.mean([y != u for u, y in contexts])))
    reasons = []
    if no_carriers:
        reasons.append("NO_LOG_CARRIERS")
    if thin:
        reasons.append("THIN_LOG")
    if zero_entropy:
        reasons.append("ZERO_ENTROPY_ENSEMBLE")
    if len(reasons) > 1:
        reasons = ["MIXED_DEGRADATION"]
    defined = [v for v in (fidelity, consistency, lambda_sample) if v is not None]
    upper = 1.0
    for value in defined:
        upper *= value
    degraded = fidelity is None or consistency is None or lambda_sample is None
    return {"fidelity": fidelity, "endorsement_consistency": consistency,
            "Lambda": lambda_sample,
            "A_ref": None if degraded else fidelity * consistency * lambda_sample,
            "A_ref_interval": [0.0, upper] if degraded else None,
            "degradation_reason": reasons[0] if reasons else None}


def estimate_from_logs_r19(config: NativeConfig, operating_logs: list[dict],
                           execution_logs: list[dict], *, n_bootstrap: int = 100,
                           rng) -> dict:
    """Estimate every operating-side channel from the SAME joint log batch.

    R19 corrected estimator: canonicalized execution input, actual five-channel
    state_autonomy_RNI, degradation-aware reflection, bias-corrected shares and
    per-convention composite bootstrap intervals.
    """
    horizon = config.horizon
    n_traj = len(operating_logs)
    if n_traj < 2:
        raise ValueError("joint audit requires at least two operating trajectories")

    counts = _joint_counts_from_logs(operating_logs, horizon)
    registered = _share_report(counts / counts.sum(), horizon)
    alt_counts = _joint_counts_from_logs(operating_logs, horizon, alternative=True)
    alternative = _share_report(alt_counts / alt_counts.sum(), horizon)

    per_traj_hits = np.asarray([
        np.mean([step["B"] == step["E"] for step in log["steps"]])
        for log in operating_logs])
    epi_mean = float(per_traj_hits.mean())
    epi_se = float(per_traj_hits.std(ddof=1) / math.sqrt(n_traj))

    event_pairs = [(event["theta"], event["self_report"])
                   for log in operating_logs for event in log["events"]
                   if event["type"] == "NORMATIVE_UPDATE"]
    updates = len(event_pairs)
    endorsements = sum(1 for log in operating_logs for event in log["events"]
                       if event["type"] == "NORMATIVE_UPDATE" and event["endorsed"])
    contexts = [(event["U"], event["Y"])
                for log in operating_logs for event in log["events"]
                if event["type"] == "SURGERY_CONTEXT"]
    reflection = _reflection_factors(event_pairs, updates, endorsements, contexts)
    reflection["event_counts"] = {"normative_update_events": updates,
                                  "endorsement_events": endorsements,
                                  "surgery_contexts": len(contexts)}

    viability = min(step["Z"] for log in operating_logs for step in log["steps"])
    defense = min(step["D"] for log in operating_logs for step in log["steps"])

    kernel_counts = np.zeros((4, 2))
    for log in execution_logs:
        if log["uses_intermediate_observations"]:
            raise ValueError("execution audit must not read intermediate observations")
        kernel_counts[log["sequence_index"], log["terminal_observation"]] += 1.0
    kernels = kernel_counts / kernel_counts.sum(axis=1, keepdims=True)
    exec_score = open_loop_execution_score(kernels, n_actions=2, action_alphabet_size=2,
                                           canonicalize_input=True)

    # Trajectory-level bootstrap (resampling unit = trajectory).
    share_keys = ("normative_share_RNI", "normative_share_NRI",
                  "normative_share_order_average", "joint_di_bits")
    boot = {key: [] for key in share_keys}
    boot_alt = {key: [] for key in share_keys}
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
        for key in share_keys:
            boot[key].append(report[key])
            boot_alt[key].append(report_alt[key])
        if reflection["fidelity"] is not None:
            fidelity_boot.append(_fidelity_from_events(pairs))

    def _interval(values):
        arr = np.asarray(values, dtype=float)
        return {"bootstrap_se": float(arr.std(ddof=1)),
                "bootstrap_mean": float(arr.mean()),
                "percentile_95": [float(np.percentile(arr, 2.5)),
                                  float(np.percentile(arr, 97.5))]}

    source_intervals = {key: (_interval(values) if values else None)
                        for key, values in boot.items()}
    alternative_intervals = {key: (_interval(values) if values else None)
                             for key, values in boot_alt.items()}

    # Bootstrap bias correction: corrected = 2*plugin - bootstrap_mean, clipped.
    # With n_bootstrap=0 (control arms) no correction is applied (declared).
    def _bias_corrected(report, intervals):
        out = {}
        for key in ("normative_share_RNI", "normative_share_NRI",
                    "normative_share_order_average"):
            plugin = report[key]
            if plugin is None:
                out[key] = None
            elif intervals is None or intervals[key] is None:
                out[key] = float(plugin)
            else:
                out[key] = float(min(1.0, max(0.0, 2.0 * plugin
                                               - intervals[key]["bootstrap_mean"])))
        return out

    corrected_registered = _bias_corrected(registered, source_intervals)
    corrected_alternative = _bias_corrected(alternative, alternative_intervals)

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
    a_ref = reflection["A_ref"]
    goal = goal_report()
    channels = {"a_org_RNI": a_org, "a_goal_structural": goal["structural_point"],
                "a_exec_open_loop": a_exec, "a_epi": epi_mean, "a_ref": a_ref}

    # R19 FIX: the returned state_autonomy_RNI is computed from the ACTUAL five
    # channels (R18 passed a unit composite and returned only the resource gate).
    if a_ref is None or a_org is None:
        state_autonomy_rni = None
    else:
        state_autonomy_rni = float(composite_A(
            viability, (a_org, goal["structural_point"], a_exec, epi_mean, a_ref),
            config.weights, sigma=1.0))

    # Per-convention composite uncertainty propagation (share bootstrap only;
    # other channels held at their point estimates -- declared scope).
    rest = (goal["structural_point"], a_exec, epi_mean,
            a_ref if a_ref is not None else 1.0)

    def _composite_at(share):
        if share is None or a_ref is None:
            return None
        return float(composite_A(viability, (share,) + rest, config.weights, sigma=1.0))

    composite_uncertainty = {}
    for partition_name, report, intervals, corrected in (
            ("registered", registered, source_intervals, corrected_registered),
            (ALTERNATIVE_PARTITION_NAME, alternative, alternative_intervals,
             corrected_alternative)):
        composite_uncertainty[partition_name] = {}
        for convention, key in (("RNI", "normative_share_RNI"),
                                ("NRI", "normative_share_NRI"),
                                ("order_average", "normative_share_order_average")):
            interval = intervals[key] if intervals else None
            share_95 = interval["percentile_95"] if interval else None
            composite_uncertainty[partition_name][convention] = {
                "plugin_composite": _composite_at(report[key]),
                "bias_corrected_composite": _composite_at(corrected[key]),
                "share_bootstrap_95": share_95,
                "composite_bootstrap_95": ([_composite_at(share_95[0]),
                                            _composite_at(share_95[1])]
                                           if share_95 else None),
            }

    fidelity_interval = (_interval(fidelity_boot) if fidelity_boot else None)
    return {
        "source": {"registered_partition": registered,
                   f"alternative_partition_{ALTERNATIVE_PARTITION_NAME}": alternative},
        "source_bootstrap_intervals": source_intervals,
        "alternative_bootstrap_intervals": alternative_intervals,
        "bias_corrected_shares": {"registered": corrected_registered,
                                  ALTERNATIVE_PARTITION_NAME: corrected_alternative},
        "composite_uncertainty": composite_uncertainty,
        "epistemic": {"sample_mean": epi_mean, "trajectory_block_se": epi_se,
                      "normal_95": [max(0.0, epi_mean - z * epi_se),
                                    min(1.0, epi_mean + z * epi_se)]},
        "reflection": dict(reflection, fidelity_bootstrap=fidelity_interval),
        "execution_open_loop": {"sample_a_exec": a_exec,
                                "sequence_kernels": kernels.tolist(),
                                "kernel_wilson_95": kernel_intervals,
                                "score": exec_score,
                                "uses_intermediate_observations": False},
        "goal": goal,
        "viability_state": viability,
        "defense_readiness": defense,
        "channels": channels,
        "state_autonomy_RNI": state_autonomy_rni,
    }


def _arm_logs(config: NativeConfig, *, n_samples: int, rng):
    operating = generate_operating_logs(config, n_trajectories=n_samples, rng=rng)
    execution = generate_execution_logs(config, n_samples=n_samples, rng=rng)
    return operating, execution


def run_joint_audit_r19(*, n_samples: int = 8192, seed: int = 20261122,
                        n_bootstrap: int = 100) -> dict:
    config = NativeConfig(surgery=0)
    rng = np.random.default_rng(seed)
    operating_logs, execution_logs = _arm_logs(config, n_samples=n_samples, rng=rng)
    sampled = estimate_from_logs_r19(config, operating_logs, execution_logs,
                                     n_bootstrap=n_bootstrap, rng=rng)
    surgery_config = NativeConfig(surgery=1)
    surgery_operating, surgery_execution = _arm_logs(surgery_config, n_samples=n_samples, rng=rng)
    surgery_sampled = estimate_from_logs_r19(surgery_config, surgery_operating,
                                             surgery_execution, n_bootstrap=0, rng=rng)
    decoupled_config = NativeConfig(action_effect=False)
    decoupled_operating, decoupled_execution = _arm_logs(decoupled_config,
                                                         n_samples=n_samples, rng=rng)
    decoupled_sampled = estimate_from_logs_r19(decoupled_config, decoupled_operating,
                                               decoupled_execution, n_bootstrap=0, rng=rng)
    exact = exact_bundle(config)
    surgery_exact = exact_bundle(surgery_config)
    decoupled_exact = exact_bundle(decoupled_config)

    def _errors(sampled_report, exact_report):
        return {key: float(abs(sampled_report[key] - exact_report[key]))
                for key in ("normative_share_RNI", "normative_share_NRI",
                            "normative_share_order_average", "joint_di_bits")}

    log_hashes = {
        "operating_log_sha256": _canonical_hash(operating_logs),
        "execution_log_sha256": _canonical_hash(execution_logs),
        "surgery_operating_log_sha256": _canonical_hash(surgery_operating),
        "surgery_execution_log_sha256": _canonical_hash(surgery_execution),
        "decoupled_operating_log_sha256": _canonical_hash(decoupled_operating),
        "decoupled_execution_log_sha256": _canonical_hash(decoupled_execution),
    }
    config_payload = {
        "horizon": config.horizon, "p_obs": config.p_obs, "q_self": config.q_self,
        "surgery": config.surgery, "action_effect": config.action_effect,
        "resource_ratios": list(config.resource_ratios),
        "defense_margins": list(config.defense_margins),
        "weights": list(config.weights),
    }
    # R19 evidence binding: IMMUTABLE registered inputs only.  Iterative
    # optimizer coordinates and other approximate analysis outputs are NOT
    # part of this payload (the R18 failure cause).
    evidence_payload = {"log_hashes": log_hashes, "config": config_payload,
                        "seed": seed, "n_samples_per_stream": n_samples,
                        "n_bootstrap": n_bootstrap,
                        "log_schema": R19_LOG_SCHEMA_VERSION}
    return {
        "artifact_version": "R19-native-joint-audit-v1",
        "status": "INTERNAL_JOINT_LOG_CONCEPT_VALIDATION_NOT_EXTERNAL",
        "config": config_payload,
        "seed": seed,
        "n_samples_per_stream": n_samples,
        "n_bootstrap": n_bootstrap,
        "log_schema": {"version": R19_LOG_SCHEMA_VERSION,
                       "step_fields": list(STEP_FIELDS),
                       "event_types": list(EVENT_TYPES),
                       "streams": [OPERATING_STREAM, EXECUTION_STREAM],
                       "compatible_with": LOG_SCHEMA_VERSION},
        "logs": dict(log_hashes,
                     operating_trajectories=len(operating_logs),
                     execution_trajectories=len(execution_logs),
                     operating_excerpt=operating_logs[0],
                     execution_excerpt=execution_logs[0]),
        "evidence_binding": {
            "policy": "IMMUTABLE_RAW_INPUTS_ONLY_NOT_ANALYSIS_OUTPUTS",
            "payload": evidence_payload,
            "evidence_sha256": _canonical_hash(evidence_payload),
            "excluded": ["iterative optimizer input-distribution coordinates",
                         "plug-in estimates", "bootstrap intervals"],
        },
        "exact_truth": exact,
        "sampled": sampled,
        "sampling_errors": {
            "source_registered": _errors(sampled["source"]["registered_partition"],
                                         exact["source"]["registered_partition"]),
            "source_alternative": _errors(
                sampled["source"][f"alternative_partition_{ALTERNATIVE_PARTITION_NAME}"],
                exact["source"][f"alternative_partition_{ALTERNATIVE_PARTITION_NAME}"]),
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
        "surgery_arm_sampled": surgery_sampled,
        "action_decoupled_negative_control_exact": decoupled_exact,
        "action_decoupled_negative_control_sampled": decoupled_sampled,
        "reporting_constants": {
            "nri_share_detection_limit": NRI_SHARE_DETECTION_LIMIT,
            "min_reflection_events": MIN_REFLECTION_EVENTS,
            "provenance": ("POST_HOC_FROZEN_INTERNAL_REPORTING_CONSTANTS_"
                           "NOT_DOMAIN_SESOI_NOT_PREREGISTERED_BEFORE_OUTCOMES"),
        },
        "scope": {
            "single_scm": True,
            "single_log_schema": True,
            "single_operating_batch_for": [
                "source_attribution", "epistemic", "reflection_fidelity",
                "endorsement_consistency", "Lambda", "viability", "defense_readiness"],
            "execution_audit": ("separate precommitted open-loop intervention stream "
                                "from the same environment law; required by the estimand "
                                "because the operating policy is reactive"),
            "sampled_negative_controls": ["surgery_arm", "action_decoupled_arm"],
            "goal_mode": "registered structural white-box read plus caller-registered IRL interval",
            "operating_policy": "reactive closed-loop A_t=N_t xor R_t xor B_t",
            "generic_MaxEnt_IRL_solver": False,
            "external_construct_validation": False,
            "supersedes": "R18 joint audit (read-only; cross-environment replay failure recorded)",
        },
        "interpretation": ("Finite-sample implementation agreement on one registered "
                           "instance from one joint log batch; not statistical consistency, "
                           "not a power claim, and not external construct validation. "
                           "Exact-truth composites are model anchors, not evidence that "
                           "finite samples recover the near-zero NRI endpoint."),
    }
