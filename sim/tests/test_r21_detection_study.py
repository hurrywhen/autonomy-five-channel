"""R21 detection study guards: predeclared grid structure, separated coverage
semantics (envelope containment vs share-conditional vs joint), oracle/deployable
separation, analytic anchors, and frozen-artifact snapshot regression.  Empirical
rates are descriptive findings, never universal pass conditions."""
import copy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim.r20_detection import DETECTION_RULE_VERSION  # noqa: E402
from autonomy_sim.r21_guards import SHARE_CONDITIONAL_KIND  # noqa: E402
from analysis_r21_detection_study import (COVERAGE_SEMANTICS,  # noqa: E402
                                          PREDECLARED_GRID, compute, validate_result)


class R21DetectionStudy(unittest.TestCase):
    def test_small_grid_runs_and_validates_structurally(self):
        grid = copy.deepcopy(PREDECLARED_GRID)
        grid["seeds"] = [20261122, 20261123]
        grid["n_samples_per_stream"] = [512]
        grid["n_bootstrap"] = 15
        grid["n_joint_bootstrap"] = 15
        result = compute(grid=grid)
        validate_result(result)
        self.assertEqual(len(result["cells"]), 2)
        self.assertTrue(result["scope"]["oracle_used_for_evaluation_only"])
        self.assertFalse(result["scope"]["oracle_used_in_decision"])
        self.assertFalse(result["scope"]["external_construct_validation"])
        self.assertFalse(result["scope"]["power_analysis"])
        self.assertEqual(result["coverage_semantics"], COVERAGE_SEMANTICS)
        for cell in result["cells"]:
            for row in cell["conventions"].values():
                self.assertIn(row["convention_status"],
                              {"DATA_BELOW_LIMIT", "DATA_ABOVE_LIMIT", "INDETERMINATE_NEAR_ZERO"})
                kind = row["reported_interval_kind"]
                if kind == "LOGICAL_ENVELOPE":
                    self.assertIsNotNone(row["logical_envelope_anchor_containment"])
                    self.assertIsNone(row["share_conditional_sampling_covers_exact"])
                else:
                    self.assertEqual(kind, SHARE_CONDITIONAL_KIND)
                    self.assertIsNotNone(row["share_conditional_sampling_covers_exact"])
                    self.assertIsNone(row["logical_envelope_anchor_containment"])
                self.assertIsNotNone(row["joint_sampling_covers_exact"])

    def test_predeclared_grid_is_frozen_and_complete(self):
        self.assertEqual(PREDECLARED_GRID["seeds"], list(range(20261122, 20261138)))
        self.assertEqual(PREDECLARED_GRID["n_samples_per_stream"], [2048, 8192])
        self.assertEqual(PREDECLARED_GRID["n_bootstrap"], 200)
        self.assertEqual(PREDECLARED_GRID["n_joint_bootstrap"], 200)
        self.assertEqual(PREDECLARED_GRID["decision_rule"], DETECTION_RULE_VERSION)
        self.assertTrue(PREDECLARED_GRID["declared_before_outcomes"])

    def test_coverage_semantics_governance(self):
        self.assertTrue(COVERAGE_SEMANTICS["no_combined_or_cross_kind_coverage_comparison"])
        self.assertEqual(COVERAGE_SEMANTICS["logical_envelope_anchor_containment"],
                         "CONTAINMENT_DIAGNOSTIC_NOT_STATISTICAL_COVERAGE")
        self.assertIn("directed_information_plugin_bias", COVERAGE_SEMANTICS["undercoverage_causes"])
        self.assertIn("share_conditional_design_other_channels_fixed",
                      COVERAGE_SEMANTICS["undercoverage_causes"])

    def test_saved_full_study_structure_and_snapshot(self):
        root = Path(__file__).resolve().parents[1]
        saved = json.loads((root / "analysis_r21_detection_study.json").read_text(
            encoding="utf-8"))
        validate_result(saved)
        self.assertEqual(saved["predeclared_grid"], PREDECLARED_GRID)
        self.assertEqual(len(saved["cells"]), 32)
        self.assertEqual(saved["status"], "INTERNAL_FINITE_SAMPLE_STUDY_NOT_EXTERNAL_NOT_POWER")
        self.assertEqual(saved["coverage_semantics"], COVERAGE_SEMANTICS)
        # SNAPSHOT REGRESSION on the frozen artifact (descriptive findings of THIS
        # grid, not universal invariants).  Share-conditional results reproduce R20
        # (same estimator/rule/grid); the joint diagnostic is supplementary.
        for n_key in ("2048", "8192"):
            agg = saved["aggregates"][n_key]
            # NRI: always INDETERMINATE, never misclassified, envelope contains anchor.
            self.assertEqual(agg["NRI"]["indeterminate_rate"], 1.0)
            self.assertEqual(agg["NRI"]["false_below_rate"], 0.0)
            self.assertEqual(agg["NRI"]["false_above_rate"], 0.0)
            self.assertEqual(agg["NRI"]["reported_interval_kind"], "LOGICAL_ENVELOPE")
            self.assertEqual(agg["NRI"]["logical_envelope_anchor_containment_rate"], 1.0)
            self.assertIsNone(agg["NRI"]["share_conditional_sampling_coverage_rate"])
            # RNI / order_average: always ABOVE, share-conditional coverage reproduces R20.
            self.assertEqual(agg["RNI"]["status_rates"]["DATA_ABOVE_LIMIT"], 1.0)
            self.assertEqual(agg["RNI"]["reported_interval_kind"], SHARE_CONDITIONAL_KIND)
            self.assertIsNone(agg["RNI"]["logical_envelope_anchor_containment_rate"])
            self.assertEqual(agg["order_average"]["status_rates"]["DATA_ABOVE_LIMIT"], 1.0)
        self.assertEqual(saved["aggregates"]["2048"]["RNI"]["share_conditional_sampling_coverage_rate"], 0.25)
        self.assertEqual(saved["aggregates"]["8192"]["RNI"]["share_conditional_sampling_coverage_rate"], 0.0)
        self.assertEqual(saved["aggregates"]["2048"]["order_average"]["share_conditional_sampling_coverage_rate"], 0.5)
        self.assertEqual(saved["aggregates"]["8192"]["order_average"]["share_conditional_sampling_coverage_rate"], 0.125)
        # Joint diagnostic (SNAPSHOT, descriptive): it improves share-conditional
        # coverage for above-limit conventions (conditional-design attributable),
        # but not for NRI (plug-in bias dominates; joint does not remove bias).
        self.assertEqual(saved["aggregates"]["2048"]["RNI"]["joint_sampling_coverage_rate"], 1.0)
        self.assertEqual(saved["aggregates"]["8192"]["RNI"]["joint_sampling_coverage_rate"], 0.875)
        self.assertEqual(saved["aggregates"]["2048"]["order_average"]["joint_sampling_coverage_rate"], 0.9375)
        self.assertEqual(saved["aggregates"]["8192"]["order_average"]["joint_sampling_coverage_rate"], 0.8125)
        self.assertEqual(saved["aggregates"]["2048"]["NRI"]["joint_sampling_coverage_rate"], 0.0)
        self.assertEqual(saved["aggregates"]["8192"]["NRI"]["joint_sampling_coverage_rate"], 0.0)
        self.assertEqual(saved["aggregates"]["8192"]["RNI"]["undercoverage_attribution"]
                         ["share_conditional_miss_joint_cover_count"], 14)
        self.assertEqual(saved["aggregates"]["8192"]["RNI"]["undercoverage_attribution"]
                         ["both_miss_count"], 2)
        self.assertEqual(saved["aggregates"]["8192"]["order_average"]["undercoverage_attribution"]
                         ["share_conditional_miss_joint_cover_count"], 11)

    def test_duplicate_seeds_fail_closed(self):
        grid = copy.deepcopy(PREDECLARED_GRID)
        grid["seeds"] = [20261122, 20261122]
        grid["n_samples_per_stream"] = [512]
        grid["n_bootstrap"] = 5
        grid["n_joint_bootstrap"] = 5
        result = compute(grid=grid)
        with self.assertRaises(ValueError):
            validate_result(result)

    def test_oracle_in_decision_flag_fails_closed(self):
        grid = copy.deepcopy(PREDECLARED_GRID)
        grid["seeds"] = [20261122]
        grid["n_samples_per_stream"] = [512]
        grid["n_bootstrap"] = 5
        grid["n_joint_bootstrap"] = 5
        result = compute(grid=grid)
        result["scope"]["oracle_used_in_decision"] = True
        with self.assertRaises(ValueError):
            validate_result(result)


if __name__ == "__main__":
    unittest.main()