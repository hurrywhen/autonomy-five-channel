"""R21 joint trajectory bootstrap: full-channel composite uncertainty.

The R20 share-conditional composite interval propagates ONLY the source-share
basic bootstrap interval, holding the execution/epistemic/reflection channels
at their plug-in points.  The R20 review correctly noted that its under-coverage
therefore has two causes: directed-information plug-in bias AND the
share-conditional design (other channels' estimation error and inter-channel
covariance are not propagated).

This module provides the SUPPLEMENTARY joint diagnostic: a trajectory-block
bootstrap that, on every resample, recomputes ALL operating-side channels from
the SAME resampled operating batch (preserving their within-batch covariance)
and the execution channel from the independent precommitted stream (resampled
stratified by sequence, independent of the operating batch by design), then
recomputes the composite per convention.  The resulting percentile interval is
a genuine joint composite sampling interval.

It is a DIAGNOSTIC, not the certificate's reported semantics: the formal R21
certificate still reports the honestly-named share-conditional interval.  The
joint diagnostic quantifies how much of the under-coverage is attributable to
the conditional design versus plug-in bias.  It does NOT remove plug-in bias
(a bias-corrected or bias-aware estimator would be a separate change).

Efficiency: per-trajectory sufficient statistics are precomputed once, so each
resample is numpy aggregation plus a small (4x2) Blahut--Arimoto capacity call
(the well-conditioned, unique capacity VALUE; no canonical-input IPF needed).
Deterministic given the seed.  Internal finite-sample diagnostic, not external
validation, not a power or universal-coverage claim.
"""
from __future__ import annotations

import math

import numpy as np

from .aggregate import composite_A
from .empowerment import channel_capacity
from .native_benchmark import NativeConfig, _share_report, goal_report
from .native_joint_audit import ALTERNATIVE_PARTITION_NAME

CONVENTIONS = (("RNI", "normative_share_RNI"),
               ("NRI", "normative_share_NRI"),
               ("order_average", "normative_share_order_average"))
JOINT_BOOTSTRAP_CONSTRUCTION = "PERCENTILE_95_OF_JOINT_COMPOSITE_REPLICATES"
JOINT_RESAMPLING = {
    "operating": "trajectory_with_replacement_joint_all_operating_channels",
    "execution": "stratified_by_precommitted_sequence_independent_of_operating",
    "resampling_unit": "trajectory",
}


def _fidelity_from_joint(joint: np.ndarray) -> float:
    total = float(joint.sum())
    if total <= 0:
        return 0.0
    p = joint / total
    pt = p.sum(axis=1)
    pm = p.sum(axis=0)
    mi = 0.0
    for tval in range(2):
        for mval in range(2):
            pij = p[tval, mval]
            if pij > 0:
                mi += pij * math.log(pij / (pt[tval] * pm[mval]))
    h_theta = -float(np.sum(pt[pt > 0] * np.log(pt[pt > 0])))
    return float(mi / h_theta) if h_theta > 0 else 0.0


