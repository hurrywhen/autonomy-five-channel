"""R14 reviewer-counterexample and estimand regression tests.

These are deterministic mathematical checks, not independent experiments or
external construct validation.  Historical CONFIRMED archives are not inputs.
"""
import math
import unittest
import warnings

import numpy as np

from autonomy_sim.aggregate import composite_A
from autonomy_sim.attack import (defense_equalization_necessary, grid_search_2d,
                                 linear_fraction_objective, loglinear_damage_comparison,
                                 solve_linear_fraction_attack,
                                 symbolic_symmetric_kkt_certificate)
from autonomy_sim.components import truth_A_ref
from autonomy_sim.counterfactual import (ThresholdEndorsementSCM,
                                         identity_endorsement_audit,
                                         observation_equivalent_xor_witness,
                                         xor_endorsement_audit,
                                         xor_endorsement_audit_from_observations)
from autonomy_sim.di import entropy_nats, mi_nats
from autonomy_sim.empowerment import a_exec
from autonomy_sim.env0 import Env0Config
from autonomy_sim.wiring import _truth_a_ref
from autonomy_sim.numerics import NumericalBoundaryWarning, clip_unit_value
from autonomy_sim.rng import make_rng


class R14PositivityAndMonotonicity(unittest.TestCase):
    def test_T_R14_T1B_zero_lambda_ref_annihilates_despite_other_positive_factors(self):
        joint = np.array([[0.5, 0.0], [0.0, 0.5]])  # fidelity 1, finite discrete ensemble
        result = truth_A_ref(joint, p_endorse=1.0, lam_ref=0.0)
        self.assertEqual(result.point, 0.0)
        a = composite_A(1.0, (0.9, 0.9, 0.9, 0.9, result.point),
                        (0.2,) * 5, 1.0)
        self.assertEqual(a, 0.0)
        positive = truth_A_ref(joint, p_endorse=1.0, lam_ref=1.0)
        self.assertGreater(positive.point, 0.0)

    def test_T_R14_ORG_positive_post_external_flow_does_not_imply_decline(self):
        before = 0.1 / (0.1 + 1.0)
        after = 1.0 / (1.0 + 0.1)
        self.assertAlmostEqual(before, 1.0 / 11.0)
        self.assertAlmostEqual(after, 10.0 / 11.0)
        self.assertGreater(after, before)
        ratio_before, ratio_after = 1.0 / 0.1, 0.1 / 1.0
        self.assertLess(ratio_after, ratio_before)
        # The corrected sufficient comparison is the external/internal ratio.
        self.assertTrue(1.0 / 0.5 > 0.2 / 0.5)

    def test_T_R14_GOAL_identity_endorsement_returns_degenerate_interval(self):
        from autonomy_sim.components import truth_A_goal
        result = truth_A_goal(0.5, lambda u: u, [0.0, 0.5, 1.0])
        self.assertTrue(result.degenerate)
        self.assertIsNone(result.point)
        self.assertEqual((result.lo, result.hi), (0.0, 1.0))

    def test_T_R14_GOAL_leaving_or_staying_off_fix_is_not_distance_increase(self):
        dc = 1.0
        d0, d1 = 0.8, 0.1
        self.assertAlmostEqual(1.0 - d0 / dc, 0.2)
        self.assertAlmostEqual(1.0 - d1 / dc, 0.9)
        self.assertGreater(d0, d1)
        # A separate zero baseline makes every strict composite decrease vacuous.
        a0 = a1 = 0.0
        self.assertEqual(a0, a1)


