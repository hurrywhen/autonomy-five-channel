"""R18 open-loop output conventions: terminal observation vs observation
sequence, and the support-relative zero-MI quantifier."""
import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim.open_loop_execution import (  # noqa: E402
    controlling_open_loop_kernels,
    memoryless_observation_sequence_kernels,
    memoryless_sequence_kernels,
    memoryless_terminal_observation_kernels,
    open_loop_execution_score,
    open_loop_zero_iff_positive_support_rows_identical,
    open_loop_zero_iff_rows_identical,
    sequence_channel_mi_nats,
)


def _bsc(p: float) -> np.ndarray:
    return np.array([[1 - p, p], [p, 1 - p]])


def _binary_entropy(p: float) -> float:
    return -p * math.log(p) - (1 - p) * math.log(1 - p)


class R18OpenLoopConventions(unittest.TestCase):
    def test_terminal_observation_bsc_matches_paper_estimand(self):
        # The paper reads only O_{t+n}; for a memoryless per-step BSC the
        # terminal kernel depends only on the last action.  p=0.1, n=2:
        # capacity ln2 - H_b(0.1), normalized by 2 ln2 -> 0.2655022.
        p = 0.1
        kernels = memoryless_terminal_observation_kernels(_bsc(p), n_actions=2)
        self.assertEqual(kernels.shape, (4, 2))
        for sequence in range(4):
            np.testing.assert_allclose(kernels[sequence], _bsc(p)[sequence % 2])
        result = open_loop_execution_score(kernels, n_actions=2, action_alphabet_size=2)
        expected = (math.log(2.0) - _binary_entropy(p)) / (2 * math.log(2.0))
        self.assertAlmostEqual(result["a_exec"], expected, places=12)
        self.assertAlmostEqual(result["a_exec"], 0.26550220320535944, places=12)
        self.assertFalse(result["uses_intermediate_observations"])

    def test_observation_sequence_channel_is_a_different_object(self):
        # The Kronecker construction reads the WHOLE observation sequence;
        # its normalized capacity is 1 - H_b(p)/ln2 = 0.5310044 at p=0.1,
        # strictly larger than the terminal-observation value.
        p = 0.1
        kernels = memoryless_observation_sequence_kernels(_bsc(p), n_actions=2)
        result = open_loop_execution_score(kernels, n_actions=2, action_alphabet_size=2)
        expected = 1.0 - _binary_entropy(p) / math.log(2.0)
        self.assertAlmostEqual(result["a_exec"], expected, places=12)
        self.assertAlmostEqual(result["a_exec"], 0.5310044064107189, places=12)
        terminal = open_loop_execution_score(
            memoryless_terminal_observation_kernels(_bsc(p), n_actions=2),
            n_actions=2, action_alphabet_size=2)
        self.assertGreater(result["a_exec"], terminal["a_exec"] + 0.2)
        # Backward-compatible R17 alias denotes the same observation-sequence object.
        np.testing.assert_allclose(memoryless_sequence_kernels(_bsc(p), n_actions=2),
                                   kernels)

    def test_fixed_point_mass_q_is_zero_even_with_distinct_rows(self):
        # R18 quantifier regression: a point-mass precommitted distribution has
        # zero MI regardless of kernel differences; capacity over the same
        # allowed set is positive.  The zero-iff must be support-relative.
        kernels = controlling_open_loop_kernels()
        q = [1.0, 0.0, 0.0, 0.0]
        fixed = open_loop_execution_score(kernels, n_actions=2, action_alphabet_size=2,
                                          input_dist=q)
        self.assertEqual(fixed["a_exec"], 0.0)
        self.assertEqual(fixed["empowerment_nats"], 0.0)
        capacity = open_loop_execution_score(kernels, n_actions=2, action_alphabet_size=2)
        self.assertGreater(capacity["a_exec"], 0.99)
        self.assertFalse(open_loop_zero_iff_rows_identical(kernels))
        self.assertTrue(open_loop_zero_iff_positive_support_rows_identical(kernels, q))
        self.assertFalse(open_loop_zero_iff_positive_support_rows_identical(
            kernels, [0.25, 0.25, 0.25, 0.25]))

    def test_support_iff_tracks_positive_probability_rows_only(self):
        kernels = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 0.0], [0.0, 1.0]])
        # Support {0,2}: identical rows -> zero MI.  Support {0,1}: distinct.
        self.assertTrue(open_loop_zero_iff_positive_support_rows_identical(
            kernels, [0.5, 0.0, 0.5, 0.0]))
        self.assertFalse(open_loop_zero_iff_positive_support_rows_identical(
            kernels, [0.5, 0.5, 0.0, 0.0]))
        self.assertAlmostEqual(sequence_channel_mi_nats([0.5, 0.0, 0.5, 0.0], kernels),
                               0.0, places=14)
        self.assertAlmostEqual(sequence_channel_mi_nats([0.5, 0.5, 0.0, 0.0], kernels),
                               math.log(2.0), places=14)
        # Capacity mode quantifies over every allowed sequence (point masses
        # admissible), so distinct rows anywhere in the allowed set give >0.
        self.assertFalse(open_loop_zero_iff_rows_identical(kernels))
        self.assertTrue(open_loop_zero_iff_rows_identical(kernels, allowed_sequences=(0, 2)))

    def test_convention_helpers_fail_closed(self):
        with self.assertRaises(ValueError):
            memoryless_terminal_observation_kernels(np.array([[0.5, 0.5]]), n_actions=2)
        with self.assertRaises(ValueError):
            memoryless_terminal_observation_kernels(_bsc(0.1), n_actions=0)
        with self.assertRaises(ValueError):
            open_loop_zero_iff_positive_support_rows_identical(
                controlling_open_loop_kernels(), [0.0, 0.0, 0.0, 0.0])
        with self.assertRaises(ValueError):
            open_loop_zero_iff_positive_support_rows_identical(
                controlling_open_loop_kernels(), [1.0, 0.0, 0.0], allowed_sequences=(0,))
        with self.assertRaises(ValueError):
            open_loop_zero_iff_positive_support_rows_identical(
                controlling_open_loop_kernels(), [0.5, 0.5, 0.0, 0.0],
                allowed_sequences=(0,))


if __name__ == "__main__":
    unittest.main()