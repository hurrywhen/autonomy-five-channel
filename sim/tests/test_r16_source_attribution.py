"""R16 exact finite-binary source-attribution guards.

All laws below are constructed trajectory by trajectory.  The reference DI
oracle independently accumulates atom-wise conditional-MI log ratios; it does
not call the implementation's entropy, marginalization, or DI routines.  These
are exact mathematical model guards, not experiments and not external
construct validation.
"""
import itertools
import math
import os
import sys
import unittest
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim.source_attribution import (  # noqa: E402
    flow_share,
    joint_directed_information_nats,
    nats_to_bits,
    ordered_attribution_nats,
    ordered_residual_di_nats,
    shapley_order_average_nats,
    validate_binary_sequence_joint,
)

R, N, I, A = 0, 1, 2, 3
LN2 = math.log(2.0)


def _prefix(variables, time, horizon=2):
    return tuple(variable * horizon + past
                 for variable in variables for past in range(time + 1))


def _reference_di_bits(joint, sources, action, conditioning=(), horizon=2):
    """Independent exact oracle: enumerate every positive atom and every history.

    For each t this directly evaluates
        sum p(x,y,z) log2[p(x,y,z)p(z) / (p(x,z)p(y,z))],
    where x=X^t, y=A_t, and z=(A^(t-1),Z^t).  In particular, the test oracle
    never reuses the implementation's tensor-marginal entropy identities.
    """
    result = 0.0
    for time in range(horizon):
        x_axes = _prefix(tuple(sources), time, horizon)
        z_axes = (_prefix(tuple(conditioning), time, horizon)
                  + tuple(action * horizon + past for past in range(time)))
        y_axis = action * horizon + time
        p_xyz = defaultdict(float)
        p_xz = defaultdict(float)
        p_yz = defaultdict(float)
        p_z = defaultdict(float)
        for index in np.ndindex(joint.shape):
            probability = float(joint[index])
            if probability == 0.0:
                continue
            x = tuple(index[axis] for axis in x_axes)
            y = index[y_axis]
            z = tuple(index[axis] for axis in z_axes)
            p_xyz[x, y, z] += probability
            p_xz[x, z] += probability
            p_yz[y, z] += probability
            p_z[z] += probability
        for (x, y, z), probability in p_xyz.items():
            result += probability * math.log2(
                probability * p_z[z] / (p_xz[x, z] * p_yz[y, z]))
    return result


def _or_law():
    """Independent fair R,N; A=R OR N; axes (R,N,A), with no I variable."""
    joint = np.zeros((2, 2, 2))
    for r in (0, 1):
        for n in (0, 1):
            joint[r, n, r | n] += 0.25
    return joint


def _policy_action(policy, r, n):
    if policy == "pure_random":
        return r
    if policy == "pure_normative":
        return n
    if policy == "mixed_xor":
        return r ^ n
    raise AssertionError(f"unknown test policy {policy}")


def _closed_loop_law(policy):
    """T=2 deterministic SCM, axes (R1,R2,N1,N2,I1,I2,A1,A2).

    Exogenous R1,R2,I1,I2 are independent fair bits.  N1=I1 and
    N2=N1 XOR A1 XOR I2, so the second normative state has action feedback and
    external input is mediated by N.  Actions are respectively R_t, N_t, or
    R_t XOR N_t for the pure-random, pure-normative, and mixed policies.
    Each of the 16 exogenous trajectories has probability 1/16.
    """
    joint = np.zeros((2,) * 8)
    for r1, r2, i1, i2 in itertools.product((0, 1), repeat=4):
        n1 = i1
        a1 = _policy_action(policy, r1, n1)
        n2 = n1 ^ a1 ^ i2
        a2 = _policy_action(policy, r2, n2)
        joint[r1, r2, n1, n2, i1, i2, a1, a2] += 1.0 / 16.0
    return joint


