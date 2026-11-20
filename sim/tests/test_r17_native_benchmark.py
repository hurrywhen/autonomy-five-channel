"""R17-native end-to-end benchmark guards (internal concept validation)."""
import json
import math
import os
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim.native_benchmark import (NativeConfig, exact_bundle,
                                           exact_source_joints, run_benchmark)
from analysis_r17_native_benchmark import compute, validate_result


class R17NativeBenchmark(unittest.TestCase):
    def test_exact_joints_are_normalized_and_alternative_partition_differs(self):
        config = NativeConfig()
        joint, alt = exact_source_joints(config)
        self.assertAlmostEqual(float(joint.sum()), 1.0, places=12)
        self.assertAlmostEqual(float(alt.sum()), 1.0, places=12)
        bundle = exact_bundle(config)
        registered = bundle["source"]["registered_partition"]
        alternative = bundle["source"]["alternative_partition_R_as_normative_memory"]
        self.assertNotAlmostEqual(registered["normative_share_order_average"],
                                  alternative["normative_share_order_average"], places=6)
        self.assertNotAlmostEqual(registered["normative_share_NRI"],
                                  alternative["normative_share_NRI"], places=6)

    def test_exact_anchors_and_open_loop_execution_in_same_environment(self):
        bundle = exact_bundle(NativeConfig())
        p = bundle["config"]["p_obs"]
        expected_exec = (math.log(2.0) + p * math.log(p) + (1 - p) * math.log(1 - p)) / (2 * math.log(2.0))
        self.assertAlmostEqual(bundle["channels"]["a_epi"], 1 - p, places=12)
        self.assertAlmostEqual(bundle["channels"]["a_goal_structural"], 0.5, places=12)
        self.assertAlmostEqual(bundle["channels"]["a_exec_open_loop"], expected_exec, places=12)
        self.assertFalse(bundle["execution_open_loop"]["uses_intermediate_observations"])
        self.assertLess(bundle["state_autonomy"], bundle["viability_state"])
        self.assertAlmostEqual(bundle["resilience_autonomy"],
                               bundle["defense_readiness"] * bundle["state_autonomy"], places=12)

    def test_surgery_and_decoupled_negative_controls(self):
        surgery = exact_bundle(NativeConfig(surgery=1))
        self.assertEqual(surgery["reflection"]["Lambda"], 0.0)
        self.assertEqual(surgery["channels"]["a_ref"], 0.0)
        self.assertEqual(surgery["historical_formation_status"], "REGISTERED_SURGERY")
        decoupled = exact_bundle(NativeConfig(action_effect=False))
        self.assertEqual(decoupled["execution_open_loop"]["state_averaged_a_exec"], 0.0)

    def test_seeded_sampling_reports_errors_intervals_and_bias_note(self):
        result = compute(n_samples=1024, seed=7)
        validate_result(result)
        sampling = result["sampling"]
        self.assertIn("source_bootstrap_intervals", sampling)
        self.assertIn("kernel_wilson_95", sampling["execution_open_loop"])
        self.assertIn("bias_note", sampling)
        for value in sampling["source_share_abs_errors"].values():
            self.assertTrue(math.isfinite(value))
        self.assertEqual(result["baseline_certificate"]["channel_schema_version"],
                         "R17_CHANNEL_SCHEMA_V1")

    def test_saved_artifact_replays_and_is_not_external_validation(self):
        root = Path(__file__).resolve().parents[1]
        saved = json.loads((root / "analysis_r17_native_benchmark.json").read_text(encoding="utf-8"))
        validate_result(saved)
        self.assertFalse(saved["baseline"]["external_construct_validation"])
        self.assertEqual(saved["status"], "INTERNAL_CONCEPT_VALIDATION_NOT_EXTERNAL")
        self.assertFalse(saved["scope"]["generic_MaxEnt_IRL_solver"])


if __name__ == "__main__":
    unittest.main()
