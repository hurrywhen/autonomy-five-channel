"""R19 joint-log audit guards: corrected state_autonomy_RNI, immutable-input
evidence binding, sampled negative controls, detection-limit semantics, and
degradation-aware reflection estimation from synthetic thin/zero-entropy logs."""
import json
import math
import os
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim.native_benchmark import NativeConfig  # noqa: E402
from autonomy_sim.native_joint_audit import (generate_execution_logs,  # noqa: E402
                                             generate_operating_logs)
from autonomy_sim.r19_joint_audit import (MIN_REFLECTION_EVENTS,  # noqa: E402
                                          NRI_SHARE_DETECTION_LIMIT,
                                          estimate_from_logs_r19, run_joint_audit_r19)
from autonomy_sim.r19_guards import validate_r19_certificate  # noqa: E402
from analysis_r19_joint_audit import compute, validate_result  # noqa: E402


def _synthetic_operating_logs(n_traj, horizon, *, theta_mode="varied",
                              with_updates=True, surgery=0):
    """Hand-crafted logs to exercise the estimator's degradation rules."""
    rng = np.random.default_rng(5)
    logs = []
    for k in range(n_traj):
        steps, events = [], []
        for t in range(horizon):
            theta = 0 if theta_mode == "constant" else int(rng.integers(0, 2))
            report = theta ^ int(rng.random() < 0.1)
            steps.append({"t": t, "E": 0, "O": 0, "B": 0, "N": theta, "R": 0,
                          "I": 0, "A": theta, "G": 1, "M": report,
                          "Z": 0.8, "D": 0.7})
            if with_updates:
                events.append({"type": "NORMATIVE_UPDATE", "t": t, "theta": theta,
                               "self_report": report, "endorsed": True})
        u = int(rng.integers(0, 2))
        events.append({"type": "SURGERY_CONTEXT", "U": u, "Y": u ^ surgery,
                       "J": surgery})
        logs.append({"stream": "OPERATING_JOINT_LOG", "trajectory_id": k,
                     "exogenous": {}, "steps": steps, "events": events})
    return logs


