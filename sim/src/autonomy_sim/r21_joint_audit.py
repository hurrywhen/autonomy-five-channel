"""R21 native joint-log audit (internal concept validation).

Supersedes the R20 joint audit (read-only, retained).  The estimator and the
data-driven detection RULE are unchanged from R20 (frozen R19 trajectory-block
estimator; basic bias-corrected three-state rule declared before R20 outcomes).
R21 changes the CONDITIONING DISCLOSURE and adds a joint-bootstrap diagnostic:

1. **Share-conditional composite intervals are honestly named.**  Above-limit
   composite sampling intervals propagate only the source-share basic bootstrap
   interval (other channels fixed at plugin/structural points); their kind is
   SHARE_CONDITIONAL_SAMPLING_BASIC_BOOTSTRAP with a conditioning_scope field.
   The formal certificate is produced by r21_guards (R21_CHANNEL_SCHEMA_V1).
2. **Joint trajectory bootstrap (supplementary diagnostic).**  A trajectory-block
   bootstrap recomputes ALL operating-side channels from the same resampled batch
   (within-batch covariance preserved) and the execution channel from the
   independent stream (stratified by sequence), then the composite per convention.
   This genuine joint composite sampling interval quantifies how much of the
   share-conditional under-coverage is due to the conditional design versus
   plug-in bias.  It is an ARTIFACT-LEVEL diagnostic, NOT the certificate's
   reported semantics, and it does not remove plug-in bias.
3. **Coverage semantics separated.**  Logical-envelope anchor containment is a
   containment diagnostic, never a statistical coverage rate; sampling-interval
   coverage is reported with its conditioning scope.  The two are never combined
   or compared as estimator quality (enforced in analysis_r21_detection_study).

Evidence binding is unchanged: immutable raw inputs only.  Internal joint-log
concept validation, not external validation.
"""
from __future__ import annotations

import numpy as np

from .aggregate import composite_A
from .native_benchmark import NativeConfig, exact_bundle
from .native_joint_audit import (ALTERNATIVE_PARTITION_NAME, EXECUTION_STREAM,
                                 LOG_SCHEMA_VERSION, OPERATING_STREAM, STEP_FIELDS,
                                 EVENT_TYPES, _canonical_hash)
from .r19_joint_audit import (MIN_REFLECTION_EVENTS, NRI_SHARE_DETECTION_LIMIT,
                              R19_LOG_SCHEMA_VERSION, _arm_logs,
                              estimate_from_logs_r19)
from .r20_detection import (DETECTION_LIMIT, DETECTION_LIMIT_PROVENANCE,
                            DETECTION_RULE_PROVENANCE, DETECTION_RULE_VERSION,
                            ORACLE_RULE_LABEL, basic_bootstrap_bias_corrected_interval,
                            classify_share_interval,
                            oracle_assisted_fixture_classification)
from .r20_joint_audit import R20_LOG_SCHEMA_VERSION, _composite_fn
from .r21_guards import SHARE_CONDITIONAL_KIND
from .r21_joint_bootstrap import joint_composite_bootstrap

R21_LOG_SCHEMA_VERSION = "R21_JOINT_LOG_SCHEMA_V1"
CONVENTION_KEYS = (("RNI", "normative_share_RNI"),
                   ("NRI", "normative_share_NRI"),
                   ("order_average", "normative_share_order_average"))
CONDITIONING_SCOPE_PLUGIN = "other_channels_fixed_at_plugin"


