"""R22 detection-study guards: frozen grid, matched A/B/C semantics, exact R21
formal-A/C reproduction, descriptive transition accounting, and fail-closed
governance.  Empirical rates are snapshots, never universal pass conditions."""
import copy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim.r20_detection import DETECTION_RULE_VERSION  # noqa: E402
from autonomy_sim.r22_interval_contrast import (CONTRAST_POLICY, METHOD_A,  # noqa: E402
                                                METHOD_B, METHOD_C, METHODS)
from analysis_r22_detection_study import (COVERAGE_SEMANTICS, PREDECLARED_GRID,  # noqa: E402
                                          compute, validate_result)


def small_grid(seeds=(20261122, 20261123), n=512, boot=15):
    grid = copy.deepcopy(PREDECLARED_GRID)
    grid["seeds"] = list(seeds)
    grid["n_samples_per_stream"] = [n]
    grid["n_bootstrap"] = boot
    grid["n_joint_bootstrap"] = boot
    grid["n_matched_bootstrap"] = boot
    return grid


class R22DetectionStudy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.small = compute(grid=small_grid())

    def test_small_grid_runs_and_validates_matched_structure(self):
        result = self.small
        validate_result(result)
        self.assertEqual(len(result["cells"]), 2)
        self.assertEqual(result["contrast_policy"], CONTRAST_POLICY)
        self.assertFalse(result["scope"]["causal_undercoverage_attribution"])
        self.assertFalse(result["scope"]["formal_bias_decomposition"])
        for cell in result["cells"]:
            for row in cell["conventions"].values():
                self.assertEqual(set(row["matched_interval_methods"]), set(METHODS))
                self.assertEqual(set(row["method_coverage"]), set(METHODS))
                self.assertEqual(set(row["method_widths"]), set(METHODS))

    def test_predeclared_grid_and_matched_design_frozen(self):
        self.assertEqual(PREDECLARED_GRID["seeds"], list(range(20261122, 20261138)))
        self.assertEqual(PREDECLARED_GRID["n_samples_per_stream"], [2048, 8192])
        self.assertEqual(PREDECLARED_GRID["n_bootstrap"], 200)
        self.assertEqual(PREDECLARED_GRID["n_matched_bootstrap"], 200)
        self.assertEqual(PREDECLARED_GRID["decision_rule"], DETECTION_RULE_VERSION)
        self.assertTrue(PREDECLARED_GRID["declared_before_outcomes"])
        self.assertTrue(PREDECLARED_GRID["matched_design_declared_before_r22_outcomes"])

    def test_descriptive_contrast_governance(self):
        self.assertTrue(CONTRAST_POLICY["not_formal_bias_decomposition"])
        self.assertIn("NOT_IDENTIFIED", CONTRAST_POLICY["A_vs_C"])
        self.assertIn("NO_SINGLE_CAUSE", CONTRAST_POLICY["both_miss"])
        self.assertTrue(COVERAGE_SEMANTICS["no_single_cause_attribution_from_coverage_patterns"])
        self.assertEqual(len(COVERAGE_SEMANTICS["potential_undercoverage_sources"]), 3)

    def test_saved_full_study_reproduces_r21_formal_a_and_c_exactly(self):
        root = Path(__file__).resolve().parents[1]
        saved = json.loads((root / "analysis_r22_detection_study.json").read_text(
            encoding="utf-8"))
        old = json.loads((root / "analysis_r21_detection_study.json").read_text(
            encoding="utf-8"))
        validate_result(saved)
        self.assertEqual(saved["predeclared_grid"]["seeds"], old["predeclared_grid"]["seeds"])
        self.assertEqual(len(saved["cells"]), 32)
        old_cells = {(cell["n_samples"], cell["seed"]): cell for cell in old["cells"]}
        for cell in saved["cells"]:
            old_cell = old_cells[(cell["n_samples"], cell["seed"])]
            for convention in ("RNI", "NRI", "order_average"):
                row = cell["conventions"][convention]
                old_row = old_cell["conventions"][convention]
                self.assertEqual(row["reported_composite_interval"],
                                 old_row["reported_composite_interval"])
                self.assertEqual(row["share_conditional_sampling_covers_exact"],
                                 old_row["share_conditional_sampling_covers_exact"])
                self.assertEqual(row["matched_interval_methods"][METHOD_C]["bounds"],
                                 old_row["joint_sampling_interval"])
                self.assertEqual(row["method_coverage"][METHOD_C],
                                 old_row["joint_sampling_covers_exact"])
        for n_key in ("2048", "8192"):
            for convention in ("RNI", "NRI", "order_average"):
                agg = saved["aggregates"][n_key][convention]
                old_agg = old["aggregates"][n_key][convention]
                self.assertEqual(agg["share_conditional_sampling_coverage_rate"],
                                 old_agg["share_conditional_sampling_coverage_rate"])
                self.assertEqual(agg["interval_method_coverage_rates"][METHOD_C],
                                 old_agg["joint_sampling_coverage_rate"])
                self.assertNotIn("undercoverage_attribution", agg)

    def test_saved_full_study_descriptive_transition_accounting(self):
        root = Path(__file__).resolve().parents[1]
        saved = json.loads((root / "analysis_r22_detection_study.json").read_text(
            encoding="utf-8"))
        for n_key in ("2048", "8192"):
            for convention in ("RNI", "NRI", "order_average"):
                agg = saved["aggregates"][n_key][convention]
                contrast = agg["descriptive_interval_method_contrast"]
                self.assertEqual(contrast["n_cells"], 16)
                for pair in ("A_vs_B", "B_vs_C", "A_vs_C"):
                    self.assertEqual(sum(contrast[pair].values()), 16)
                rates = agg["interval_method_coverage_rates"]
                # SNAPSHOT REGRESSION of the frozen descriptive grid, not a
                # universal coverage requirement.
                expected_rates = {
                    ("2048", "RNI"): (0.25, 0.3125, 1.0),
                    ("2048", "NRI"): (1.0, 0.0, 0.0),
                    ("2048", "order_average"): (0.5, 0.5, 0.9375),
                    ("8192", "RNI"): (0.0, 0.125, 0.875),
                    ("8192", "NRI"): (1.0, 0.0, 0.0),
                    ("8192", "order_average"): (0.0625, 0.0625, 0.8125),
                }[(n_key, convention)]
                self.assertEqual(tuple(rates[m] for m in METHODS), expected_rates)
                # Each pair's cover/cover plus cover/miss identifies the first
                # method's coverage; miss/cover plus cover/cover identifies the second.
                self.assertEqual(contrast["B_vs_C"]["cover_cover"]
                                 + contrast["B_vs_C"]["cover_miss"],
                                 round(16 * rates[METHOD_B]))
                self.assertEqual(contrast["B_vs_C"]["cover_cover"]
                                 + contrast["B_vs_C"]["miss_cover"],
                                 round(16 * rates[METHOD_C]))
                if convention == "NRI":
                    self.assertEqual(contrast["A_vs_B"],
                                     {"miss_miss": 0, "miss_cover": 0,
                                      "cover_miss": 16, "cover_cover": 0})
        # Matched propagation and construction patterns (descriptive snapshots).
        self.assertEqual(saved["aggregates"]["8192"]["RNI"][
            "descriptive_interval_method_contrast"]["B_vs_C"],
            {"miss_miss": 2, "miss_cover": 12, "cover_miss": 0, "cover_cover": 2})
        self.assertEqual(saved["aggregates"]["8192"]["order_average"][
            "descriptive_interval_method_contrast"]["B_vs_C"],
            {"miss_miss": 3, "miss_cover": 12, "cover_miss": 0, "cover_cover": 1})
        self.assertEqual(saved["aggregates"]["8192"]["order_average"][
            "share_conditional_sampling_coverage_rate"], 0.125)
        self.assertEqual(saved["aggregates"]["8192"]["order_average"][
            "interval_method_coverage_rates"][METHOD_A], 0.0625)

    def test_duplicate_seeds_fail_closed(self):
        result = compute(grid=small_grid(seeds=(20261122, 20261122), boot=5))
        with self.assertRaises(ValueError):
            validate_result(result)

    def test_oracle_or_causal_flags_fail_closed(self):
        result = copy.deepcopy(self.small)
        result["scope"]["oracle_used_in_decision"] = True
        with self.assertRaises(ValueError):
            validate_result(result)
        result2 = copy.deepcopy(self.small)
        result2["scope"]["causal_undercoverage_attribution"] = True
        with self.assertRaises(ValueError):
            validate_result(result2)
        result3 = copy.deepcopy(self.small)
        result3["aggregates"]["512"]["RNI"]["descriptive_interval_method_contrast"][
            "B_vs_C"]["miss_cover"] += 1
        with self.assertRaises(ValueError):
            validate_result(result3)
        # Large finite empirical errors are descriptive data, not a universal
        # software-correctness failure (R20/R22 test-decoupling discipline).
        result4 = copy.deepcopy(self.small)
        result4["cells"][0]["channel_errors"]["epistemic_abs"] = 100.0
        validate_result(result4)
        result5 = copy.deepcopy(self.small)
        result5["cells"][0]["conventions"]["RNI"]["joint_sampling_interval"] = [0.0, 1.0]
        with self.assertRaises(ValueError):
            validate_result(result5)
        result6 = copy.deepcopy(self.small)
        result6["predeclared_grid"]["n_matched_bootstrap"] = 14
        with self.assertRaises(ValueError):
            validate_result(result6)
        result7 = copy.deepcopy(self.small)
        result7["cells"][0]["conventions"]["RNI"]["matched_interval_methods"][
            METHOD_A]["plugin_share"] = 0.123
        with self.assertRaises(ValueError):
            validate_result(result7)


if __name__ == "__main__":
    unittest.main()
