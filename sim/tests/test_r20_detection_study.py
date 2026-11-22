"""R20 detection study guards: predeclared grid structure, oracle/deployable
separation, analytic anchors, and frozen-artifact snapshot regression.
Empirical classification/coverage rates are descriptive findings, never
universal pass conditions (R20 review item 4)."""
import copy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim.r20_detection import DETECTION_RULE_VERSION  # noqa: E402
from analysis_r20_detection_study import (PREDECLARED_GRID, compute,  # noqa: E402
                                          validate_result)


class R20DetectionStudy(unittest.TestCase):
    def test_small_grid_runs_and_validates_structurally(self):
        grid = copy.deepcopy(PREDECLARED_GRID)
        grid["seeds"] = [20261122, 20261123]
        grid["n_samples_per_stream"] = [1024]
        grid["n_bootstrap"] = 15
        result = compute(grid=grid)
        validate_result(result)
        self.assertEqual(len(result["cells"]), 2)
        self.assertTrue(result["scope"]["oracle_used_for_evaluation_only"])
        self.assertFalse(result["scope"]["oracle_used_in_decision"])
        self.assertFalse(result["scope"]["external_construct_validation"])
        self.assertFalse(result["scope"]["power_analysis"])
        self.assertFalse(result["scope"]["universal_coverage_claim"])
        for cell in result["cells"]:
            for row in cell["conventions"].values():
                self.assertIn(row["convention_status"],
                              {"DATA_BELOW_LIMIT", "DATA_ABOVE_LIMIT",
                               "INDETERMINATE_NEAR_ZERO"})

    def test_predeclared_grid_is_frozen_and_complete(self):
        self.assertEqual(PREDECLARED_GRID["seeds"], list(range(20261122, 20261138)))
        self.assertEqual(PREDECLARED_GRID["n_samples_per_stream"], [2048, 8192])
        self.assertEqual(PREDECLARED_GRID["n_bootstrap"], 200)
        self.assertEqual(PREDECLARED_GRID["decision_rule"], DETECTION_RULE_VERSION)
        self.assertTrue(PREDECLARED_GRID["declared_before_outcomes"])

    def test_saved_full_study_structure_and_snapshot(self):
        root = Path(__file__).resolve().parents[1]
        saved = json.loads((root / "analysis_r20_detection_study.json").read_text(
            encoding="utf-8"))
        validate_result(saved)
        self.assertEqual(saved["predeclared_grid"], PREDECLARED_GRID)
        self.assertEqual(len(saved["cells"]), 32)
        self.assertEqual(saved["status"],
                         "INTERNAL_FINITE_SAMPLE_STUDY_NOT_EXTERNAL_NOT_POWER")
        # SNAPSHOT REGRESSION on the frozen artifact (descriptive findings of
        # THIS grid, not universal invariants): on this fixture the data rule
        # never confirms the near-zero NRI share (all INDETERMINATE), never
        # misclassifies, and the conservative envelope covers the anchor.
        for n_key in ("2048", "8192"):
            agg = saved["aggregates"][n_key]
            self.assertEqual(agg["NRI"]["indeterminate_rate"], 1.0)
            self.assertEqual(agg["NRI"]["false_below_rate"], 0.0)
            self.assertEqual(agg["NRI"]["false_above_rate"], 0.0)
            self.assertEqual(agg["NRI"]["reported_composite_coverage_rate"], 1.0)
            self.assertEqual(agg["RNI"]["status_rates"]["DATA_ABOVE_LIMIT"], 1.0)
            self.assertEqual(agg["RNI"]["false_below_rate"], 0.0)
            self.assertEqual(agg["order_average"]["status_rates"]["DATA_ABOVE_LIMIT"], 1.0)

    def test_duplicate_seeds_fail_closed(self):
        grid = copy.deepcopy(PREDECLARED_GRID)
        grid["seeds"] = [20261122, 20261122]
        grid["n_samples_per_stream"] = [512]
        grid["n_bootstrap"] = 5
        result = compute(grid=grid)
        with self.assertRaises(ValueError):
            validate_result(result)

    def test_oracle_in_decision_flag_fails_closed(self):
        grid = copy.deepcopy(PREDECLARED_GRID)
        grid["seeds"] = [20261122]
        grid["n_samples_per_stream"] = [512]
        grid["n_bootstrap"] = 5
        result = compute(grid=grid)
        result["scope"]["oracle_used_in_decision"] = True
        with self.assertRaises(ValueError):
            validate_result(result)


if __name__ == "__main__":
    unittest.main()