def _direct_bypass_law():
    """Positive-control SCM: I_t enters A_t directly, outside the N update.

    Exogenous bits are as above.  N1=0 and N2=A1 retain action feedback but do
    not carry I2.  The mixed-with-bypass actions are
    A1=R1 XOR N1 XOR I1 and A2=R2 XOR N2 XOR I2.  Thus, even after conditioning
    on complete R and N histories and A^(t-1), fresh I_t still determines A_t.
    """
    joint = np.zeros((2,) * 8)
    for r1, r2, i1, i2 in itertools.product((0, 1), repeat=4):
        n1 = 0
        a1 = r1 ^ n1 ^ i1
        n2 = a1
        a2 = r2 ^ n2 ^ i2
        joint[r1, r2, n1, n2, i1, i2, a1, a2] += 1.0 / 16.0
    return joint


def _bits(flows):
    return tuple(nats_to_bits(flow) for flow in flows)


class R16ORGateGuard(unittest.TestCase):
    def test_T_R16_OR_exact_bits_order_reversal_and_order_average(self):
        joint = _or_law()
        rn = _bits(ordered_attribution_nats(
            joint, horizon=1, order=(R, N), action=2))
        nr = _bits(ordered_attribution_nats(
            joint, horizon=1, order=(N, R), action=2))
        grouped = nats_to_bits(joint_directed_information_nats(
            joint, horizon=1, sources=(R, N), action=2))

        # P(A=1)=3/4 and H(A|R)=1/2 bit.  These identities give the exact
        # anchor, independently of both DI implementations.
        entropy_a = 2.0 - 0.75 * math.log2(3.0)
        self.assertAlmostEqual(entropy_a, 0.8112781244591328, places=15)
        self.assertAlmostEqual(rn[0], entropy_a - 0.5, places=14)
        self.assertAlmostEqual(rn[0], 0.31127812445913283, places=14)
        self.assertAlmostEqual(rn[1], 0.5, places=14)
        self.assertAlmostEqual(grouped, entropy_a, places=14)
        self.assertAlmostEqual(math.fsum(rn), grouped, places=14)
        self.assertAlmostEqual(math.fsum(nr), grouped, places=14)
        self.assertAlmostEqual(nr[0], entropy_a - 0.5, places=14)
        self.assertAlmostEqual(nr[1], 0.5, places=14)

        share_rn = flow_share(rn[1], grouped)
        share_nr = flow_share(nr[0], grouped)
        self.assertAlmostEqual(share_rn, 0.6163114534036557, places=14)
        self.assertAlmostEqual(share_nr, 0.3836885465963443, places=14)
        self.assertAlmostEqual(share_rn + share_nr, 1.0, places=14)

        average = shapley_order_average_nats(
            joint, horizon=1, sources=(R, N), action=2)
        average = {source: nats_to_bits(flow) for source, flow in average.items()}
        self.assertAlmostEqual(average[R], entropy_a / 2.0, places=14)
        self.assertAlmostEqual(average[N], entropy_a / 2.0, places=14)
        # This 0.5 is an order-sensitivity descriptor, not a causal/PID-
        # identified unique decomposition of the OR interaction.
        self.assertAlmostEqual(flow_share(average[N], grouped), 0.5, places=14)

        # Independent atom-wise checks for the first flow, residual flow, and
        # grouped joint DI (horizon one, so A^(t-1) is empty).
        self.assertAlmostEqual(
            _reference_di_bits(joint, (R,), 2, horizon=1), rn[0], places=14)
        self.assertAlmostEqual(
            _reference_di_bits(joint, (N,), 2, (R,), horizon=1), rn[1], places=14)
        self.assertAlmostEqual(
            _reference_di_bits(joint, (R, N), 2, horizon=1), grouped, places=14)


