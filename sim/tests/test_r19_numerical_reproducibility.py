"""R19 numerical reproducibility: canonical capacity-input rule, perturbation
stability, near-zero branch, and declared per-field replay tolerances."""
import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from autonomy_sim.empowerment import channel_capacity  # noqa: E402
from autonomy_sim.open_loop_execution import (  # noqa: E402
    CANONICAL_INPUT_REPLAY_TOL, CANONICAL_NEAR_ZERO_NATS,
    canonical_capacity_input_distribution, controlling_open_loop_kernels,
    feedback_copy_counterexample, memoryless_terminal_observation_kernels,
    open_loop_execution_score,
)
from analysis_r15_x5c_paired import compare_replay_json  # noqa: E402


def _parity_kernel(p=0.1):
    return np.array([[1 - p, p], [p, 1 - p], [p, 1 - p], [1 - p, p]])


class R19CanonicalCapacity(unittest.TestCase):
    def test_exact_parity_kernel_canonical_input_is_exactly_uniform(self):
        # The optimal face is two-dimensional (q0+q3 = q1+q2 = 1/2); the raw
        # solver returns a platform-dependent vertex.  The canonical rule
        # returns the exact uniform vector, bit-identical across platforms.
        kernel = _parity_kernel()
        capacity, q_raw = channel_capacity(kernel)
        q_canon = canonical_capacity_input_distribution(kernel, capacity, q_raw)
        np.testing.assert_array_equal(q_canon, np.full(4, 0.25))
        score = open_loop_execution_score(kernel, n_actions=2, action_alphabet_size=2,
                                          canonicalize_input=True)
        self.assertEqual(score["input_distribution_over_allowed"], [0.25] * 4)
        self.assertAlmostEqual(score["a_exec"], 0.26550220320535944, places=12)
        self.assertIsNotNone(score["input_canonicalization"])
        self.assertTrue(score["input_canonicalization"]["non_unique_optimum_auxiliary_coordinate"])

    def test_canonical_output_stable_under_solver_coordinate_perturbations(self):
        # Inject perturbations up to 5e-9 (larger than the observed ~7.5e-10
        # cross-platform drift) into the raw solver coordinates: the canonical
        # representative must be unchanged on the uniform branch.
        kernel = _parity_kernel()
        capacity, q_raw = channel_capacity(kernel)
        base = canonical_capacity_input_distribution(kernel, capacity, q_raw)
        for eps in (1e-12, 1e-10, 7.5e-10, 1e-9, 5e-9):
            for sign in (+1, -1):
                perturbed = q_raw.copy()
                perturbed[0] += sign * eps
                perturbed[1] -= sign * eps
                perturbed /= perturbed.sum()
                q = canonical_capacity_input_distribution(kernel, capacity, perturbed)
                np.testing.assert_array_equal(q, base)

    def test_asymmetric_channel_max_entropy_branch_is_unique_and_verified(self):
        # Rows 1 and 3 are uninformative mixtures; the optimum uses rows 0,2.
        kernel = np.array([[0.9, 0.1], [0.5, 0.5], [0.1, 0.9], [0.5, 0.5]])
        capacity, q_raw = channel_capacity(kernel)
        base = canonical_capacity_input_distribution(kernel, capacity, q_raw)
        np.testing.assert_allclose(base, [0.5, 0.0, 0.5, 0.0], atol=1e-9)
        for eps in (1e-10, 1e-9):
            perturbed = q_raw.copy()
            perturbed[0] += eps
            perturbed[2] -= eps
            perturbed /= perturbed.sum()
            q = canonical_capacity_input_distribution(kernel, capacity, perturbed)
            np.testing.assert_allclose(q, base, atol=CANONICAL_INPUT_REPLAY_TOL)
        # The canonical input achieves capacity within declared precision.
        from autonomy_sim.open_loop_execution import sequence_channel_mi_nats
        achieved = sequence_channel_mi_nats(base, kernel)
        self.assertGreaterEqual(achieved, capacity - 1e-6)

    def test_near_zero_capacity_branch_returns_exact_uniform(self):
        # Sampled action-decoupled kernels have nearly identical rows and tiny
        # positive capacity; moment matching is ill-conditioned there.  The
        # declared near-zero branch returns exact uniform.
        kernel = np.array([[0.9014, 0.0986], [0.9000, 0.1000],
                           [0.9008, 0.0992], [0.8993, 0.1007]])
        capacity, q_raw = channel_capacity(kernel)
        self.assertLessEqual(capacity, CANONICAL_NEAR_ZERO_NATS)
        q = canonical_capacity_input_distribution(kernel, capacity, q_raw)
        np.testing.assert_array_equal(q, np.full(4, 0.25))

    def test_zero_capacity_feedback_copy_canonical_uniform(self):
        witness = feedback_copy_counterexample()
        score = open_loop_execution_score(witness["open_loop_sequence_kernels"],
                                          n_actions=2, action_alphabet_size=2,
                                          canonicalize_input=True)
        self.assertEqual(score["a_exec"], 0.0)
        self.assertEqual(score["input_distribution_over_allowed"], [0.25] * 4)

    def test_identity_and_terminal_bsc_canonical_uniform(self):
        score = open_loop_execution_score(controlling_open_loop_kernels(),
                                          n_actions=2, action_alphabet_size=2,
                                          canonicalize_input=True)
        self.assertEqual(score["input_distribution_over_allowed"], [0.25] * 4)
        self.assertAlmostEqual(score["a_exec"], 1.0, places=12)
        step = np.array([[0.9, 0.1], [0.1, 0.9]])
        score2 = open_loop_execution_score(
            memoryless_terminal_observation_kernels(step, n_actions=2),
            n_actions=2, action_alphabet_size=2, canonicalize_input=True)
        self.assertEqual(score2["input_distribution_over_allowed"], [0.25] * 4)
        self.assertAlmostEqual(score2["a_exec"], 0.26550220320535944, places=12)

    def test_default_path_remains_r18_compatible(self):
        # canonicalize_input defaults to False: historical R17/R18 replays are
        # unaffected (raw solver coordinates, NO canonicalization key at all,
        # byte-identical output schema).
        kernel = _parity_kernel()
        score = open_loop_execution_score(kernel, n_actions=2, action_alphabet_size=2)
        self.assertNotIn("input_canonicalization", score)
        q = score["input_distribution_over_allowed"]
        self.assertAlmostEqual(sum(q), 1.0, places=12)
        self.assertAlmostEqual(score["a_exec"], 0.26550220320535944, places=12)

    def test_canonicalization_fails_closed_on_invalid_inputs(self):
        kernel = _parity_kernel()
        with self.assertRaises(ValueError):
            canonical_capacity_input_distribution(kernel, float("nan"), [0.25] * 4)
        with self.assertRaises(ValueError):
            canonical_capacity_input_distribution(kernel, -0.1, [0.25] * 4)
        # Force the IPF branch (uniform not optimal) with a wrong-size q_raw.
        asymmetric = np.array([[0.9, 0.1], [0.5, 0.5], [0.1, 0.9], [0.5, 0.5]])
        capacity, _ = channel_capacity(asymmetric)
        with self.assertRaises(ValueError):
            canonical_capacity_input_distribution(asymmetric, capacity, [0.5, 0.5])


