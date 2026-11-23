"""R22 matched interval-method contrast (supplementary diagnostic).

R21 compared the certificate's basic share-conditional interval (A) with a
percentile joint interval (C).  Those intervals differ in BOTH interval
construction and channel propagation, and their bootstrap streams differ too.
Consequently "A misses / C covers" is not an identified conditional-design
effect, and "both miss" is not an identified plug-in-bias effect.

This module computes three intervals on the SAME trajectory-bootstrap
replicates:

* A -- the existing BASIC SHARE-CONDITIONAL construction: form the basic
  (pivotal) share interval from the replicate share percentiles and propagate
  its endpoints with every other channel fixed at the original plug-in point;
* B -- the PERCENTILE SHARE-CONDITIONAL composite interval: percentile of
  composite replicates computed from the resampled share with every other
  channel fixed at the SAME original plug-in point;
* C -- the PERCENTILE JOINT composite interval: percentile of composite
  replicates with all data-estimated channels recomputed, exactly as in R21;
  the registered structural goal and model configuration remain fixed.

B versus C is a matched-replicate, matched-percentile channel-propagation
contrast.  A versus B is an interval-construction contrast.  Neither is a
formal bias decomposition or a single-cause attribution.  Plug-in bias is
assessed separately by the exact-truth multi-seed simulation summaries.

The RNG stream and per-replicate operations intentionally follow R21's joint
bootstrap.  Given the same logs, resample count, and RNG seed, C therefore
reproduces R21's joint intervals exactly (tested), provided the stronger matched
A/B input requirements succeed (defined original plug-ins and at least two
common finite replicates).  A is a matched-stream
recomputation of the certificate's construction; the formal certificate and
its original reported interval are unchanged.

Internal finite-sample diagnostic only: not external validation, not a power
or universal-coverage claim, and not a causal attribution of under-coverage.
"""
from __future__ import annotations

import hashlib
import math

import numpy as np

from .aggregate import composite_A
from .empowerment import channel_capacity
from .native_benchmark import NativeConfig, _share_report, goal_report
from .native_joint_audit import ALTERNATIVE_PARTITION_NAME
from .r20_detection import basic_bootstrap_bias_corrected_interval
from .r21_joint_bootstrap import (_execution_sufficient_stats,
                                  _fidelity_from_joint,
                                  _operating_sufficient_stats)

CONVENTIONS = (("RNI", "normative_share_RNI"),
               ("NRI", "normative_share_NRI"),
               ("order_average", "normative_share_order_average"))
METHOD_A = "A_basic_share_conditional"
METHOD_B = "B_percentile_share_conditional"
METHOD_C = "C_percentile_joint"
METHODS = (METHOD_A, METHOD_B, METHOD_C)
METHOD_LABELS = {
    METHOD_A: "basic-share-conditional",
    METHOD_B: "percentile-share-conditional",
    METHOD_C: "percentile-joint",
}
CONTRAST_POLICY = {
    "status": "DESCRIPTIVE_INTERVAL_METHOD_CONTRAST_NOT_CAUSAL_ATTRIBUTION",
    "A_vs_B": "MATCHED_REPLICATES_INTERVAL_CONSTRUCTION_CONTRAST_ONLY",
    "B_vs_C": "MATCHED_REPLICATES_MATCHED_PERCENTILE_CHANNEL_PROPAGATION_CONTRAST_ONLY",
    "A_vs_C": "MIXED_CONSTRUCTION_AND_CONDITIONING_NOT_IDENTIFIED",
    "both_miss": "NO_SINGLE_CAUSE_ATTRIBUTION_BIAS_OTHER_CHANNELS_AND_CONSTRUCTION_REMAIN_POSSIBLE",
    "plugin_bias": "ASSESSED_SEPARATELY_BY_EXACT_TRUTH_MULTI_SEED_SIMULATION_NOT_BOTH_MISS",
    "not_formal_bias_decomposition": True,
    "not_certificate_reported_semantics": True,
}


def _mask_hash(mask) -> str:
    """Platform-independent hash of the exact common-mask decisions."""
    packed = np.packbits(np.asarray(mask, dtype=bool), bitorder="big")
    return hashlib.sha256(packed.tobytes()).hexdigest()


def _percentile_summary(values) -> dict:
    arr = np.asarray(values, dtype=float)
    return {"bounds": [float(np.percentile(arr, 2.5)),
                       float(np.percentile(arr, 97.5))],
            "bootstrap_mean": float(arr.mean()),
            "bootstrap_se": float(arr.std(ddof=1))}