class R16ClosedLoopEnumeration(unittest.TestCase):
    def test_T_R16_closed_loop_policies_chain_equals_joint_and_matches_oracle(self):
        # Entries are (RN/I flows, NR/I flows), all in bits.  The mixed XOR
        # policy is interaction-rich: neither source alone has marginal DI,
        # while the second source in either order supplies the two action bits.
        expected = {
            "pure_random": ((2.0, 0.0, 0.0), (0.0, 2.0, 0.0)),
            "pure_normative": ((0.0, 2.0, 0.0), (2.0, 0.0, 0.0)),
            "mixed_xor": ((0.0, 2.0, 0.0), (0.0, 2.0, 0.0)),
        }
        for policy, (expected_rn, expected_nr) in expected.items():
            with self.subTest(policy=policy):
                joint = _closed_loop_law(policy)
                # Independent trajectory-enumeration sanity check: exactly one
                # positive atom per exogenous trajectory, each with mass 1/16.
                self.assertEqual(np.count_nonzero(joint), 16)
                np.testing.assert_allclose(joint[joint > 0.0], 1.0 / 16.0)
                rn = _bits(ordered_attribution_nats(
                    joint, horizon=2, order=(R, N, I), action=A))
                nr = _bits(ordered_attribution_nats(
                    joint, horizon=2, order=(N, R, I), action=A))
                grouped = nats_to_bits(joint_directed_information_nats(
                    joint, horizon=2, sources=(R, N, I), action=A))
                np.testing.assert_allclose(rn, expected_rn, atol=2e-12, rtol=0.0)
                np.testing.assert_allclose(nr, expected_nr, atol=2e-12, rtol=0.0)
                self.assertAlmostEqual(math.fsum(rn), grouped, places=12)
                self.assertAlmostEqual(math.fsum(nr), grouped, places=12)
                self.assertAlmostEqual(grouped, 2.0, places=12)

                specifications = (
                    ((R,), (), rn[0]),
                    ((N,), (R,), rn[1]),
                    ((I,), (R, N), rn[2]),
                    ((N,), (), nr[0]),
                    ((R,), (N,), nr[1]),
                    ((I,), (N, R), nr[2]),
                    ((R, N, I), (), grouped),
                )
                for sources, conditioning, actual in specifications:
                    reference = _reference_di_bits(
                        joint, sources, A, conditioning, horizon=2)
                    self.assertAlmostEqual(actual, reference, places=11)

    def test_T_R16_mixed_interaction_is_order_sensitive_with_I_last(self):
        joint = _closed_loop_law("mixed_xor")
        rn = _bits(ordered_attribution_nats(
            joint, horizon=2, order=(R, N, I), action=A))
        nr = _bits(ordered_attribution_nats(
            joint, horizon=2, order=(N, R, I), action=A))
        total = nats_to_bits(joint_directed_information_nats(
            joint, horizon=2, sources=(R, N, I), action=A))
        self.assertAlmostEqual(flow_share(rn[1], total), 1.0, places=12)
        self.assertAlmostEqual(flow_share(nr[0], total), 0.0, places=12)
        self.assertNotAlmostEqual(rn[1], nr[0], places=6)

        # Average only the two R,N orders while holding I last in both chains.
        # Align NR back to (R,N,I) before averaging.  This is strictly an
        # order-sensitivity descriptor, not a unique causal/PID attribution.
        average_r = 0.5 * (rn[0] + nr[1])
        average_n = 0.5 * (rn[1] + nr[0])
        average_i = 0.5 * (rn[2] + nr[2])
        self.assertAlmostEqual(average_r, 1.0, places=12)
        self.assertAlmostEqual(average_n, 1.0, places=12)
        self.assertAlmostEqual(average_i, 0.0, places=12)
        self.assertAlmostEqual(flow_share(average_n, total), 0.5, places=12)

    def test_T_R16_pure_random_zero_is_RNI_specific_not_order_free(self):
        # N=R duplicates the register to make the semantic/order caveat explicit:
        # RNI gives normative residual zero, whereas NRI gives it the full share.
        joint = np.zeros((2, 2, 2))
        for r in (0, 1):
            joint[r, r, r] = 0.5
        rn = _bits(ordered_attribution_nats(joint, horizon=1, order=(R, N), action=2))
        nr = _bits(ordered_attribution_nats(joint, horizon=1, order=(N, R), action=2))
        total = nats_to_bits(joint_directed_information_nats(
            joint, horizon=1, sources=(R, N), action=2))
        self.assertAlmostEqual(flow_share(rn[1], total), 0.0, places=12)
        self.assertAlmostEqual(flow_share(nr[0], total), 1.0, places=12)
        # This is why a pure-random zero is a statement about the primary RNI
        # convention, not an order-free or semantic-relabeling-proof theorem.


