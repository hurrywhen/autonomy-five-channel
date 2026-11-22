"""R20 native joint-log audit (internal concept validation).

Supersedes the R19 joint audit (read-only, retained).  The estimator itself
is the frozen R19 trajectory-block estimator (``estimate_from_logs_r19``);
R20 changes the REPORTING and CERTIFICATION layer:

1. **Data-driven near-zero detection.**  Every attribution convention is
   classified by the declared R20 rule (plug-in share + bootstrap percentile
   interval -> basic bias-corrected interval -> three-state classification
   against the inherited post hoc frozen detection limit).  The exact truth
   is attached ONLY as an explicitly labeled oracle evaluation for the
   validation fixture; it never enters the decision.
2. **Detection inside the formal certificate.**  The R20 certificate carries
   per-convention ``convention_status``, ``share_interval``,
   ``composite_interval`` (with declared kinds), detection limit/provenance,
   and diagnostic plug-in outputs.  The sampled baseline certificate is
   INTERVAL-valued: no point export, and the overall composite range is the
   hull of the reported convention composite intervals.
3. **Real interval propagation.**  Share intervals are the actual basic
   bias-corrected bootstrap intervals, not degenerate [s,s] points.
   Logical envelopes (detection-limited reporting) are explicitly marked
   non-statistical.
4. **Corrected field semantics.**  ``diagnostic_state_autonomy_RNI_plugin``
   is the actual five-channel plug-in composite (the R18 resource-gate bug
   was fixed in R19); it is labeled DIAGNOSTIC because the formal sampled
   certificate exports an interval, not this point.

Evidence binding is unchanged from R19: immutable raw inputs only (log
SHA-256 digests + config), never optimizer coordinates or plug-in outputs.
This is internal joint-log concept validation, not external validation.
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
                            ORACLE_RULE_LABEL, convention_detection_report)

R20_LOG_SCHEMA_VERSION = "R20_JOINT_LOG_SCHEMA_V1"
CONVENTION_KEYS = (("RNI", "normative_share_RNI"),
                   ("NRI", "normative_share_NRI"),
                   ("order_average", "normative_share_order_average"))


def _composite_fn(sampled: dict, config: NativeConfig):
    channels = sampled["channels"]
    if channels["a_ref"] is None or channels["a_org_RNI"] is None:
        return None
    rest = (channels["a_goal_structural"], channels["a_exec_open_loop"],
            channels["a_epi"], channels["a_ref"])
    viability = sampled["viability_state"]
    weights = config.weights

    def fn(share):
        return float(composite_A(viability, (share,) + rest, weights, sigma=1.0))
    return fn


def detection_reports(sampled: dict, exact: dict, config: NativeConfig) -> dict:
    """Per-partition/per-convention data-driven reports + oracle evaluation.

    The decision uses estimable inputs only; ``exact_share`` is passed solely
    to attach the labeled oracle comparison (fixture evaluation).
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
            if plugin is None or perc is None:
                out[partition_name][convention] = {
                    "convention_status": "NOT_EVALUABLE",
                    "reason": "ZERO_TOTAL_FLOW_OR_NO_BOOTSTRAP_INPUTS",
                    "detection_limit": DETECTION_LIMIT,
                    "detection_rule_version": DETECTION_RULE_VERSION,
                    "detection_provenance": DETECTION_RULE_PROVENANCE}
                continue
            out[partition_name][convention] = convention_detection_report(
                plugin_share=plugin, percentile_interval=perc,
                composite_fn=fn, exact_share=exact_report[key])
    return out


def run_joint_audit_r20(*, n_samples: int = 8192, seed: int = 20261122,
                        n_bootstrap: int = 100) -> dict:
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
                        "log_schema": R20_LOG_SCHEMA_VERSION}
    return {
        "artifact_version": "R20-native-joint-audit-v1",
        "status": "INTERNAL_JOINT_LOG_CONCEPT_VALIDATION_NOT_EXTERNAL",
        "config": config_payload,
        "seed": seed,
        "n_samples_per_stream": n_samples,
        "n_bootstrap": n_bootstrap,
        "log_schema": {"version": R20_LOG_SCHEMA_VERSION,
                       "step_fields": list(STEP_FIELDS),
                       "event_types": list(EVENT_TYPES),
                       "streams": [OPERATING_STREAM, EXECUTION_STREAM],
                       "compatible_with": [LOG_SCHEMA_VERSION, R19_LOG_SCHEMA_VERSION]},
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
                         "detection classifications"],
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
        "detection_reports": detection_reports(sampled, exact, config),
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
            "goal_mode": "registered structural white-box read plus caller-registered IRL interval",
            "operating_policy": "reactive closed-loop A_t=N_t xor R_t xor B_t",
            "generic_MaxEnt_IRL_solver": False,
            "external_construct_validation": False,
            "supersedes": ("R19 joint audit (read-only; oracle-triggered detection "
                           "outside the certificate superseded by the R20 data-driven "
                           "in-certificate rule)"),
        },
        "interpretation": ("Finite-sample implementation agreement on one registered "
                           "instance from one joint log batch; not statistical "
                           "consistency, not a power claim, and not external construct "
                           "validation. Exact-truth composites are model anchors. The "
                           "data-driven detection rule cannot confirm the near-zero NRI "
                           "share at this sample size (INDETERMINATE is the honest "
                           "outcome); diagnostic plug-in outputs are not the reported "
                           "certificate semantics."),
    }