class R19JointAuditFields(unittest.TestCase):
    def test_state_autonomy_rni_equals_certificate_composite_not_gate(self):
        # THE R19 bug-fix regression: R18 returned the resource gate (0.8)
        # because it passed a unit channel composite to state_defense_split.
        result = compute(n_samples=2048, seed=7, n_bootstrap=20)
        sampled = result["sampled"]
        cert = result["baseline_certificate"]
        self.assertIsNotNone(sampled["state_autonomy_RNI"])
        self.assertAlmostEqual(sampled["state_autonomy_RNI"], cert["state_autonomy"],
                               places=12)
        self.assertNotAlmostEqual(sampled["state_autonomy_RNI"],
                                  sampled["viability_state"], places=6)
        # Independent recomputation from the five channels.
        from autonomy_sim.aggregate import composite_A
        channels = sampled["channels"]
        independent = composite_A(
            sampled["viability_state"],
            (channels["a_org_RNI"], channels["a_goal_structural"],
             channels["a_exec_open_loop"], channels["a_epi"], channels["a_ref"]),
            result["config"]["weights"], sigma=1.0)
        self.assertAlmostEqual(sampled["state_autonomy_RNI"], independent, places=12)

    def test_evidence_binding_is_immutable_inputs_only(self):
        result = compute(n_samples=1024, seed=9, n_bootstrap=10)
        binding = result["evidence_binding"]
        self.assertEqual(binding["policy"], "IMMUTABLE_RAW_INPUTS_ONLY_NOT_ANALYSIS_OUTPUTS")
        payload = binding["payload"]
        self.assertEqual(set(payload), {"log_hashes", "config", "seed",
                                        "n_samples_per_stream", "n_bootstrap",
                                        "log_schema"})
        self.assertEqual(result["baseline_certificate"]["evidence_hash"],
                         binding["evidence_sha256"])
        # Changing an analysis output must NOT change the evidence hash.
        mutated = json.loads(json.dumps(result))
        mutated["sampled"]["channels"]["a_epi"] = 0.5
        self.assertEqual(mutated["evidence_binding"]["evidence_sha256"],
                         binding["evidence_sha256"])

    def test_canonical_execution_metadata_and_precision(self):
        result = compute(n_samples=1024, seed=11, n_bootstrap=10)
        score = result["sampled"]["execution_open_loop"]["score"]
        self.assertIsNotNone(score["input_canonicalization"])
        self.assertEqual(score["input_canonicalization"]["replay_tolerance"], 1e-6)
        q = score["input_distribution_over_allowed"]
        self.assertAlmostEqual(sum(q), 1.0, places=12)

    def test_sampled_surgery_arm_annihilates_all_conventions(self):
        result = compute(n_samples=1024, seed=13, n_bootstrap=10)
        surgery = result["surgery_arm_sampled"]
        self.assertEqual(surgery["reflection"]["Lambda"], 0.0)
        self.assertEqual(surgery["channels"]["a_ref"], 0.0)
        self.assertEqual(surgery["state_autonomy_RNI"], 0.0)
        cert = result["surgery_certificate_sampled"]
        self.assertEqual(validate_r19_certificate(cert), [])
        self.assertEqual(cert["state_autonomy"], 0.0)
        self.assertEqual(cert["sensitivity_flags"], [])
        self.assertEqual(cert["historical_formation_profile"]["formation_status"],
                         "REGISTERED_SURGERY")
        for partition in cert["attribution_sensitivity"]["composite_by_convention"].values():
            for value in partition.values():
                self.assertEqual(value, 0.0)

    def test_sampled_decoupled_arm_zero_within_sampling_precision(self):
        result = compute(n_samples=1024, seed=15, n_bootstrap=10)
        decoupled = result["action_decoupled_negative_control_sampled"]
        self.assertLessEqual(decoupled["channels"]["a_exec_open_loop"], 1e-3)
        self.assertEqual(decoupled["execution_open_loop"]["score"]
                         ["input_distribution_over_allowed"], [0.25] * 4)
        cert = result["decoupled_certificate_sampled"]
        self.assertEqual(validate_r19_certificate(cert), [])
        self.assertLessEqual(cert["channel_profile"]["a_exec"]["value"], 1e-3)
        # The exact arm remains exactly zero.
        self.assertEqual(result["action_decoupled_negative_control_exact"]
                         ["execution_open_loop"]["state_averaged_a_exec"], 0.0)

    def test_near_zero_detection_limit_semantics(self):
        """R19 ORACLE-ASSISTED fixture rule (compatibility snapshot).  R20
        supersedes it with a data-driven in-certificate rule; this test
        preserves the frozen R19 behavior of the read-only artifact."""
        result = compute(n_samples=2048, seed=17, n_bootstrap=20)
        detection = result["near_zero_detection"]
        self.assertTrue(detection["NRI"]["below_detection_limit"])
        self.assertEqual(detection["NRI"]["reported_semantics"],
                         "INTERVAL_BELOW_DETECTION_LIMIT")
        interval = detection["NRI"]["reported_composite_interval"]
        self.assertEqual(interval[0], 0.0)
        self.assertGreater(interval[1], 0.0)
        self.assertFalse(detection["RNI"]["below_detection_limit"])
        self.assertEqual(detection["RNI"]["reported_semantics"],
                         "POINT_WITH_SENSITIVITY_QUALIFICATION")
        self.assertLess(detection["NRI"]["exact_share"], NRI_SHARE_DETECTION_LIMIT)

    def test_full_default_run_passes_all_anchors(self):
        result = compute()  # default 8192 / seed 20261122 / 100 bootstrap
        validate_result(result)
        exact_cert = result["baseline_certificate_exact"]
        composites = exact_cert["attribution_sensitivity"]["composite_by_convention"]["registered"]
        self.assertAlmostEqual(composites["RNI"], 0.4608565248033332, places=9)
        self.assertAlmostEqual(composites["NRI"], 0.0003907988672884718, places=9)
        self.assertAlmostEqual(composites["order_average"], 0.4011989072662361, places=9)
        self.assertEqual(result["logs"]["operating_trajectories"], 8192)
        self.assertEqual(result["logs"]["execution_trajectories"], 4 * 8192)

    def test_saved_artifact_replays_and_keeps_evidence_boundaries(self):
        root = Path(__file__).resolve().parents[1]
        saved = json.loads((root / "analysis_r19_joint_audit.json").read_text(
            encoding="utf-8"))
        validate_result(saved)
        self.assertEqual(saved["status"], "INTERNAL_JOINT_LOG_CONCEPT_VALIDATION_NOT_EXTERNAL")
        self.assertFalse(saved["scope"]["external_construct_validation"])
        self.assertIn("R18", saved["scope"]["supersedes"])
        self.assertEqual(saved["baseline_certificate"]["sensitivity_flags"],
                         ["ORDER_SENSITIVE", "MODEL_SENSITIVE"])
        self.assertIn("POST_HOC_FROZEN",
                      saved["sensitivity_thresholds"]["provenance"])