class R16MediationAndBypass(unittest.TestCase):
    def test_T_R16_mediated_external_input_has_flow_but_zero_residual(self):
        joint = _closed_loop_law("pure_normative")
        # A1=I1 and A2=I2 through N, so the external-only grouped DI is a
        # nonempty two-bit mediation witness, not a vacuous zero-flow model.
        external_only = nats_to_bits(joint_directed_information_nats(
            joint, horizon=2, sources=(I,), action=A))
        residual = nats_to_bits(ordered_residual_di_nats(
            joint, horizon=2, source=I, action=A, condition_on=(R, N)))
        self.assertAlmostEqual(external_only, 2.0, places=12)
        self.assertAlmostEqual(
            _reference_di_bits(joint, (I,), A, horizon=2), 2.0, places=12)
        self.assertAlmostEqual(residual, 0.0, places=12)
        self.assertAlmostEqual(
            _reference_di_bits(joint, (I,), A, (R, N), horizon=2),
            0.0, places=12)

    def test_T_R16_direct_action_bypass_has_positive_external_residual(self):
        joint = _direct_bypass_law()
        self.assertEqual(np.count_nonzero(joint), 16)
        np.testing.assert_allclose(joint[joint > 0.0], 1.0 / 16.0)
        chain = _bits(ordered_attribution_nats(
            joint, horizon=2, order=(R, N, I), action=A))
        grouped = nats_to_bits(joint_directed_information_nats(
            joint, horizon=2, sources=(R, N, I), action=A))
        self.assertAlmostEqual(chain[2], 2.0, places=12)
        self.assertGreater(chain[2], 0.0)
        self.assertAlmostEqual(math.fsum(chain), grouped, places=12)
        self.assertAlmostEqual(grouped, 2.0, places=12)
        self.assertAlmostEqual(
            _reference_di_bits(joint, (I,), A, (R, N), horizon=2),
            chain[2], places=12)


class R16FailClosedValidation(unittest.TestCase):
    def test_T_R16_invalid_probabilities_and_shapes_are_rejected(self):
        valid = _or_law()
        cases = {}
        nonfinite_nan = valid.copy()
        nonfinite_nan[0, 0, 0] = math.nan
        cases["nan"] = nonfinite_nan
        nonfinite_inf = valid.copy()
        nonfinite_inf[0, 0, 0] = math.inf
        cases["inf"] = nonfinite_inf
        negative = valid.copy()
        negative[0, 0, 0] = -0.25
        cases["negative"] = negative
        cases["unnormalized"] = valid * 0.9
        cases["nonbinary_alphabet"] = np.full((2, 2, 3), 1.0 / 12.0)
        cases["flat_not_sequence_layout"] = np.full(8, 1.0 / 8.0)
        for label, candidate in cases.items():
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    validate_binary_sequence_joint(candidate, horizon=1)
        with self.assertRaises(ValueError):
            validate_binary_sequence_joint(
                np.full((2, 2, 2, 3), 1.0 / 24.0), horizon=2)
        with self.assertRaises(ValueError):
            validate_binary_sequence_joint(valid, horizon=1, n_variables=4)
        for bad_horizon in (0, -1, 1.5, True):
            with self.subTest(bad_horizon=bad_horizon):
                with self.assertRaises(ValueError):
                    validate_binary_sequence_joint(valid, horizon=bad_horizon)

    def test_T_R16_invalid_attribution_specs_and_zero_denominator_are_rejected(self):
        joint = _or_law()
        bad_orders = ((R, R), (R, N, 2), (R, 3), ())
        for order in bad_orders:
            with self.subTest(order=order):
                with self.assertRaises(ValueError):
                    ordered_attribution_nats(
                        joint, horizon=1, order=order, action=2)
        with self.assertRaises(ValueError):
            ordered_residual_di_nats(
                joint, horizon=1, source=N, action=2, condition_on=(R, R))
        with self.assertRaises(ValueError):
            ordered_residual_di_nats(
                joint, horizon=1, source=N, action=2, condition_on=(N,))
        for part, total in ((0.0, 0.0), (-1.0, 1.0), (2.0, 1.0),
                            (1e-13, 1e-15), (math.nan, 1.0), (1.0, math.inf)):
            with self.subTest(part=part, total=total):
                with self.assertRaises(ValueError):
                    flow_share(part, total)


if __name__ == "__main__":
    unittest.main()