class R14LinearFractionOptimization(unittest.TestCase):
    def setUp(self):
        self.w = (0.5, 0.5)
        self.c = self.s = (1.0, 1.0)
        self.B = 0.5

    def test_T_R14_LINF_concentrated_beats_spread_for_attacker_minimization(self):
        concentrated = linear_fraction_objective((0.5, 0.0), self.w, self.s)
        spread = linear_fraction_objective((0.25, 0.25), self.w, self.s)
        self.assertAlmostEqual(concentrated, -0.34657359027997264)
        self.assertAlmostEqual(spread, -0.2876820724517809)
        self.assertLess(concentrated, spread)

    def test_T_R14_LINF_vertex_grid_and_symbolic_certificates_agree(self):
        exact = solve_linear_fraction_attack(self.w, self.c, self.s, self.B)
        self.assertAlmostEqual(exact["objective"], -0.5 * math.log(2.0))
        self.assertEqual(exact["optimal_channels"], [0, 1])  # symmetric tie
        self.assertAlmostEqual(exact["x"][0], 0.5)
        grid = grid_search_2d(self.w, self.c, self.s, self.B, n=81)
        self.assertGreaterEqual(grid["objective"], exact["objective"] - 1e-12)
        self.assertLess(abs(grid["objective"] - exact["objective"]), 0.01)
        symbolic = symbolic_symmetric_kkt_certificate()
        self.assertTrue(symbolic["stationary_is_local_maximum"])
        self.assertAlmostEqual(symbolic["budget_multiplier"], 2.0 / 3.0)
        self.assertTrue(all(abs(h + 8.0 / 9.0) < 1e-12
                            for h in symbolic["hessian_diagonal"]))
        self.assertAlmostEqual(symbolic["minimum"]["objective"], exact["objective"])

    def test_T_R14_LINF_zero_retention_is_extended_minus_infinity(self):
        result = solve_linear_fraction_attack((0.5, 0.5), (1.0, 1.0), (1.0, 1.0), 1.0)
        self.assertEqual(result["objective"], -math.inf)

    def test_T_R14_T4_INDEX_non_equal_weights_use_selected_channel(self):
        comparison = loglinear_damage_comparison((0.2, 0.8), (1.0, 1.0),
                                                  (1.0, 1.0), 0.5)
        self.assertEqual(comparison["pick"], 1)
        self.assertAlmostEqual(comparison["concentrated"], 0.4)
        self.assertAlmostEqual(comparison["spread"], 0.25)
        tied = loglinear_damage_comparison((0.5, 0.5), (1.0, 1.0),
                                           (1.0, 1.0), 0.5)
        self.assertEqual(tied["optimal_channels"], [0, 1])

    def test_T_R14_LINF_zero_boundary_can_have_non_extreme_minimizers(self):
        result = solve_linear_fraction_attack((0.5, 0.5), (1.0, 1.0),
                                              (1.0, 1.0), 3.0)
        self.assertEqual(result["objective"], -math.inf)
        # (1,1/4)=.5*(1,0)+.5*(1,1/2) is non-extreme and also -inf.
        non_extreme = linear_fraction_objective((1.0, 0.25), (0.5, 0.5), (1.0, 1.0))
        self.assertEqual(non_extreme, -math.inf)
        self.assertIn("strictly positive-retention", result["proof"]["extreme_point_argument"])
        self.assertIn("zero-retention is handled separately", result["proof"]["extreme_point_argument"])

    def test_T_R14_PROOF_defense_funded_unfunded_and_ties(self):
        # Unique funded maximum with a donor: a transfer reduces the maximum.
        self.assertFalse(defense_equalization_necessary((0.8, 0.4), (0.5, 0.5), 1.0))
        # A strict unfunded maximum can be funded by a transfer: not optimal either.
        self.assertFalse(defense_equalization_necessary((0.4, 0.8), (1.0, 0.0), 1.0))
        # Non-strict maxima need no equalization of the smaller entries.
        self.assertTrue(defense_equalization_necessary((0.8, 0.8, 0.1), (0.4, 0.4, 0.2), 1.0))
        # One funded channel is trivially equalized over the funded set.
        self.assertTrue(defense_equalization_necessary((0.8, 0.4), (1.0, 0.0), 1.0))
        # Flat maximal response: split allocation can be optimal despite a
        # unique strict maximum, so responsiveness is indispensable.
        self.assertTrue(defense_equalization_necessary((2.0, 1.0), (0.5, 0.5),
                                                        1.0, responsive=False))


