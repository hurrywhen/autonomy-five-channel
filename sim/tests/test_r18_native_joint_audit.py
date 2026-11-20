"""R18 native joint-log end-to-end audit guards (internal concept validation)."""
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
from autonomy_sim.native_joint_audit import (  # noqa: E402
    EXECUTION_STREAM, OPERATING_STREAM, estimate_from_logs,
    generate_execution_logs, generate_operating_logs, run_joint_audit)
from autonomy_sim.r18_guards import validate_r18_certificate  # noqa: E402
from analysis_r18_native_joint_audit import compute, validate_result  # noqa: E402


class R18NativeJointAudit(unittest.TestCase):
    def test_single_batch_provenance_and_event_carriers(self):
        config = NativeConfig()
        rng = np.random.default_rng(11)
        logs = generate_operating_logs(config, n_trajectories=64, rng=rng)
        self.assertEqual(len(logs), 64)
        for log in logs:
            self.assertEqual(log["stream"], OPERATING_STREAM)
            self.assertEqual(len(log["steps"]), config.horizon)
            updates = [e for e in log["events"] if e["type"] == "NORMATIVE_UPDATE"]
            contexts = [e for e in log["events"] if e["type"] == "SURGERY_CONTEXT"]
            self.assertEqual(len(updates), config.horizon)
            self.assertEqual(len(contexts), 1)
            for step, event in zip(log["steps"], updates):
                self.assertEqual(event["theta"], step["N"])
                self.assertEqual(event["self_report"], step["M"])
        # Regeneration with the same seed is bit-identical (deterministic provenance).
        rng2 = np.random.default_rng(11)
        logs2 = generate_operating_logs(config, n_trajectories=64, rng=rng2)
        self.assertEqual(json.dumps(logs, sort_keys=True),
                         json.dumps(logs2, sort_keys=True))

    def test_execution_stream_reads_terminal_observation_only(self):
        config = NativeConfig()
        rng = np.random.default_rng(12)
        logs = generate_execution_logs(config, n_samples=32, rng=rng)
        self.assertEqual(len(logs), 4 * 32)
        for log in logs:
            self.assertEqual(log["stream"], EXECUTION_STREAM)
            self.assertFalse(log["uses_intermediate_observations"])
            self.assertEqual(log["terminal_observation"], log["steps"][-1]["O"])
            a1, a2 = log["sequence"]
            parity = a1 ^ a2
            # E_1=0: terminal O_3 = parity xor V_3 with V_3 ~ Bernoulli(p_obs).
            self.assertIn(log["terminal_observation"], (parity, parity ^ 1))

    def test_all_operating_channels_come_from_the_same_logs(self):
        config = NativeConfig()
        rng = np.random.default_rng(13)
        operating = generate_operating_logs(config, n_trajectories=512, rng=rng)
        execution = generate_execution_logs(config, n_samples=512, rng=rng)
        estimate = estimate_from_logs(config, operating, execution,
                                      n_bootstrap=10, rng=rng)
        counts = estimate["reflection"]["event_counts"]
        self.assertEqual(counts["normative_update_events"], 512 * config.horizon)
        self.assertEqual(counts["surgery_contexts"], 512)
        self.assertEqual(estimate["reflection"]["endorsement_consistency"], 1.0)
        self.assertEqual(estimate["reflection"]["Lambda"], 1.0)
        self.assertAlmostEqual(estimate["viability_state"], 0.8, places=12)
        self.assertAlmostEqual(estimate["defense_readiness"], 0.7, places=12)
        # Epistemic accuracy from logged (B,E): truth 0.9, sampling error small.
        self.assertLess(abs(estimate["epistemic"]["sample_mean"] - 0.9), 0.05)
        self.assertFalse(estimate["execution_open_loop"]["uses_intermediate_observations"])

    def test_compute_small_run_isinternally_consistent(self):
        result = compute(n_samples=1024, seed=7, n_bootstrap=10)
        cert = result["baseline_certificate"]
        self.assertEqual(validate_r18_certificate(cert), [])
        self.assertEqual(cert["channel_schema_version"], "R18_CHANNEL_SCHEMA_V1")
        self.assertEqual(cert["sensitivity_flags"], ["ORDER_SENSITIVE", "MODEL_SENSITIVE"])
        self.assertTrue(cert["scalar_export_warning"].strip())
        self.assertEqual(result["surgery_certificate"]["state_autonomy"], 0.0)
        self.assertEqual(result["surgery_certificate"]["sensitivity_flags"], [])
        self.assertEqual(result["decoupled_certificate"]["channel_profile"]["a_exec"]["value"], 0.0)
        self.assertEqual(result["baseline_certificate_exact"]["sensitivity_flags"],
                         ["ORDER_SENSITIVE", "MODEL_SENSITIVE"])
        self.assertFalse(result["scope"]["external_construct_validation"])
        self.assertTrue(result["scope"]["single_scm"])
        self.assertTrue(result["scope"]["single_log_schema"])

    def test_full_default_run_passes_all_anchors(self):
        result = compute(n_samples=8192, seed=20261121, n_bootstrap=30)
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
        saved = json.loads((root / "analysis_r18_native_joint_audit.json").read_text(
            encoding="utf-8"))
        validate_result(saved)
        self.assertEqual(saved["status"], "INTERNAL_JOINT_LOG_CONCEPT_VALIDATION_NOT_EXTERNAL")
        self.assertFalse(saved["scope"]["generic_MaxEnt_IRL_solver"])
        self.assertFalse(saved["scope"]["external_construct_validation"])
        self.assertEqual(saved["baseline_certificate"]["sensitivity_flags"],
                         ["ORDER_SENSITIVE", "MODEL_SENSITIVE"])
        self.assertIn("R17-native", saved["scope"]["supersedes"])


if __name__ == "__main__":
    unittest.main()