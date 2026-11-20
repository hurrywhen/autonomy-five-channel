"""R17 closed-simplex geometric bookkeeping bounds and negative controls."""
import json
import math
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from analysis_r17_weight_regions import (  # noqa: E402
    compute, geometric_log_bounds, pairwise_log_damage, validate_result)


class R17WeightRegions(unittest.TestCase):
    def test_exact_bounds_are_vertex_values(self):
        result = geometric_log_bounds((0.5, 0.25, 0.75), 0.8)
        self.assertAlmostEqual(result["composite_min"], 0.2, places=14)
        self.assertAlmostEqual(result["composite_max"], 0.6, places=14)
        self.assertEqual(result["minimizing_vertex"], 1)
        self.assertEqual(result["maximizing_vertex"], 2)

    def test_pairwise_halfspace_and_classification(self):
        robust = pairwise_log_damage((0.8, 0.6), 1.0, (0.4, 0.5), 1.0)
        self.assertEqual(robust["verdict"], "POSITIVE_DAMAGE_FOR_ALL_WEIGHTS")
        self.assertAlmostEqual(robust["slopes"][0], math.log(2.0), places=14)
        self.assertIn("sum_i slopes[i]*w_i >= 0",
                      robust["nonnegative_damage_region"]["inequality"])
        dependent = pairwise_log_damage((0.8, 0.2), 1.0, (0.4, 0.6), 1.0)
        self.assertEqual(dependent["verdict"], "WEIGHT_DEPENDENT")
        self.assertLess(dependent["damage_log_min"], 0.0)
        self.assertGreater(dependent["damage_log_max"], 0.0)

    def test_zero_gate_components_and_invalid_inputs_are_not_in_log_domain(self):
        for args in [((0.8, 0.0), 1.0, (0.4, 0.5), 1.0),
                     ((0.8, 0.5), 0.0, (0.4, 0.5), 1.0)]:
            self.assertEqual(pairwise_log_damage(*args)["status"],
                             "ZERO_COMPONENT_OR_GATE_SEPARATE")
        with self.assertRaises(ValueError):
            geometric_log_bounds((0.5, float("nan")), 1.0)
        with self.assertRaises(ValueError):
            pairwise_log_damage((0.8,), 1.0, (0.4, 0.5), 1.0)

    def test_saved_historical_read_only_analysis_replays(self):
        root = Path(__file__).resolve().parents[1]
        result = compute(root / "runs/20261017_full")
        validate_result(result)
        saved = json.loads((root / "analysis_r17_weight_regions.json").read_text(
            encoding="utf-8")) if (root / "analysis_r17_weight_regions.json").exists() else None
        if saved is not None:
            from analysis_r15_x5c_paired import compare_replay_json
            comparison = compare_replay_json(saved, result)
            self.assertTrue(comparison["passed"], comparison["differences"])
        self.assertGreater(result["n_unique_contrasts"], 0)
        self.assertFalse(result["causal_attribution"])
        self.assertFalse(result["ratio_scale_established"])


if __name__ == "__main__":
    unittest.main()