def detection_reports_r21(sampled: dict, exact: dict, config: NativeConfig) -> dict:
    """R21 artifact-level detection reports: R20 rule + conditioning disclosure.

    The decision uses estimable inputs only; exact_share attaches the labeled
    oracle comparison (fixture evaluation) and never enters the decision.
    """
    out = {}
    for partition_name, source_key, interval_key in (
            ("registered", "registered_partition", "source_bootstrap_intervals"),
            (ALTERNATIVE_PARTITION_NAME,
             f"alternative_partition_{ALTERNATIVE_PARTITION_NAME}",
             "alternative_bootstrap_intervals")):
        report = sampled["source"][source_key]
        intervals = sampled[interval_key]
        exact_report = exact["source"][source_key]
        fn = _composite_fn(sampled, config)
        out[partition_name] = {}
        for convention, key in CONVENTION_KEYS:
            plugin = report[key]
            perc = intervals[key]["percentile_95"] if intervals[key] else None
            base = {"detection_limit": DETECTION_LIMIT,
                    "detection_rule_version": DETECTION_RULE_VERSION,
                    "detection_provenance": DETECTION_RULE_PROVENANCE}
            if plugin is None or perc is None:
                out[partition_name][convention] = dict(
                    base, convention_status="NOT_EVALUABLE",
                    reason="ZERO_TOTAL_FLOW_OR_NO_BOOTSTRAP_INPUTS")
                continue
            decision = basic_bootstrap_bias_corrected_interval(plugin, perc[0], perc[1])
            status = classify_share_interval(decision)
            sampling_bounds = ([float(fn(decision[0])), float(fn(decision[1]))]
                               if fn is not None else None)
            plugin_composite = float(fn(plugin)) if fn is not None else None
            if status == "DATA_ABOVE_LIMIT":
                reported = (None if sampling_bounds is None else
                            {"bounds": sampling_bounds, "kind": SHARE_CONDITIONAL_KIND,
                             "conditioning_scope": CONDITIONING_SCOPE_PLUGIN})
            else:
                reported = (None if fn is None else
                            {"bounds": [0.0, float(fn(decision[1]))],
                             "kind": "LOGICAL_ENVELOPE",
                             "conditioning_scope": CONDITIONING_SCOPE_PLUGIN})
            rep = dict(
                base, convention_status=status,
                share_interval={"bounds": decision, "kind": "SAMPLING_BASIC_BOOTSTRAP"},
                share_bootstrap_percentile_95=[float(perc[0]), float(perc[1])],
                composite_interval=reported,
                composite_interval_sampling=(
                    None if sampling_bounds is None else
                    {"bounds": sampling_bounds, "kind": SHARE_CONDITIONAL_KIND,
                     "conditioning_scope": CONDITIONING_SCOPE_PLUGIN}),
                diagnostic_plugin_share=plugin,
                diagnostic_plugin_composite=plugin_composite)
            oracle = oracle_assisted_fixture_classification(exact_report[key])
            below = oracle["oracle_below_limit"]
            if status == "DATA_BELOW_LIMIT":
                comparison = "TRUE_BELOW" if below else "FALSE_BELOW"
            elif status == "DATA_ABOVE_LIMIT":
                comparison = "FALSE_ABOVE" if below else "TRUE_ABOVE"
            else:
                comparison = ("INDETERMINATE_TRUE_BELOW" if below
                              else "INDETERMINATE_TRUE_ABOVE")
            oracle["classification_vs_oracle"] = comparison
            rep["oracle_evaluation"] = oracle
            out[partition_name][convention] = rep
    return out