def _operating_sufficient_stats(operating_logs: list[dict], horizon: int):
    n = len(operating_logs)
    shape = (2,) * (4 * horizon)
    size = int(np.prod(shape))
    reg_idx = np.zeros(n, dtype=np.int64)
    alt_idx = np.zeros(n, dtype=np.int64)
    epi_hits = np.zeros(n, dtype=float)
    fid_contrib = np.zeros((n, 2, 2), dtype=float)
    updates = np.zeros(n, dtype=float)
    endorsements = np.zeros(n, dtype=float)
    ctx_count = np.zeros(n, dtype=float)
    ctx_mismatch = np.zeros(n, dtype=float)
    theta_mask = np.zeros(n, dtype=np.int64)
    min_z = np.zeros(n, dtype=float)
    min_d = np.zeros(n, dtype=float)
    for k, log in enumerate(operating_logs):
        steps = log["steps"]
        rr = tuple(step["R"] for step in steps)
        nn = tuple(step["N"] for step in steps)
        ii = tuple(step["I"] for step in steps)
        aa = tuple(step["A"] for step in steps)
        reg_idx[k] = int(np.ravel_multi_index(rr + nn + ii + aa, shape))
        n_alt = tuple(nv ^ rv for nv, rv in zip(nn, rr))
        alt_idx[k] = int(np.ravel_multi_index((0,) * horizon + n_alt + ii + aa, shape))
        epi_hits[k] = float(np.mean([step["B"] == step["E"] for step in steps]))
        for event in log["events"]:
            if event["type"] == "NORMATIVE_UPDATE":
                theta = int(event["theta"])
                fid_contrib[k, theta, int(event["self_report"])] += 1.0
                updates[k] += 1.0
                endorsements[k] += 1.0 if event["endorsed"] else 0.0
                theta_mask[k] |= (1 << theta)
            elif event["type"] == "SURGERY_CONTEXT":
                ctx_count[k] += 1.0
                ctx_mismatch[k] += 1.0 if event["Y"] != event["U"] else 0.0
        min_z[k] = min(step["Z"] for step in steps)
        min_d[k] = min(step["D"] for step in steps)
    return {"shape": shape, "size": size, "reg_idx": reg_idx, "alt_idx": alt_idx,
            "epi_hits": epi_hits, "fid_contrib": fid_contrib, "updates": updates,
            "endorsements": endorsements, "ctx_count": ctx_count,
            "ctx_mismatch": ctx_mismatch, "theta_mask": theta_mask,
            "min_z": min_z, "min_d": min_d}


def _execution_sufficient_stats(execution_logs: list[dict]):
    by_seq: dict[int, list[int]] = {}
    for log in execution_logs:
        if log["uses_intermediate_observations"]:
            raise ValueError("execution audit must not read intermediate observations")
        by_seq.setdefault(int(log["sequence_index"]), []).append(
            int(log["terminal_observation"]))
    seq_indices = sorted(by_seq)
    terminals = {s: np.asarray(by_seq[s], dtype=float) for s in seq_indices}
    return seq_indices, terminals


def _interval(values) -> dict:
    arr = np.asarray(values, dtype=float)
    return {"bootstrap_se": float(arr.std(ddof=1)),
            "bootstrap_mean": float(arr.mean()),
            "percentile_95": [float(np.percentile(arr, 2.5)),
                              float(np.percentile(arr, 97.5))]}