class R19ReflectionDegradationEstimator(unittest.TestCase):
    def _execution_logs(self, n=16):
        rng = np.random.default_rng(21)
        return generate_execution_logs(NativeConfig(), n_samples=n, rng=rng)

    def test_thin_log_degrades_consistency_to_interval(self):
        n_traj = 4  # 12 update events < MIN_REFLECTION_EVENTS
        logs = _synthetic_operating_logs(n_traj, 3)
        estimate = estimate_from_logs_r19(NativeConfig(), logs, self._execution_logs(),
                                          n_bootstrap=0, rng=np.random.default_rng(22))
        reflection = estimate["reflection"]
        self.assertEqual(reflection["event_counts"]["normative_update_events"], 12)
        self.assertLess(12, MIN_REFLECTION_EVENTS)
        self.assertEqual(reflection["degradation_reason"], "THIN_LOG")
        self.assertIsNone(reflection["endorsement_consistency"])
        self.assertIsNone(reflection["A_ref"])
        upper = reflection["fidelity"] * reflection["Lambda"]
        self.assertAlmostEqual(reflection["A_ref_interval"][1], upper, places=12)
        self.assertEqual(reflection["A_ref_interval"][0], 0.0)
        self.assertIsNone(estimate["state_autonomy_RNI"])

    def test_zero_entropy_ensemble_degrades_fidelity_to_interval(self):
        logs = _synthetic_operating_logs(40, 3, theta_mode="constant")
        estimate = estimate_from_logs_r19(NativeConfig(), logs, self._execution_logs(),
                                          n_bootstrap=0, rng=np.random.default_rng(23))
        reflection = estimate["reflection"]
        self.assertEqual(reflection["degradation_reason"], "ZERO_ENTROPY_ENSEMBLE")
        self.assertIsNone(reflection["fidelity"])
        self.assertEqual(reflection["endorsement_consistency"], 1.0)
        self.assertEqual(reflection["Lambda"], 1.0)
        self.assertAlmostEqual(reflection["A_ref_interval"][1], 1.0, places=12)
        self.assertIsNone(reflection["A_ref"])

    def test_no_update_carriers_degrades_to_no_log_carriers(self):
        logs = _synthetic_operating_logs(40, 3, with_updates=False)
        estimate = estimate_from_logs_r19(NativeConfig(), logs, self._execution_logs(),
                                          n_bootstrap=0, rng=np.random.default_rng(24))
        reflection = estimate["reflection"]
        self.assertEqual(reflection["degradation_reason"], "NO_LOG_CARRIERS")
        self.assertIsNone(reflection["fidelity"])
        self.assertIsNone(reflection["endorsement_consistency"])
        self.assertEqual(reflection["Lambda"], 1.0)
        self.assertAlmostEqual(reflection["A_ref_interval"][1], 1.0, places=12)

    def test_well_logged_baseline_has_no_degradation(self):
        rng = np.random.default_rng(25)
        logs = generate_operating_logs(NativeConfig(), n_trajectories=256, rng=rng)
        estimate = estimate_from_logs_r19(NativeConfig(), logs, self._execution_logs(),
                                          n_bootstrap=0, rng=np.random.default_rng(26))
        reflection = estimate["reflection"]
        self.assertIsNone(reflection["degradation_reason"])
        self.assertIsNotNone(reflection["A_ref"])
        self.assertIsNone(reflection["A_ref_interval"])
        self.assertIsNotNone(estimate["state_autonomy_RNI"])


if __name__ == "__main__":
    unittest.main()