def run_joint_audit_r21(*, n_samples: int = 8192, seed: int = 20261122,
                        n_bootstrap: int = 100, n_joint_bootstrap: int = 200) -> dict:
    config = NativeConfig(surgery=0)
    rng = np.random.default_rng(seed)
    operating_logs, execution_logs = _arm_logs(config, n_samples=n_samples, rng=rng)
    sampled = estimate_from_logs_r19(config, operating_logs, execution_logs,
                                     n_bootstrap=n_bootstrap, rng=rng)
    surgery_config = NativeConfig(surgery=1)
    surgery_operating, surgery_execution = _arm_logs(surgery_config, n_samples=n_samples,
                                                     rng=rng)
    surgery_sampled = estimate_from_logs_r19(surgery_config, surgery_operating,
                                             surgery_execution,
                                             n_bootstrap=n_bootstrap, rng=rng)
    decoupled_config = NativeConfig(action_effect=False)
    decoupled_operating, decoupled_execution = _arm_logs(decoupled_config,
                                                         n_samples=n_samples, rng=rng)
    decoupled_sampled = estimate_from_logs_r19(decoupled_config, decoupled_operating,
                                               decoupled_execution,
                                               n_bootstrap=n_bootstrap, rng=rng)
    exact = exact_bundle(config)
    surgery_exact = exact_bundle(surgery_config)
    decoupled_exact = exact_bundle(decoupled_config)

    # Supplementary joint bootstrap on the main sampled arm.  A DEDICATED rng
    # (seeded deterministically from seed/n) keeps the share-conditional results
    # above byte-identical to R20 while adding the joint diagnostic.
    rng_joint = np.random.default_rng([seed, n_samples, 21])
    joint_bootstrap = joint_composite_bootstrap(
        config, operating_logs, execution_logs,
        n_bootstrap=n_joint_bootstrap, rng=rng_joint)

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
    evidence_payload = {"log_hashes": log_hashes, "config": config_payload,
                        "seed": seed, "n_samples_per_stream": n_samples,
                        "n_bootstrap": n_bootstrap,
                        "log_schema": R21_LOG_SCHEMA_VERSION}
    return {
        "artifact_version": "R21-native-joint-audit-v1",
        "status": "INTERNAL_JOINT_LOG_CONCEPT_VALIDATION_NOT_EXTERNAL",
        "config": config_payload,
        "seed": seed,
        "n_samples_per_stream": n_samples,
        "n_bootstrap": n_bootstrap,
        "n_joint_bootstrap": n_joint_bootstrap,
        "log_schema": {"version": R21_LOG_SCHEMA_VERSION,
                       "step_fields": list(STEP_FIELDS),
                       "event_types": list(EVENT_TYPES),
                       "streams": [OPERATING_STREAM, EXECUTION_STREAM],
                       "compatible_with": [LOG_SCHEMA_VERSION, R19_LOG_SCHEMA_VERSION,
                                           R20_LOG_SCHEMA_VERSION]},
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
                         "plug-in estimates", "bootstrap intervals",
                         "detection classifications", "joint bootstrap replicates"],
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
        "detection_reports": detection_reports_r21(sampled, exact, config),
        "joint_bootstrap": joint_bootstrap,
        "diagnostic_state_autonomy_RNI_plugin": sampled["state_autonomy_RNI"],
        "reporting_constants": {
            "nri_share_detection_limit": NRI_SHARE_DETECTION_LIMIT,
            "detection_rule_version": DETECTION_RULE_VERSION,
            "detection_rule_provenance": DETECTION_RULE_PROVENANCE,
            "detection_limit_provenance": DETECTION_LIMIT_PROVENANCE,
            "oracle_rule_label": ORACLE_RULE_LABEL,
            "min_reflection_events": MIN_REFLECTION_EVENTS,
            "provenance": ("DETECTION_RULE_DECLARED_BEFORE_R20_STUDY_OUTCOMES_"
                           "LIMIT_VALUE_POST_HOC_FROZEN_R19_NOT_DOMAIN_SESOI"),
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
            "detection_decision_inputs": "ESTIMABLE_ONLY_NO_EXACT_TRUTH",
            "oracle_evaluation": ORACLE_RULE_LABEL,
            "composite_interval_conditioning": "SHARE_CONDITIONAL_OTHER_CHANNELS_FIXED_AT_PLUGIN",
            "joint_bootstrap": "SUPPLEMENTARY_ARTIFACT_LEVEL_DIAGNOSTIC_NOT_REPORTED_SEMANTICS",
            "goal_mode": "registered structural white-box read plus caller-registered IRL interval",
            "operating_policy": "reactive closed-loop A_t=N_t xor R_t xor B_t",
            "generic_MaxEnt_IRL_solver": False,
            "external_construct_validation": False,
            "supersedes": ("R20 joint audit (read-only; share-conditional composite "
                           "intervals now honestly named with conditioning_scope, and a "
                           "joint trajectory bootstrap added as a supplementary diagnostic)"),
        },
        "interpretation": ("Finite-sample implementation agreement on one registered "
                           "instance from one joint log batch; not statistical "
                           "consistency, not a power claim, and not external construct "
                           "validation. Exact-truth composites are model anchors. The "
                           "data-driven detection rule cannot confirm the near-zero NRI "
                           "share at this sample size (INDETERMINATE is the honest "
                           "outcome). Above-limit composite intervals are share-conditional "
                           "(other channels fixed at points); their under-coverage reflects "
                           "both plug-in bias and the conditional design. The joint bootstrap "
                           "is a supplementary diagnostic, not the reported semantics, and "
                           "does not remove plug-in bias."),
    }