def joint_composite_bootstrap(config: NativeConfig, operating_logs: list[dict],
                              execution_logs: list[dict], *, n_bootstrap: int = 200,
                              rng) -> dict:
    """Joint trajectory bootstrap recomputing ALL channels and the composite.

    Returns per-partition/per-convention joint composite percentile intervals
    plus per-channel bootstrap intervals (diagnostics).  Deterministic given rng.
    """
    horizon = config.horizon
    n = len(operating_logs)
    if n < 2:
        raise ValueError("joint bootstrap requires at least two operating trajectories")
    if n_bootstrap < 2:
        raise ValueError("joint bootstrap requires at least two resamples")
    stats = _operating_sufficient_stats(operating_logs, horizon)
    seq_indices, terminals = _execution_sufficient_stats(execution_logs)
    n_seq = len(seq_indices)
    normalizer = 2 * math.log(2.0)
    goal = goal_report()["structural_point"]
    weights = config.weights
    shape, size = stats["shape"], stats["size"]

    comp_boot = {"registered": {c: [] for c, _ in CONVENTIONS},
                 ALTERNATIVE_PARTITION_NAME: {c: [] for c, _ in CONVENTIONS}}
    chan_boot = {key: [] for key in ("a_exec", "a_epi", "a_ref", "fidelity",
                                     "endorsement_consistency", "Lambda",
                                     "viability_state")}
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        reg_counts = np.bincount(stats["reg_idx"][idx], minlength=size).reshape(shape)
        alt_counts = np.bincount(stats["alt_idx"][idx], minlength=size).reshape(shape)
        reg_report = _share_report(reg_counts / reg_counts.sum(), horizon)
        alt_report = _share_report(alt_counts / alt_counts.sum(), horizon)
        epi_b = float(stats["epi_hits"][idx].mean())
        fid_joint = stats["fid_contrib"][idx].sum(axis=0)
        fidelity_b = _fidelity_from_joint(fid_joint)
        upd_b = float(stats["updates"][idx].sum())
        consistency_b = (float(stats["endorsements"][idx].sum()) / upd_b
                         if upd_b > 0 else None)
        ctx_b = float(stats["ctx_count"][idx].sum())
        lambda_b = (1.0 - float(stats["ctx_mismatch"][idx].sum()) / ctx_b
                    if ctx_b > 0 else None)
        theta_bits = int(np.bitwise_or.reduce(stats["theta_mask"][idx]))
        zero_entropy = upd_b > 0 and bin(theta_bits).count("1") <= 1
        thin = 0 < upd_b < 30
        degraded = (zero_entropy or thin or consistency_b is None
                    or lambda_b is None or upd_b == 0)
        a_ref_b = (None if degraded else fidelity_b * consistency_b * lambda_b)
        viability_b = float(stats["min_z"][idx].min())
        # Execution: stratified resampling within each precommitted sequence.
        kernels = np.zeros((n_seq, 2))
        for row, s in enumerate(seq_indices):
            term = terminals[s]
            draw = term[rng.integers(0, len(term), size=len(term))]
            p1 = float(draw.mean())
            kernels[row, 0] = 1.0 - p1
            kernels[row, 1] = p1
        capacity_b, _q = channel_capacity(kernels)
        a_exec_b = min(1.0, float(capacity_b) / normalizer)
        chan_boot["a_exec"].append(a_exec_b)
        chan_boot["a_epi"].append(epi_b)
        chan_boot["fidelity"].append(fidelity_b)
        chan_boot["endorsement_consistency"].append(
            consistency_b if consistency_b is not None else float("nan"))
        chan_boot["Lambda"].append(lambda_b if lambda_b is not None else float("nan"))
        chan_boot["a_ref"].append(a_ref_b if a_ref_b is not None else float("nan"))
        chan_boot["viability_state"].append(viability_b)
        rest = (goal, a_exec_b, epi_b, a_ref_b if a_ref_b is not None else 1.0)
        for partition, report in (("registered", reg_report),
                                  (ALTERNATIVE_PARTITION_NAME, alt_report)):
            for convention, key in CONVENTIONS:
                share_b = report[key]
                value = (None if (share_b is None or a_ref_b is None)
                         else float(composite_A(viability_b, (share_b,) + rest,
                                                weights, sigma=1.0)))
                comp_boot[partition][convention].append(
                    value if value is not None else float("nan"))

    composite_intervals = {}
    for partition, conventions in comp_boot.items():
        composite_intervals[partition] = {}
        for convention, values in conventions.items():
            arr = np.asarray(values, dtype=float)
            finite = arr[np.isfinite(arr)]
            composite_intervals[partition][convention] = (
                _interval(finite) if finite.size >= 2 else None)
    channel_intervals = {}
    for key, values in chan_boot.items():
        arr = np.asarray(values, dtype=float)
        finite = arr[np.isfinite(arr)]
        channel_intervals[key] = _interval(finite) if finite.size >= 2 else None
    return {
        "n_bootstrap": n_bootstrap,
        "construction": JOINT_BOOTSTRAP_CONSTRUCTION,
        "resampling": dict(JOINT_RESAMPLING),
        "scope": ("SUPPLEMENTARY_JOINT_DIAGNOSTIC_NOT_CERTIFICATE_REPORTED_SEMANTICS_"
                  "DOES_NOT_REMOVE_PLUGIN_BIAS"),
        "composite_intervals": composite_intervals,
        "channel_intervals": channel_intervals,
        "note": ("Joint trajectory bootstrap recomputes all operating-side channels "
                 "from the same resampled batch (within-batch covariance preserved) and "
                 "the execution channel from the independent stream (stratified by "
                 "sequence). The percentile interval is a genuine joint composite "
                 "sampling interval; it addresses the share-conditional design limitation "
                 "but not directed-information plug-in bias."),
    }