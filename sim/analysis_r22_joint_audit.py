#!/usr/bin/env python3
"""R22 joint-log audit with matched A/B/C interval-method diagnostics.

The R21 audit, estimator, certificate, detection rule, negative controls, and
joint-bootstrap stream are reused unchanged.  R22 adds A (basic share-
conditional), B (percentile share-conditional), and C (percentile joint) on the
same replicates, and withdraws R21's causal reading of A/C coverage patterns.

B/C is a matched-percentile channel-propagation contrast; A/B is an interval-
construction contrast.  Neither is a formal bias decomposition.  Both-miss and
A-miss/C-cover cells receive no single-cause attribution.  Exact-truth multi-seed
plug-in bias is evaluated separately in analysis_r22_detection_study.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "src"))

import numpy as np  # noqa: E402

from autonomy_sim.aggregate import composite_A  # noqa: E402
from autonomy_sim.native_benchmark import NativeConfig  # noqa: E402
from autonomy_sim.native_joint_audit import ALTERNATIVE_PARTITION_NAME, _canonical_hash  # noqa: E402
from autonomy_sim.r19_joint_audit import _arm_logs  # noqa: E402
from autonomy_sim.r20_detection import basic_bootstrap_bias_corrected_interval  # noqa: E402
from autonomy_sim.r22_interval_contrast import (  # noqa: E402
    CONTRAST_POLICY, METHOD_A, METHOD_B, METHOD_C, METHODS,
    coverage_transitions, matched_interval_bootstrap, method_coverage)
from analysis_r21_joint_audit import (REPLAY_FIELD_TOLERANCES,  # noqa: E402
                                      _independent_exact_composites,
                                      compute as compute_r21,
                                      validate_result as validate_r21)
from analysis_r22_detection_study import COVERAGE_SEMANTICS  # noqa: E402

CONVENTIONS = ("RNI", "NRI", "order_average")


def _matched_table(result: dict, matched: dict) -> dict:
    exact = _independent_exact_composites(result["exact_truth"])
    cert_reports = result["baseline_certificate"]["attribution_sensitivity"]["convention_reports"]
    table = {}
    for partition in ("registered", ALTERNATIVE_PARTITION_NAME):
        table[partition] = {}
        for convention in CONVENTIONS:
            anchor = exact[partition][convention]
            entry = matched["intervals"][partition][convention]
            coverage = method_coverage(entry, anchor)
            table[partition][convention] = {
                "exact_composite_model_anchor": anchor,
                "certificate_reported_interval":
                    cert_reports[partition][convention]["composite_interval"],
                "certificate_reported_status":
                    cert_reports[partition][convention]["convention_status"],
                "matched_interval_methods": entry,
                "method_coverage": coverage,
                "method_widths": {
                    method: entry[method]["bounds"][1] - entry[method]["bounds"][0]
                    for method in METHODS},
                "matched_replicate_audit":
                    matched["replicate_audit"][partition][convention],
                "descriptive_interval_method_contrast": {
                    "A_vs_B": coverage_transitions(
                        [{"method_coverage": coverage}], METHOD_A, METHOD_B),
                    "B_vs_C": coverage_transitions(
                        [{"method_coverage": coverage}], METHOD_B, METHOD_C),
                    "A_vs_C": coverage_transitions(
                        [{"method_coverage": coverage}], METHOD_A, METHOD_C),
                    "note": ("One-cell descriptive patterns, not causal attribution. "
                             "A/C mixes construction and conditioning; both-miss has "
                             "multiple possible sources."),
                },
            }
    return table


def compute(*, n_samples: int = 8192, seed: int = 20261122,
            n_bootstrap: int = 100, n_joint_bootstrap: int = 200) -> dict:
    result = compute_r21(n_samples=n_samples, seed=seed, n_bootstrap=n_bootstrap,
                         n_joint_bootstrap=n_joint_bootstrap)
    # Recreate the first (main-arm) immutable log batch exactly and bind it to
    # the R21 hashes before using it for the matched diagnostic.
    config = NativeConfig(surgery=0)
    operating, execution = _arm_logs(config, n_samples=n_samples,
                                     rng=np.random.default_rng(seed))
    if _canonical_hash(operating) != result["logs"]["operating_log_sha256"] or \
            _canonical_hash(execution) != result["logs"]["execution_log_sha256"]:
        raise ValueError("matched diagnostic log batch differs from the audited immutable inputs")
    matched = matched_interval_bootstrap(
        config, operating, execution, result["sampled"],
        n_bootstrap=n_joint_bootstrap,
        rng=np.random.default_rng([seed, n_samples, 21]))
    result["matched_interval_contrast"] = matched
    result["matched_convention_table"] = _matched_table(result, matched)
    result["r22_coverage_semantics"] = dict(COVERAGE_SEMANTICS)
    result["contrast_policy"] = dict(CONTRAST_POLICY)
    result["artifact_version"] = "R22-native-joint-audit-v1"
    result["evidence_binding"]["excluded"] = list(
        result["evidence_binding"]["excluded"]) + ["matched A/B/C bootstrap replicates"]
    result["conditioning_note"] = (
        "The formal certificate remains the R21 basic share-conditional interval / "
        "logical envelope. R22 does NOT identify the contribution of conditional design "
        "from an A-miss/C-cover pattern, because A and C also differ in basic versus "
        "percentile construction. On common replicates, B/C is a matched-percentile "
        "channel-propagation contrast and A/B is an interval-construction contrast. "
        "These are descriptive method contrasts, not a formal bias decomposition. "
        "Both-miss cells may reflect source-share bias, other-channel estimation error, "
        "or interval construction and receive no single-cause attribution. The joint "
        "diagnostic does not remove plug-in bias; envelope containment is not coverage.")
    result["bias_note"] = (
        "Plug-in directed-information estimates have finite-sample bias, amplified for "
        "near-zero shares by the geometric composite. That bias is assessed separately "
        "by exact-truth multi-seed simulation summaries, not inferred from both-miss "
        "coverage cells. The diagnostic plug-in NRI composite is not the certificate's "
        "reported semantics; the formal certificate reports INDETERMINATE_NEAR_ZERO and "
        "a logical envelope on the default instance. Exact-truth composites are model "
        "anchors, not finite-sample recoverability claims.")
    result["scope"].update({
        "causal_undercoverage_attribution": False,
        "formal_bias_decomposition": False,
        "matched_interval_contrast": "DESCRIPTIVE_A_B_C_ON_COMMON_REPLICATES",
        "supersedes": ("R21 joint audit (read-only; conditional-design attribution from "
                       "A/C coverage patterns withdrawn; matched A/B/C method contrasts added)"),
    })
    result["interpretation"] = (
        "Internal joint-log concept validation on one registered instance. The formal "
        "certificate and detection decisions are unchanged. A/B/C matched diagnostics "
        "separate an interval-construction contrast (A/B) from a channel-propagation "
        "contrast (B/C), but do not identify a formal bias decomposition or single cause "
        "of under-coverage. Plug-in bias is evaluated separately against exact truth. "
        "INDETERMINATE remains honest; logical-envelope containment is not statistical "
        "coverage; no external validation, power, or universal-coverage claim is made.")
    validate_r21(result)
    validate_result(result)
    return result


def validate_result(result: dict) -> None:
    """R22 structural/governance checks; empirical coverage is descriptive."""
    validate_r21(result)
    matched = result["matched_interval_contrast"]
    if result["contrast_policy"] != CONTRAST_POLICY or matched["policy"] != CONTRAST_POLICY:
        raise ValueError("matched contrast must be descriptive, not causal attribution")
    if result["r22_coverage_semantics"] != COVERAGE_SEMANTICS:
        raise ValueError("R22 coverage semantics drift")
    if not matched["resampling_audit"]["not_analysis_output_float_hash"] or \
            len(matched["resampling_audit"]["draws_sha256"]) != 64:
        raise ValueError("resampling audit must hash exact input draws, not float outputs")
    if result["scope"]["causal_undercoverage_attribution"] or \
            result["scope"]["formal_bias_decomposition"]:
        raise ValueError("R22 must not claim causal attribution or formal bias decomposition")
    sampled = result["sampled"]
    channels = sampled["channels"]
    fixed = (channels["a_goal_structural"], channels["a_exec_open_loop"],
             channels["a_epi"], channels["a_ref"])
    for partition in ("registered", ALTERNATIVE_PARTITION_NAME):
        for convention in CONVENTIONS:
            row = result["matched_convention_table"][partition][convention]
            entry = row["matched_interval_methods"]
            if entry != matched["intervals"][partition][convention] or \
                    row["matched_replicate_audit"] != \
                    matched["replicate_audit"][partition][convention]:
                raise ValueError("top-level matched diagnostic and table copy drift")
            if set(entry) != set(METHODS) or set(row["method_coverage"]) != set(METHODS):
                raise ValueError("matched table must contain exactly A/B/C")
            original_share = result["baseline_certificate"]["attribution_sensitivity"][
                "convention_reports"][partition][convention]["diagnostic_plugin_share"]
            if entry[METHOD_A]["plugin_share"] != original_share:
                raise ValueError("matched A plugin share differs from the formal certificate")
            expected_basic = basic_bootstrap_bias_corrected_interval(
                original_share, *entry[METHOD_A]["share_percentile_95"])
            if entry[METHOD_A]["share_basic_interval"] != expected_basic:
                raise ValueError("A basic interval must be recomputed from the original share")
            # Independent check that A is the existing basic-share propagation.
            basic_share = entry[METHOD_A]["share_basic_interval"]
            expected_a = [float(composite_A(
                sampled["viability_state"], (share,) + fixed,
                result["config"]["weights"], sigma=1.0)) for share in basic_share]
            if any(abs(a - b) > 1e-12 for a, b in
                   zip(expected_a, entry[METHOD_A]["bounds"])):
                raise ValueError("A must propagate the basic share interval at fixed channels")
            for method in METHODS:
                bounds = entry[method]["bounds"]
                if not 0.0 <= bounds[0] <= bounds[1] <= 1.0:
                    raise ValueError("matched interval out of bounds")
                expected_cover = bool(bounds[0] <= row["exact_composite_model_anchor"] <= bounds[1])
                if row["method_coverage"][method] is not expected_cover:
                    raise ValueError("matched coverage flag mismatch")
            # C must reproduce the retained R21 joint diagnostic exactly.
            r21_c = result["joint_bootstrap"]["composite_intervals"][partition][convention]
            if entry[METHOD_C]["bounds"] != r21_c["percentile_95"] or \
                    entry[METHOD_C]["bootstrap_mean"] != r21_c["bootstrap_mean"] or \
                    entry[METHOD_C]["bootstrap_se"] != r21_c["bootstrap_se"]:
                raise ValueError("C must reproduce the R21 joint interval on the same stream")
            audit = row["matched_replicate_audit"]
            if audit["n_common_finite"] + audit["n_excluded_from_matched_contrast"] != \
                    result["n_joint_bootstrap"]:
                raise ValueError("matched replicate accounting mismatch")
            if len(audit["common_finite_mask_sha256"]) != 64:
                raise ValueError("matched common-mask audit missing or malformed")
            for pair in ("A_vs_B", "B_vs_C", "A_vs_C"):
                if sum(row["descriptive_interval_method_contrast"][pair].values()) != 1:
                    raise ValueError("one-cell contrast counts must sum to one")
    if "quantifies the second cause" in result["conditioning_note"] or \
            "conditional-design attributable" in result["conditioning_note"]:
        raise ValueError("withdrawn R21 causal attribution language must not remain")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-samples", type=int, default=8192)
    parser.add_argument("--seed", type=int, default=20261122)
    parser.add_argument("--n-bootstrap", type=int, default=100)
    parser.add_argument("--n-joint-bootstrap", type=int, default=200)
    parser.add_argument("--out", default=str(HERE / "analysis_r22_joint_audit.json"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = compute(n_samples=args.n_samples, seed=args.seed,
                     n_bootstrap=args.n_bootstrap,
                     n_joint_bootstrap=args.n_joint_bootstrap)
    if args.check:
        saved = json.loads(Path(args.out).read_text(encoding="utf-8"))
        from analysis_r15_x5c_paired import compare_replay_json
        comparison = compare_replay_json(saved, result,
                                         field_tolerances=REPLAY_FIELD_TOLERANCES)
        if not comparison["passed"]:
            raise SystemExit("R22 joint audit check FAILED: "
                             + "; ".join(comparison["differences"][:8]))
        print("R22 joint audit check OK: unchanged R21 certificate/detection/controls, "
              "matched A/B/C descriptive contrasts, C reproduces R21, no causal "
              f"attribution; max abs float diff={comparison['max_abs_float_difference']:.3e}")
        return 0
    Path(args.out).write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                              encoding="utf-8")
    print("R22 native joint-log audit PASS (matched descriptive contrasts, not causal attribution)")
    print("[out]", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
