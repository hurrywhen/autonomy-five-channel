"""R20 data-driven detection rule: formulas, boundaries, analytic anchors,
and the oracle/deployable separation.  No empirical pass conditions."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim.r20_detection import (  # noqa: E402
    CONVENTION_STATUSES, DETECTION_LIMIT, DETECTION_RULE_PROVENANCE,
    DETECTION_RULE_VERSION, ORACLE_RULE_LABEL,
    basic_bootstrap_bias_corrected_interval, classify_share_interval,
    convention_detection_report, oracle_assisted_fixture_classification,
)


class BasicInterval(unittest.TestCase):
    def test_formula_anchor(self):
        # plugin 0.0033464, percentile [0.0047633, 0.0107115] (the registered
        # instance's R19 values): basic interval [2p-q97.5, 2p-q2.5] clipped.
        p = 0.0033464053205058595
        lo, hi = 0.004763275099774422, 0.0107114682051783
        interval = basic_bootstrap_bias_corrected_interval(p, lo, hi)
        self.assertAlmostEqual(interval[0], max(0.0, 2 * p - hi), places=15)
        self.assertAlmostEqual(interval[1], min(1.0, 2 * p - lo), places=15)
        self.assertEqual(interval[0], 0.0)  # lower clipped at zero
        self.assertGreater(interval[1], DETECTION_LIMIT)  # upper above limit

    def test_clipping_and_order(self):
        self.assertEqual(basic_bootstrap_bias_corrected_interval(0.99, 0.98, 1.0),
                         [0.98, 1.0])
        self.assertEqual(basic_bootstrap_bias_corrected_interval(0.01, 0.0, 0.02),
                         [0.0, 0.02])
        interval = basic_bootstrap_bias_corrected_interval(0.5, 0.4, 0.6)
        self.assertEqual(interval, [0.4, 0.6])  # symmetric case: unchanged

    def test_invalid_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            basic_bootstrap_bias_corrected_interval(0.5, 0.6, 0.4)  # unordered
        with self.assertRaises(ValueError):
            basic_bootstrap_bias_corrected_interval(float("nan"), 0.4, 0.6)
        with self.assertRaises(ValueError):
            basic_bootstrap_bias_corrected_interval(1.5, 0.4, 0.6)
        with self.assertRaises(ValueError):
            basic_bootstrap_bias_corrected_interval(0.5, -0.1, 0.6)


class ThreeStateClassification(unittest.TestCase):
    def test_below_above_indeterminate(self):
        self.assertEqual(classify_share_interval([0.0, 1e-7]), "DATA_BELOW_LIMIT")
        self.assertEqual(classify_share_interval([1e-5, 0.01]), "DATA_ABOVE_LIMIT")
        self.assertEqual(classify_share_interval([0.0, 0.0019]),
                         "INDETERMINATE_NEAR_ZERO")
        self.assertEqual(classify_share_interval([5e-7, 2e-6]),
                         "INDETERMINATE_NEAR_ZERO")

    def test_boundary_equality_is_indeterminate(self):
        self.assertEqual(classify_share_interval([0.0, DETECTION_LIMIT]),
                         "INDETERMINATE_NEAR_ZERO")
        self.assertEqual(classify_share_interval([DETECTION_LIMIT, 0.1]),
                         "INDETERMINATE_NEAR_ZERO")

    def test_custom_limit_and_invalid_inputs(self):
        self.assertEqual(classify_share_interval([0.0, 0.005], limit=0.01),
                         "DATA_BELOW_LIMIT")
        with self.assertRaises(ValueError):
            classify_share_interval([0.5, 0.1])
        with self.assertRaises(ValueError):
            classify_share_interval([0.0, 0.1], limit=0.0)
        with self.assertRaises(ValueError):
            classify_share_interval([0.0, 0.1], limit=1.0)
        with self.assertRaises(ValueError):
            classify_share_interval([0.0, float("inf")])

    def test_decision_has_no_truth_parameter(self):
        # The deployable classifier's signature takes only the decision
        # interval and the limit --- no exact-share input exists.
        import inspect
        params = list(inspect.signature(classify_share_interval).parameters)
        self.assertEqual(params, ["interval", "limit"])
        params2 = list(inspect.signature(
            basic_bootstrap_bias_corrected_interval).parameters)
        self.assertEqual(params2, ["plugin_share", "percentile_lower",
                                   "percentile_upper"])


class OracleSeparation(unittest.TestCase):
    def test_oracle_rule_is_labeled_fixture_only(self):
        oracle = oracle_assisted_fixture_classification(4.38e-16)
        self.assertEqual(oracle["label"], ORACLE_RULE_LABEL)
        self.assertIn("NOT_DEPLOYABLE", oracle["label"])
        self.assertTrue(oracle["oracle_below_limit"])
        self.assertFalse(oracle_assisted_fixture_classification(0.5)["oracle_below_limit"])

    def test_all_six_comparison_labels(self):
        fn = lambda share: 0.8 * (share * 0.5 * 0.2655 * 0.9 * 0.531) ** 0.2
        cases = [
            # (plugin, percentile, exact_share, expected comparison)
            (1e-8, [0.0, 5e-8], 1e-16, "TRUE_BELOW"),
            (0.5, [0.4, 0.6], 1e-16, "FALSE_ABOVE"),
            (0.0033464, [0.0047633, 0.0107115], 4.38e-16, "INDETERMINATE_TRUE_BELOW"),
            (0.99, [0.98, 1.0], 1.0, "TRUE_ABOVE"),
            (1e-8, [0.0, 5e-8], 0.9, "FALSE_BELOW"),
            (0.0005, [0.0001, 0.002], 0.9, "INDETERMINATE_TRUE_ABOVE"),
        ]
        for plugin, perc, exact, expected in cases:
            rep = convention_detection_report(plugin_share=plugin,
                                              percentile_interval=perc,
                                              composite_fn=fn, exact_share=exact)
            self.assertEqual(rep["oracle_evaluation"]["classification_vs_oracle"],
                             expected, msg=f"{plugin} {perc} {exact}")
            self.assertEqual(rep["oracle_evaluation"]["label"], ORACLE_RULE_LABEL)

    def test_no_oracle_field_without_exact_share(self):
        rep = convention_detection_report(plugin_share=0.5,
                                          percentile_interval=[0.4, 0.6])
        self.assertNotIn("oracle_evaluation", rep)


class ConventionReport(unittest.TestCase):
    def setUp(self):
        self.fn = lambda share: 0.8 * (share * 0.5 * 0.2655 * 0.9 * 0.531) ** 0.2

    def test_above_limit_propagates_sampling_interval(self):
        rep = convention_detection_report(plugin_share=0.99,
                                          percentile_interval=[0.98, 1.0],
                                          composite_fn=self.fn)
        self.assertEqual(rep["convention_status"], "DATA_ABOVE_LIMIT")
        self.assertEqual(rep["composite_interval"]["kind"], "SAMPLING_BASIC_BOOTSTRAP")
        bounds = rep["composite_interval"]["bounds"]
        self.assertAlmostEqual(bounds[0], self.fn(0.98), places=12)
        self.assertAlmostEqual(bounds[1], self.fn(1.0), places=12)
        self.assertEqual(rep["share_interval"]["kind"], "SAMPLING_BASIC_BOOTSTRAP")

    def test_indeterminate_uses_logical_envelope_not_confidence_interval(self):
        rep = convention_detection_report(plugin_share=0.0033464,
                                          percentile_interval=[0.0047633, 0.0107115],
                                          composite_fn=self.fn)
        self.assertEqual(rep["convention_status"], "INDETERMINATE_NEAR_ZERO")
        self.assertEqual(rep["composite_interval"]["kind"], "LOGICAL_ENVELOPE")
        self.assertEqual(rep["composite_interval"]["bounds"][0], 0.0)
        upper = rep["share_interval"]["bounds"][1]
        self.assertAlmostEqual(rep["composite_interval"]["bounds"][1],
                               self.fn(upper), places=12)
        # The diagnostic plug-in may lie OUTSIDE the reported envelope: it is
        # a different semantics, never the reported point.
        self.assertGreater(rep["diagnostic_plugin_composite"],
                           rep["composite_interval"]["bounds"][1])
        self.assertAlmostEqual(rep["diagnostic_plugin_composite"],
                               self.fn(0.0033464), places=12)

    def test_below_limit_envelope(self):
        rep = convention_detection_report(plugin_share=1e-8,
                                          percentile_interval=[0.0, 5e-8],
                                          composite_fn=self.fn)
        self.assertEqual(rep["convention_status"], "DATA_BELOW_LIMIT")
        self.assertEqual(rep["composite_interval"]["kind"], "LOGICAL_ENVELOPE")
        self.assertEqual(rep["composite_interval"]["bounds"][0], 0.0)

    def test_undefined_composite_channel(self):
        rep = convention_detection_report(plugin_share=0.5,
                                          percentile_interval=[0.4, 0.6],
                                          composite_fn=None)
        self.assertIsNone(rep["composite_interval"])
        self.assertIsNone(rep["composite_interval_sampling"])
        self.assertIsNone(rep["diagnostic_plugin_composite"])
        self.assertEqual(rep["convention_status"], "DATA_ABOVE_LIMIT")

    def test_provenance_fields_present(self):
        rep = convention_detection_report(plugin_share=0.5,
                                          percentile_interval=[0.4, 0.6])
        self.assertEqual(rep["detection_limit"], DETECTION_LIMIT)
        self.assertEqual(rep["detection_rule_version"], DETECTION_RULE_VERSION)
        self.assertEqual(rep["detection_provenance"], DETECTION_RULE_PROVENANCE)
        self.assertIn("DECLARED_BEFORE_R20_STUDY_OUTCOMES", rep["detection_provenance"])
        self.assertIn("POST_HOC_FROZEN", rep["detection_provenance"])
        self.assertTrue(set(rep["convention_status"]) or
                        rep["convention_status"] in CONVENTION_STATUSES)


if __name__ == "__main__":
    unittest.main()