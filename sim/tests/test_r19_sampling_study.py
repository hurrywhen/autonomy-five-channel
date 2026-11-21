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

    def test_saved_full_study_replays_and_reports_undercoverage(self):
        root = Path(__file__).resolve().parents[1]
        saved = json.loads((root / "analysis_r19_sampling_study.json").read_text(
            encoding="utf-8"))
        validate_result(saved)
        self.assertEqual(tuple(saved["seeds"]), STUDY_SEEDS)
        aggregates = saved["aggregates"]
        # The central honest finding: percentile intervals under-cover the
        # exact truth because plug-in bias dominates near zero shares.
        self.assertLess(aggregates["NRI"]["coverage_plugin_95"], 0.5)
        self.assertGreater(aggregates["NRI"]["mean_bias_plugin"], 0.05)
        self.assertGreater(aggregates["NRI"]["max_abs_error_plugin"], 0.05)
        # Bias correction reduces near-zero NRI RMSE on average (not a
        # consistency guarantee).
        self.assertLess(aggregates["NRI"]["rmse_bias_corrected"],
                        aggregates["NRI"]["rmse_plugin"])
        self.assertEqual(saved["status"],
                         "INTERNAL_FINITE_SAMPLE_STUDY_NOT_EXTERNAL_NOT_POWER")

    def test_duplicate_seeds_fail_closed(self):
        result = compute(n_samples=512, n_bootstrap=10,
                         seeds=(20261122, 20261122))
        with self.assertRaises(ValueError):
            validate_result(result)


if __name__ == "__main__":
    unittest.main()
