"""Numerical-tolerance replay checks; verdicts and identifiers remain exact."""
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from analysis_r15_x5c_paired import compare_replay_json  # noqa: E402


class R16ReplayComparison(unittest.TestCase):
    def test_float_roundoff_is_tolerated_and_max_difference_reported(self):
        saved = {"status": "POST_HOC_PASS", "seed": 17, "count": 2,
                 "estimate": 0.00039835525717941717,
                 "nested": [{"value": 1.0}]}
        computed = {"status": "POST_HOC_PASS", "seed": 17, "count": 2,
                    "estimate": 0.00039835525717941695,
                    "nested": [{"value": 1.0 + 2e-13}]}
        report = compare_replay_json(saved, computed)
        self.assertTrue(report["passed"], report["differences"])
        self.assertGreater(report["max_abs_float_difference"], 0.0)
        self.assertLess(report["max_abs_float_difference"], 1e-12)

    def test_verdict_seed_count_hash_and_types_are_exact(self):
        base = {"status": "PASS", "seed": 17, "count": 2, "hash": "abc", "value": 1.0}
        for key, changed in (("status", "FAIL"), ("seed", 18), ("count", 3),
                             ("hash", "def"), ("count", 2.0)):
            other = dict(base)
            other[key] = changed
            report = compare_replay_json(base, other)
            self.assertFalse(report["passed"], key)

    def test_out_of_tolerance_and_nonfinite_float_fail_closed(self):
        self.assertFalse(compare_replay_json({"x": 1.0}, {"x": 1.0 + 1e-6})["passed"])
        self.assertFalse(compare_replay_json({"x": float("nan")},
                                             {"x": float("nan")})["passed"])
        with self.assertRaises(ValueError):
            compare_replay_json({"x": 1.0}, {"x": 1.0}, abs_tol=-1.0)

    def test_saved_paired_audit_matches_within_float_tolerance(self):
        root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(root))
        from analysis_r15_x5c_paired import compute
        import json
        saved = json.loads((root / "analysis_r15_x5c_paired.json").read_text(
            encoding="utf-8"))
        report = compare_replay_json(saved, compute())
        self.assertTrue(report["passed"], report["differences"])


if __name__ == "__main__":
    unittest.main()