class R19FieldTolerances(unittest.TestCase):
    def test_default_comparison_unchanged(self):
        saved = {"a": 1.0, "h": "x" * 64}
        computed = {"a": 1.0 + 5e-10, "h": "x" * 64}
        self.assertFalse(compare_replay_json(saved, computed)["passed"])
        self.assertTrue(compare_replay_json(saved, {"a": 1.0, "h": "x" * 64})["passed"])

    def test_field_tolerance_absorbs_declared_auxiliary_drift_only(self):
        saved = {"score": {"input_distribution_over_allowed": [0.5, 0.5, 0.0, 0.0]},
                 "hash": "x" * 64, "count": 3}
        drifted = {"score": {"input_distribution_over_allowed":
                             [0.5 + 7.5e-10, 0.5 - 7.5e-10, 0.0, 0.0]},
                   "hash": "x" * 64, "count": 3}
        tolerances = {"input_distribution_over_allowed": CANONICAL_INPUT_REPLAY_TOL}
        self.assertFalse(compare_replay_json(saved, drifted)["passed"])
        self.assertTrue(compare_replay_json(saved, drifted,
                                            field_tolerances=tolerances)["passed"])
        # Hashes and counts are never covered by float tolerances.
        bad_hash = dict(drifted, hash="y" * 64)
        self.assertFalse(compare_replay_json(saved, bad_hash,
                                             field_tolerances=tolerances)["passed"])
        bad_count = dict(drifted, count=4)
        self.assertFalse(compare_replay_json(saved, bad_count,
                                             field_tolerances=tolerances)["passed"])
        # Drift beyond the declared field tolerance still fails.
        too_far = {"score": {"input_distribution_over_allowed":
                             [0.5 + 1e-5, 0.5 - 1e-5, 0.0, 0.0]},
                   "hash": "x" * 64, "count": 3}
        self.assertFalse(compare_replay_json(saved, too_far,
                                             field_tolerances=tolerances)["passed"])

    def test_invalid_tolerance_declarations_fail_closed(self):
        with self.assertRaises(ValueError):
            compare_replay_json({}, {}, field_tolerances={"": 1e-6})
        with self.assertRaises(ValueError):
            compare_replay_json({}, {}, field_tolerances={"x": -1.0})
        with self.assertRaises(ValueError):
            compare_replay_json({}, {}, field_tolerances={"x": float("nan")})


if __name__ == "__main__":
    unittest.main()
