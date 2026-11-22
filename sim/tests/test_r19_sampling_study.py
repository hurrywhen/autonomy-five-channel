"""R19 multi-seed sampling study guards (internal finite-sample study)."""
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from analysis_r19_sampling_study import (STUDY_SEEDS, compute,  # noqa: E402
                                         validate_result)


class R19SamplingStudy(unittest.TestCase):
    def test_small_study_runs_and_anchors(self):
        result = compute(n_samples=1024, n_bootstrap=30,
                         seeds=(20261122, 20261123))
        validate_result(result)
        self.assertEqual(len(result["per_seed"]), 2)
        self.assertAlmostEqual(result["exact_composites"]["RNI"],
                               0.4608565248033332, places=9)
        self.assertAlmostEqual(result["exact_composites"]["NRI"],
                               0.0003907988672884718, places=9)
        self.assertTrue(result["near_zero_finding"]["below_detection_limit"])
        self.assertFalse(result["scope"]["external_construct_validation"])
        self.assertFalse(result["scope"]["power_analysis"])
        self.assertFalse(result["scope"]["statistical_consistency_claim"])

    def test_saved_full_study_snapshot_and_structure(self):
        """SNAPSHOT REGRESSION on the frozen R19 artifact (not a universal
        invariant): the specific 8-seed findings are recorded values of this
        study.  R20 review item 4 decoupled them from software acceptance:
        a future improved estimator or new legitimate seeds may legitimately
        differ; only the frozen artifact's replay is checked here."""
        root = Path(__file__).resolve().parents[1]
        saved = json.loads((root / "analysis_r19_sampling_study.json").read_text(
            encoding="utf-8"))
        validate_result(saved)
        self.assertEqual(tuple(saved["seeds"]), STUDY_SEEDS)
        aggregates = saved["aggregates"]
        # Frozen-study snapshot values (descriptive findings of THIS artifact).
        self.assertEqual(aggregates["NRI"]["coverage_plugin_95"], 0.0)
        self.assertAlmostEqual(aggregates["NRI"]["mean_bias_plugin"],
                               0.15089328249790063, places=12)
        self.assertAlmostEqual(aggregates["NRI"]["max_abs_error_plugin"],
                               0.16247681744861164, places=12)
        self.assertAlmostEqual(aggregates["NRI"]["rmse_plugin"],
                               0.1511019396847366, places=12)
        self.assertAlmostEqual(aggregates["NRI"]["rmse_bias_corrected"],
                               0.08092871692744573, places=12)
        self.assertEqual(saved["status"],
                         "INTERNAL_FINITE_SAMPLE_STUDY_NOT_EXTERNAL_NOT_POWER")

    def test_duplicate_seeds_fail_closed(self):
        result = compute(n_samples=512, n_bootstrap=10,
                         seeds=(20261122, 20261122))
        with self.assertRaises(ValueError):
            validate_result(result)


if __name__ == "__main__":
    unittest.main()
