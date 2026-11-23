"""R22 matched A/B/C engine guards: exact R21-C reproduction, A propagation
formula, common-replicate accounting, determinism, and no-causal-attribution
governance.  Empirical coverage rates are not pass conditions."""
import hashlib
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim.aggregate import composite_A  # noqa: E402
from autonomy_sim.native_benchmark import NativeConfig  # noqa: E402
from autonomy_sim.r19_joint_audit import _arm_logs, estimate_from_logs_r19  # noqa: E402
from autonomy_sim.r20_detection import basic_bootstrap_bias_corrected_interval  # noqa: E402
from autonomy_sim.r21_joint_bootstrap import (_execution_sufficient_stats,  # noqa: E402
                                              joint_composite_bootstrap)
from autonomy_sim.r22_interval_contrast import (  # noqa: E402
    CONTRAST_POLICY, METHOD_A, METHOD_B, METHOD_C, METHODS,
    coverage_transitions, matched_interval_bootstrap, method_coverage,
    summarize_matched_replicates)


class MatchedIntervalContrast(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = NativeConfig(surgery=0)
        cls.n = 512
        cls.seed = 20261122
        cls.operating, cls.execution = _arm_logs(
            cls.config, n_samples=cls.n, rng=np.random.default_rng(cls.seed))
        cls.sampled = estimate_from_logs_r19(
            cls.config, cls.operating, cls.execution, n_bootstrap=10,
            rng=np.random.default_rng(1))
        cls.matched = matched_interval_bootstrap(
            cls.config, cls.operating, cls.execution, cls.sampled,
            n_bootstrap=40, rng=np.random.default_rng([cls.seed, cls.n, 21]))
        cls.r21 = joint_composite_bootstrap(
            cls.config, cls.operating, cls.execution,
            n_bootstrap=40, rng=np.random.default_rng([cls.seed, cls.n, 21]))

    def test_c_reproduces_r21_joint_interval_exactly(self):
        for partition, conventions in self.matched["intervals"].items():
            for convention, entry in conventions.items():
                new = entry[METHOD_C]
                old = self.r21["composite_intervals"][partition][convention]
                self.assertEqual(new["bounds"], old["percentile_95"])
                self.assertEqual(new["bootstrap_mean"], old["bootstrap_mean"])
                self.assertEqual(new["bootstrap_se"], old["bootstrap_se"])

    def test_a_is_basic_share_interval_propagated_at_fixed_channels(self):
        channels = self.sampled["channels"]
        fixed = (channels["a_goal_structural"], channels["a_exec_open_loop"],
                 channels["a_epi"], channels["a_ref"])
        for conventions in self.matched["intervals"].values():
            for entry in conventions.values():
                basic = entry[METHOD_A]["share_basic_interval"]
                expected = [float(composite_A(
                    self.sampled["viability_state"], (share,) + fixed,
                    self.config.weights, sigma=1.0)) for share in basic]
                self.assertEqual(entry[METHOD_A]["bounds"], expected)
                self.assertEqual(entry[METHOD_A]["other_channels"], "ORIGINAL_PLUGIN_POINTS")
                self.assertEqual(entry[METHOD_B]["other_channels"], "ORIGINAL_PLUGIN_POINTS")
                self.assertEqual(entry[METHOD_C]["other_channels"], "RECOMPUTED_JOINTLY")
        entry = self.matched["intervals"]["registered"]["RNI"]
        original_share = self.sampled["source"]["registered_partition"]["normative_share_RNI"]
        expected_basic = basic_bootstrap_bias_corrected_interval(
            original_share, *entry[METHOD_A]["share_percentile_95"])
        self.assertEqual(entry[METHOD_A]["share_basic_interval"], expected_basic)

    def test_common_replicate_accounting_and_bounds(self):
        for partition, conventions in self.matched["intervals"].items():
            for convention, entry in conventions.items():
                audit = self.matched["replicate_audit"][partition][convention]
                self.assertEqual(audit["n_bootstrap"], 40)
                self.assertEqual(audit["n_common_finite"]
                                 + audit["n_excluded_from_matched_contrast"], 40)
                self.assertGreaterEqual(audit["n_common_finite"], 2)
                self.assertEqual(len(audit["common_finite_mask_sha256"]), 64)
                self.assertNotIn("share_replicates_sha256", audit)
                self.assertNotIn("conditional_composite_replicates_sha256", audit)
                self.assertNotIn("joint_composite_replicates_sha256", audit)
                for method in METHODS:
                    lo, hi = entry[method]["bounds"]
                    self.assertTrue(0.0 <= lo <= hi <= 1.0)
        self.assertEqual(len(self.matched["resampling_audit"]["draws_sha256"]), 64)
        self.assertTrue(self.matched["resampling_audit"]["not_analysis_output_float_hash"])

    def test_independent_synthetic_a_b_and_nonfull_common_mask(self):
        share = np.array([0.2, 0.4, 0.6, 0.8, 0.5, 0.1])
        conditional = share ** 2
        joint = np.array([0.14, 0.26, 0.46, 0.74, np.nan, 0.11])
        entry, audit = summarize_matched_replicates(
            0.5, share, conditional, joint, lambda value: value ** 2)
        mask = np.array([True, True, True, True, False, True])
        self.assertEqual(audit["n_common_finite"], 5)
        self.assertEqual(audit["n_excluded_from_matched_contrast"], 1)
        expected_mask_hash = hashlib.sha256(
            np.packbits(mask, bitorder="big").tobytes()).hexdigest()
        self.assertEqual(audit["common_finite_mask_sha256"], expected_mask_hash)
        perc = [float(np.percentile(share[mask], 2.5)),
                float(np.percentile(share[mask], 97.5))]
        basic = basic_bootstrap_bias_corrected_interval(0.5, *perc)
        self.assertEqual(entry[METHOD_A]["share_percentile_95"], perc)
        self.assertEqual(entry[METHOD_A]["share_basic_interval"], basic)
        self.assertEqual(entry[METHOD_A]["plugin_share"], 0.5)
        self.assertEqual(entry[METHOD_A]["bounds"], [basic[0] ** 2, basic[1] ** 2])
        for method, values in ((METHOD_B, conditional[mask]), (METHOD_C, joint[mask])):
            self.assertEqual(entry[method]["bounds"], [float(np.percentile(values, 2.5)),
                                                       float(np.percentile(values, 97.5))])
            self.assertEqual(entry[method]["bootstrap_mean"], float(values.mean()))
            self.assertEqual(entry[method]["bootstrap_se"], float(values.std(ddof=1)))
        with self.assertRaises(ValueError):
            summarize_matched_replicates(0.5, share, conditional, joint[:-1],
                                         lambda value: value ** 2)

    def test_deterministic_given_seed(self):
        again = matched_interval_bootstrap(
            self.config, self.operating, self.execution, self.sampled,
            n_bootstrap=40, rng=np.random.default_rng([self.seed, self.n, 21]))
        self.assertEqual(again, self.matched)
        # Independently replay the exact operating and execution RNG indices;
        # no capacity or composite computations are needed for this audit hash.
        seq_indices, terminals = _execution_sufficient_stats(self.execution)
        rng = np.random.default_rng([self.seed, self.n, 21])
        digest = hashlib.sha256()
        for _ in range(40):
            idx = rng.integers(0, self.n, size=self.n)
            digest.update(np.asarray(idx, dtype="<i8").tobytes(order="C"))
            for sequence in seq_indices:
                term = terminals[sequence]
                draw_idx = rng.integers(0, len(term), size=len(term))
                digest.update(np.asarray([sequence, len(term)], dtype="<i8").tobytes(order="C"))
                digest.update(np.asarray(draw_idx, dtype="<i8").tobytes(order="C"))
        self.assertEqual(self.matched["resampling_audit"]["draws_sha256"],
                         digest.hexdigest())

    def test_coverage_helpers_full_transition_table(self):
        entry = self.matched["intervals"]["registered"]["RNI"]
        anchor = 0.4608565248033332
        coverage = method_coverage(entry, anchor)
        self.assertEqual(set(coverage), set(METHODS))
        for method in METHODS:
            lo, hi = entry[method]["bounds"]
            self.assertEqual(coverage[method], lo <= anchor <= hi)
        rows = [{"method_coverage": {METHOD_A: False, METHOD_B: False, METHOD_C: True}},
                {"method_coverage": {METHOD_A: False, METHOD_B: False, METHOD_C: False}},
                {"method_coverage": {METHOD_A: True, METHOD_B: True, METHOD_C: False}},
                {"method_coverage": {METHOD_A: True, METHOD_B: True, METHOD_C: True}}]
        self.assertEqual(coverage_transitions(rows, METHOD_B, METHOD_C),
                         {"miss_miss": 1, "miss_cover": 1, "cover_miss": 1, "cover_cover": 1})
        with self.assertRaises(ValueError):
            coverage_transitions(rows, METHOD_A, METHOD_A)

    def test_policy_is_descriptive_not_causal(self):
        self.assertEqual(self.matched["policy"], CONTRAST_POLICY)
        self.assertTrue(CONTRAST_POLICY["not_formal_bias_decomposition"])
        self.assertTrue(CONTRAST_POLICY["not_certificate_reported_semantics"])
        self.assertIn("NOT_IDENTIFIED", CONTRAST_POLICY["A_vs_C"])
        self.assertIn("NO_SINGLE_CAUSE", CONTRAST_POLICY["both_miss"])

    def test_invalid_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            matched_interval_bootstrap(
                self.config, self.operating, self.execution, self.sampled,
                n_bootstrap=1, rng=np.random.default_rng(1))
        with self.assertRaises(ValueError):
            matched_interval_bootstrap(
                self.config, self.operating[:1], self.execution, self.sampled,
                n_bootstrap=10, rng=np.random.default_rng(1))
        broken = dict(self.sampled)
        broken["channels"] = dict(self.sampled["channels"], a_ref=None)
        with self.assertRaises(ValueError):
            matched_interval_bootstrap(
                self.config, self.operating, self.execution, broken,
                n_bootstrap=10, rng=np.random.default_rng(1))


if __name__ == "__main__":
    unittest.main()