class R14InformationAndScale(unittest.TestCase):
    def test_T_R14_REF_differential_entropy_ratio_is_not_bounded(self):
        var_theta, var_noise = 100.0, 0.01
        h = 0.5 * math.log(2.0 * math.pi * math.e * var_theta)
        mutual = 0.5 * math.log1p(var_theta / var_noise)
        self.assertAlmostEqual(h, 3.721523626198718)
        self.assertAlmostEqual(mutual, 4.6052201834882585)
        self.assertAlmostEqual(mutual / h, 1.2374555816516946)
        self.assertGreater(mutual / h, 1.0)
        # Negative differential entropy can occur too; neither case enters A_ref.
        h_small = 0.5 * math.log(2.0 * math.pi * math.e * 0.01)
        self.assertLess(h_small, 0.0)

    def test_T_R14_REF_finite_discrete_fidelity_stays_in_unit_interval(self):
        rng = make_rng(910164)
        for _ in range(30):
            joint = rng.random((4, 3))
            joint /= joint.sum()
            h = entropy_nats(joint.sum(axis=1))
            fidelity = mi_nats(joint) / h
            self.assertGreaterEqual(fidelity, -1e-12)
            self.assertLessEqual(fidelity, 1.0 + 1e-12)
            result = truth_A_ref(joint, p_endorse=0.7, lam_ref=0.8)
            self.assertGreaterEqual(result.point, 0.0)
            self.assertLessEqual(result.point, 1.0)

    def test_T_R14_REF_wiring_does_not_turn_degenerate_interval_into_point(self):
        cfg = Env0Config(ensemble_joint=((1.0, 0.0), (0.0, 0.0)))
        with self.assertRaisesRegex(ValueError, "point is undefined"):
            _truth_a_ref(cfg, 1.0)
        interval = truth_A_ref(((1.0, 0.0), (0.0, 0.0)), p_endorse=0.7, lam_ref=0.8)
        self.assertTrue(interval.degenerate)
        self.assertIsNone(interval.point)
        self.assertAlmostEqual(interval.hi, 0.56)

    def test_T_R14_SCALE_distance_ratio_invariance_does_not_license_ratio_readings(self):
        # d -> a*d leaves d/dc invariant, but A_goal -> a*A_goal is a
        # different transformation, not the one induced by that rescaling.
        d, dc, multiplier = 0.4, 1.0, 3.0
        self.assertAlmostEqual((multiplier * d) / (multiplier * dc), d / dc)
        self.assertNotAlmostEqual(1.0 - (multiplier * d) / (multiplier * dc),
                                  multiplier * (1.0 - d / dc))
        x, y = (0.9, 0.2), (0.5, 0.6)
        base_x = math.sqrt(x[0] * x[1])
        base_y = math.sqrt(y[0] * y[1])
        transformed_x = math.sqrt(x[0] ** 2 * x[1])
        transformed_y = math.sqrt(y[0] ** 2 * y[1])
        self.assertGreater(base_y, base_x)
        self.assertGreater(transformed_x, transformed_y)

    def test_T_R14_PROOF_conditioning_can_increase_mutual_information(self):
        # X,Y fair independent bits, Z=X xor Y: I(X;Y)=0, I(X;Y|Z)=ln2.
        joint = np.zeros((2, 2, 2))
        for x in (0, 1):
            for y in (0, 1):
                joint[x, y, x ^ y] = 0.25
        unconditional = mi_nats(joint.sum(axis=2))
        conditional = 0.0
        for z in (0, 1):
            slice_z = joint[:, :, z]
            conditional += slice_z.sum() * mi_nats(slice_z / slice_z.sum())
        self.assertAlmostEqual(unconditional, 0.0)
        self.assertAlmostEqual(conditional, math.log(2.0))

    def test_T_R14_PROOF_via_independence_does_not_derive_gate_or_geometric_form(self):
        rng = make_rng(910165)
        via = rng.random(100)
        d1 = rng.random(100)
        d2 = rng.random(100)
        # The registered construction is independent by design, yet both
        # aggregators are compatible with those same marginals/independence.
        self.assertEqual(len({tuple(v) for v in np.column_stack((via, d1, d2))}), 100)
        geometric = via * np.sqrt((1.0 - d1) * (1.0 - d2))
        non_geometric = via * (1.0 - 0.5 * (d1 + d2))
        self.assertFalse(np.allclose(geometric, non_geometric))

    def test_T_R14_PROOF_script_claim_requires_complete_state_and_noise_control(self):
        # Even with G,pi known and B,O controlled, an unobserved independent M
        # changes A=pi(G,B,M,R)=M xor B.  No single deterministic script in
        # (B,O) represents both worlds with small TV.
        distributions = {m: np.array([float((m ^ b) == a) for b in (0, 1) for a in (0, 1)])
                         for m in (0, 1)}
        # Compare action laws conditioned on the same B=0.
        p_m0 = np.array([1.0, 0.0])
        p_m1 = np.array([0.0, 1.0])
        self.assertEqual(0.5 * float(np.abs(p_m0 - p_m1).sum()), 1.0)