def summarize_matched_replicates(share0: float, share_values, conditional_values,
                                 joint_values, fixed_composite) -> tuple[dict, dict]:
    """Independently testable A/B/C construction from three replicate arrays.

    All three methods use the intersection of finite entries.  The returned
    audit hashes the Boolean mask, never native floating-point analysis outputs.
    """
    share_arr = np.asarray(share_values, dtype=float)
    cond_arr = np.asarray(conditional_values, dtype=float)
    joint_arr = np.asarray(joint_values, dtype=float)
    if not (share_arr.shape == cond_arr.shape == joint_arr.shape) or share_arr.ndim != 1:
        raise ValueError("matched replicate arrays must be one-dimensional with equal shape")
    common = np.isfinite(share_arr) & np.isfinite(cond_arr) & np.isfinite(joint_arr)
    if int(common.sum()) < 2:
        raise ValueError("fewer than two common finite A/B/C replicates")
    share_common = share_arr[common]
    cond_common = cond_arr[common]
    joint_common = joint_arr[common]
    share_perc = [float(np.percentile(share_common, 2.5)),
                  float(np.percentile(share_common, 97.5))]
    basic_share = basic_bootstrap_bias_corrected_interval(share0, *share_perc)
    entry = {
        METHOD_A: {"bounds": [float(fixed_composite(basic_share[0])),
                              float(fixed_composite(basic_share[1]))],
                   "share_basic_interval": basic_share,
                   "share_percentile_95": share_perc,
                   "plugin_share": float(share0),
                   "other_channels": "ORIGINAL_PLUGIN_POINTS"},
        METHOD_B: dict(_percentile_summary(cond_common),
                       other_channels="ORIGINAL_PLUGIN_POINTS"),
        METHOD_C: dict(_percentile_summary(joint_common),
                       other_channels="RECOMPUTED_JOINTLY"),
    }
    audit = {
        "n_bootstrap": int(share_arr.size),
        "n_common_finite": int(common.sum()),
        "n_excluded_from_matched_contrast": int((~common).sum()),
        "common_finite_mask_sha256": _mask_hash(common),
        "mask_semantics": "INTERSECTION_FINITE_A_B_C_PLATFORM_INDEPENDENT_PACKBITS_BIG",
    }
    return entry, audit


def _source_report(sampled: dict, partition: str) -> dict:
    if partition == "registered":
        return sampled["source"]["registered_partition"]
    return sampled["source"][f"alternative_partition_{partition}"]


