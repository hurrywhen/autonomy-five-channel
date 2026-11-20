"""R17 open-loop execution repair and feedback-copy negative control."""
import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim.open_loop_execution import (  # noqa: E402
    controlling_open_loop_kernels,
    feedback_copy_counterexample,
    memoryless_sequence_kernels,
    open_loop_execution_score,
    open_loop_zero_iff_rows_identical,
    sequence_channel_mi_nats,
)


class R17OpenLoopExecution(unittest.TestCase):
    def test_feedback_copy_old_mi_is_one_bit_but_open_loop_is_zero(self):
        witness = feedback_copy_counterexample()
        joint = witness["joint"]
        # Independent hand computation: P(O=0)=P(O=1)=1/2, while O is a
        # deterministic function of the reactive action pair (A_t,A_{t+1}).
        outcome = joint.sum(axis=(0, 1, 2))
        entropy_o = -float(np.sum(outcome[outcome > 0] * np.log(outcome[outcome > 0])))
        self.assertAlmostEqual(entropy_o, math.log(2.0), places=14)
        self.assertAlmostEqual(witness["old_conditional_mi_nats"], entropy_o, places=14)
        self.assertAlmostEqual(witness["old_normalized_score"], 0.5, places=14)
        self.assertEqual(witness["repaired_open_loop"]["a_exec"], 0.0)
        self.assertTrue(witness["environment_ignores_actions"])
        self.assertTrue(open_loop_zero_iff_rows_identical(
            witness["open_loop_sequence_kernels"]))

    def test_every_open_loop_mixture_stays_zero_when_actions_are_ignored(self):
        kernels = np.full((4, 2), 0.5)
        for q in ([1, 0, 0, 0], [0.5, 0.5, 0, 0], [0.25] * 4, [0, 0, 0, 1]):
            self.assertAlmostEqual(sequence_channel_mi_nats(q, kernels), 0.0, places=14)
            result = open_loop_execution_score(kernels, n_actions=2,
                                               action_alphabet_size=2, input_dist=q)
            self.assertEqual(result["a_exec"], 0.0)
            self.assertFalse(result["uses_intermediate_observations"])

    def test_controlling_sequences_attain_the_two_action_upper_bound(self):
        result = open_loop_execution_score(controlling_open_loop_kernels(),
                                           n_actions=2, action_alphabet_size=2)
        self.assertAlmostEqual(result["empowerment_nats"], math.log(4.0), places=12)
        self.assertAlmostEqual(result["a_exec"], 1.0, places=12)

    def test_memoryless_bsc_sequence_channel_matches_analytic_capacity(self):
        p = 0.1
        step = np.array([[1 - p, p], [p, 1 - p]])
        kernels = memoryless_sequence_kernels(step, n_actions=2)
        result = open_loop_execution_score(kernels, n_actions=2, action_alphabet_size=2)
        binary_entropy = -p * math.log(p) - (1 - p) * math.log(1 - p)
        expected = 2.0 * (math.log(2.0) - binary_entropy)
        self.assertAlmostEqual(result["empowerment_nats"], expected, places=9)
        self.assertAlmostEqual(result["a_exec"], expected / (2 * math.log(2.0)), places=9)

    def test_repertoire_collapse_and_row_identity_are_zero_controls(self):
        kernels = controlling_open_loop_kernels()
        collapsed = open_loop_execution_score(kernels, n_actions=2,
                                              action_alphabet_size=2,
                                              allowed_sequences=(2,))
        self.assertEqual(collapsed["a_exec"], 0.0)
        self.assertFalse(open_loop_zero_iff_rows_identical(kernels))
        self.assertTrue(open_loop_zero_iff_rows_identical(kernels, allowed_sequences=(2,)))

    def test_invalid_kernels_distributions_and_horizons_fail_closed(self):
        with self.assertRaises(ValueError):
            open_loop_execution_score(np.array([[0.5, 0.5], [float("nan"), 0.0]]),
                                      n_actions=1, action_alphabet_size=2)
        with self.assertRaises(ValueError):
            open_loop_execution_score(np.eye(2), n_actions=1, action_alphabet_size=2,
                                      input_dist=[0.5, 0.4])
        with self.assertRaises(ValueError):
            open_loop_execution_score(np.eye(2), n_actions=0, action_alphabet_size=2)
        with self.assertRaises(ValueError):
            open_loop_execution_score(np.eye(4), n_actions=1, action_alphabet_size=2)
        with self.assertRaises(ValueError):
            open_loop_execution_score(np.eye(4), n_actions=2, action_alphabet_size=2,
                                      allowed_sequences=(4,))


if __name__ == "__main__":
    unittest.main()