class R14CounterfactualLambda(unittest.TestCase):
    def test_T_R14_LAMBDA_history_and_output_deviation_are_distinct(self):
        scm = ThresholdEndorsementSCM("gaussian", a=0.35, b=0.0)
        x = np.array([0.0, 1.0, 0.0, 1.0])
        j = np.ones(4)
        z = scm.a * x
        estimate = scm.evaluate(x, z, j)
        self.assertEqual(estimate.surgery_history, 1)
        self.assertAlmostEqual(estimate.lam, 1.0)
        self.assertAlmostEqual(estimate.mean_tv, 0.0)

    def test_T_R14_LAMBDA_abduction_action_prediction_two_noise_closed_forms(self):
        for noise, cdf_at_one in (("gaussian", 0.8413447460685429),
                                  ("logistic", 0.7310585786300049)):
            scm = ThresholdEndorsementSCM(noise, a=0.0, b=1.0)
            x, z, j = np.array([0.0]), np.array([1.0]), np.array([1.0])
            self.assertAlmostEqual(float(scm.abduct(x, z, j)[0]), 0.0)
            self.assertAlmostEqual(float(scm.action_remove_surgery(
                x, scm.abduct(x, z, j))[0]), 0.0)
            estimate = scm.evaluate(x, z, j)
            self.assertAlmostEqual(estimate.lam, 1.5 - cdf_at_one)
            self.assertGreater(estimate.lam, 0.0)
            self.assertLess(estimate.lam, 1.0)

    def test_T_R14_LAMBDA_xor_nondegenerate_boundary_witness(self):
        u = np.array([0, 1, 0, 1])
        implanted = xor_endorsement_audit(u, np.ones(4, dtype=int))
        endogenous = xor_endorsement_audit(u, np.zeros(4, dtype=int))
        self.assertEqual(implanted.lam, 0.0)
        self.assertEqual(endogenous.lam, 1.0)
        self.assertEqual(implanted.surgery_history, 1)
        self.assertEqual(endogenous.surgery_history, 0)
        self.assertEqual(len(set((u ^ 1).tolist())), 2)  # nondegenerate across contexts

    def test_T_R14_LAMBDA_xor_abduction_and_observation_equivalence(self):
        y = np.array([1, 0, 1, 0])  # factual implanted Y=U xor 1
        j = np.ones(4, dtype=int)
        estimate = xor_endorsement_audit_from_observations(y, j)
        self.assertEqual(estimate.lam, 0.0)
        identity = identity_endorsement_audit(np.array([0, 1, 0, 1]), j)
        self.assertEqual(identity.lam, 1.0)
        self.assertEqual(identity.surgery_history, 1)
        witness = observation_equivalent_xor_witness((0, 1, 0, 1))
        self.assertEqual(witness["identity_p_y1"], 0.5)
        self.assertEqual(witness["xor_p_y1"], 0.5)
        self.assertEqual(witness["identity"].lam, 1.0)
        self.assertEqual(witness["xor"].lam, 0.0)
        self.assertTrue(np.array_equal(witness["identity_passive_action"],
                                       witness["xor_passive_action"]))

    def test_T_R14_LAMBDA_strong_dominates_weak_pointwise_and_guards(self):
        for noise in ("gaussian", "logistic"):
            weak = ThresholdEndorsementSCM(noise, a=0.35, b=0.35)
            strong = ThresholdEndorsementSCM(noise, a=0.35, b=1.0)
            x = np.array([0.0, 1.0, 0.0, 1.0])
            u = np.array([-1.2, -0.3, 0.4, 1.5])
            j = np.ones(4)
            z_weak = weak.a * x + weak.b * j + u
            z_strong = strong.a * x + strong.b * j + u
            self.assertTrue(np.all(strong.tv_per_context(x, z_strong, j)
                                   >= weak.tv_per_context(x, z_weak, j) - 1e-15))
            with self.assertRaises(ValueError):
                weak.evaluate(np.array([0.5]), np.array([0.0]), np.array([1.0]))
            with self.assertRaises(ValueError):
                weak.evaluate(np.array([0.0]), np.array([np.nan]), np.array([1.0]))
            with self.assertRaises(ValueError):
                xor_endorsement_audit_from_observations(np.array([]), np.array([]))

    def test_T_R14_PROOF_full_state_script_positive_and_negative_controls(self):
        # Positive control: full decision-time state is reconstructible and
        # the policy is deterministic, so the external script is exact.
        for g in (0, 1):
            for b in (0, 1):
                for m in (0, 1):
                    for r in (0, 1):
                        state = (g, b, m, r)
                        action = (g + b + m + r) % 2
                        reconstructed = (state[0] + state[1] + state[2] + state[3]) % 2
                        self.assertEqual(action, reconstructed)
        # Negative control: dropping M from the same sufficient state fails.
        b, m0, m1 = 0, 0, 1
        self.assertNotEqual(b ^ m0, b ^ m1)


class R14NumericalBoundary(unittest.TestCase):
    def test_T_R14_CLIP_shared_tolerance_records_and_clips(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            self.assertEqual(clip_unit_value(-4.49e-17), 0.0)
            self.assertEqual(clip_unit_value(1.0 + 2e-17), 1.0)
            self.assertEqual(a_exec(-4.49e-17, 1, 5), 0.0)
            composite_A(1.0, (0.5, -4.49e-17), (0.5, 0.5), 1.0)
        self.assertGreaterEqual(len([w for w in caught
                                     if issubclass(w.category, NumericalBoundaryWarning)]), 3)
        with self.assertRaises(ValueError):
            clip_unit_value(-2e-9)
        with self.assertRaises(ValueError):
            clip_unit_value(float("nan"))


if __name__ == "__main__":
    unittest.main()