def matched_interval_bootstrap(config: NativeConfig, operating_logs: list[dict],
                               execution_logs: list[dict], sampled: dict, *,
                               n_bootstrap: int = 200, rng) -> dict:
    """Compute A/B/C on common finite replicates, deterministically given rng.

    ``sampled`` supplies the original plug-in share and fixed channel points.
    The caller must bind it to the same immutable logs (the analyses verify
    their hashes).  No exact-truth input enters this computation.
    """
    horizon = config.horizon
    n = len(operating_logs)
    if n < 2:
        raise ValueError("matched bootstrap requires at least two operating trajectories")
    if n_bootstrap < 2:
        raise ValueError("matched bootstrap requires at least two resamples")
    channels = sampled["channels"]
    fixed = (channels["a_goal_structural"], channels["a_exec_open_loop"],
             channels["a_epi"], channels["a_ref"])
    if any(value is None for value in fixed) or channels["a_ref"] is None:
        raise ValueError("matched A/B contrast requires defined original plug-in channels")
    viability0 = float(sampled["viability_state"])
    weights = config.weights
    normalizer = 2 * math.log(2.0)
    goal = goal_report()["structural_point"]
    if abs(float(fixed[0]) - float(goal)) > 1e-12:
        raise ValueError("structural goal point drift between sampled and registered reports")

    stats = _operating_sufficient_stats(operating_logs, horizon)
    seq_indices, terminals = _execution_sufficient_stats(execution_logs)
    n_seq = len(seq_indices)
    shape, size = stats["shape"], stats["size"]
    partitions = ("registered", ALTERNATIVE_PARTITION_NAME)
    shares = {p: {c: [] for c, _ in CONVENTIONS} for p in partitions}
    conditional = {p: {c: [] for c, _ in CONVENTIONS} for p in partitions}
    joint = {p: {c: [] for c, _ in CONVENTIONS} for p in partitions}
    # Hash exact resampling INPUT draws (not floating-point analysis outputs).
    draw_hash = hashlib.sha256()

    # Keep the operation/RNG order identical to R21 joint_composite_bootstrap.
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        draw_hash.update(np.asarray(idx, dtype="<i8").tobytes(order="C"))
        reg_counts = np.bincount(stats["reg_idx"][idx], minlength=size).reshape(shape)
        alt_counts = np.bincount(stats["alt_idx"][idx], minlength=size).reshape(shape)
        reg_report = _share_report(reg_counts / reg_counts.sum(), horizon)
        alt_report = _share_report(alt_counts / alt_counts.sum(), horizon)
        epi_b = float(stats["epi_hits"][idx].mean())
        fid_joint = _fidelity_from_joint(stats["fid_contrib"][idx].sum(axis=0))
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
        a_ref_b = (None if degraded else fid_joint * consistency_b * lambda_b)
        viability_b = float(stats["min_z"][idx].min())
        kernels = np.zeros((n_seq, 2))
        for row, sequence in enumerate(seq_indices):
            term = terminals[sequence]
            draw_idx = rng.integers(0, len(term), size=len(term))
            draw_hash.update(np.asarray([sequence, len(term)], dtype="<i8").tobytes(order="C"))
            draw_hash.update(np.asarray(draw_idx, dtype="<i8").tobytes(order="C"))
            draw = term[draw_idx]
            p1 = float(draw.mean())
            kernels[row, 0] = 1.0 - p1
            kernels[row, 1] = p1
        capacity_b, _q = channel_capacity(kernels)
        a_exec_b = min(1.0, float(capacity_b) / normalizer)
        rest_joint = (goal, a_exec_b, epi_b,
                      a_ref_b if a_ref_b is not None else 1.0)
        for partition, report in (("registered", reg_report),
                                  (ALTERNATIVE_PARTITION_NAME, alt_report)):
            for convention, key in CONVENTIONS:
                share_b = report[key]
                shares[partition][convention].append(
                    share_b if share_b is not None else float("nan"))
                cond_value = (None if share_b is None else float(composite_A(
                    viability0, (share_b,) + tuple(float(v) for v in fixed),
                    weights, sigma=1.0)))
                joint_value = (None if (share_b is None or a_ref_b is None)
                               else float(composite_A(
                                   viability_b, (share_b,) + rest_joint,
                                   weights, sigma=1.0)))
                conditional[partition][convention].append(
                    cond_value if cond_value is not None else float("nan"))
                joint[partition][convention].append(
                    joint_value if joint_value is not None else float("nan"))

    intervals = {p: {} for p in partitions}
    replicate_audit = {p: {} for p in partitions}
    for partition in partitions:
        source = _source_report(sampled, partition)
        for convention, key in CONVENTIONS:
            share_arr = np.asarray(shares[partition][convention], dtype=float)
            cond_arr = np.asarray(conditional[partition][convention], dtype=float)
            joint_arr = np.asarray(joint[partition][convention], dtype=float)
            share0 = source[key]
            if share0 is None:
                raise ValueError("matched A/B contrast requires defined original plug-in share")

            def fixed_composite(share):
                return float(composite_A(viability0, (float(share),) +
                                         tuple(float(v) for v in fixed),
                                         weights, sigma=1.0))

            entry, audit = summarize_matched_replicates(
                float(share0), share_arr, cond_arr, joint_arr, fixed_composite)
            intervals[partition][convention] = entry
            replicate_audit[partition][convention] = audit
    return {
        "artifact_version": "R22-matched-interval-contrast-v1",
        "method_labels": dict(METHOD_LABELS),
        "methods": list(METHODS),
        "resampling": {
            "unit": "trajectory",
            "stream": "R21_JOINT_STREAM_IDENTICAL_OPERATION_AND_RNG_ORDER",
            "operating": "same_joint_batch_for_all_operating_channels",
            "execution": "stratified_by_precommitted_sequence_independent",
            "common_finite_replicates_for_A_B_C": True,
        },
        "resampling_audit": {
            "draws_sha256": draw_hash.hexdigest(),
            "encoding": "LITTLE_ENDIAN_INT64_EXACT_RESAMPLING_INPUT_DRAWS",
            "not_analysis_output_float_hash": True,
            "includes": ["operating trajectory indices",
                         "execution sequence ids and exact resampling indices"],
        },
        "policy": dict(CONTRAST_POLICY),
        "intervals": intervals,
        "replicate_audit": replicate_audit,
    }


def method_coverage(interval_entry: dict, exact_anchor: float) -> dict:
    """Oracle-evaluation coverage flags; never inputs to interval construction."""
    out = {}
    for method in METHODS:
        bounds = interval_entry[method]["bounds"]
        out[method] = bool(bounds[0] <= exact_anchor <= bounds[1])
    return out


def coverage_transitions(rows: list[dict], first: str, second: str) -> dict:
    """Full 2x2 coverage-pattern counts for a descriptive method contrast."""
    if first not in METHODS or second not in METHODS or first == second:
        raise ValueError("contrast methods must be distinct registered A/B/C methods")
    return {
        "miss_miss": sum(not row["method_coverage"][first]
                         and not row["method_coverage"][second] for row in rows),
        "miss_cover": sum(not row["method_coverage"][first]
                          and row["method_coverage"][second] for row in rows),
        "cover_miss": sum(row["method_coverage"][first]
                          and not row["method_coverage"][second] for row in rows),
        "cover_cover": sum(row["method_coverage"][first]
                           and row["method_coverage"][second] for row in rows),
    }
