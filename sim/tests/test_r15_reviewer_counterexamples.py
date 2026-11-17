"""R15 reviewer counterexamples and construct/output guards.

Deterministic mathematical checks only.  They neither rewrite historical
archives nor constitute independent-substrate construct validation.
"""
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim.aggregate import composite_A  # noqa: E402
from autonomy_sim.di import mi_nats
from autonomy_sim.dynamics import c2_r, c2_roots
from autonomy_sim.empowerment import a_exec, empowerment_support
from autonomy_sim.logschema import validate_r15_certificate, write_r15_certificate
from autonomy_sim.r15_guards import (c2_recovery_threshold,
                                     componentwise_compatible,
                                     goal_from_distance,
                                     goal_interval_from_distances,
                                     internal_causal_org, make_audit_certificate,
                                     normative_org, produce_r15_certificate,
                                     state_defense_split)
from autonomy_sim.stats import kendall_tau_b, paired_mean_se


class R15ExecutionNormalization(unittest.TestCase):
    def test_T_R15_EXEC_two_bits_require_two_action_horizon(self):
        # R14's A_{t:t+1} contains two independent fair bits, so dividing by
        # 1*log(2) gives the unbounded value 2.  Clipping would hide, not fix,
        # the indexing error.  R15 uses n=2 for those two actions.
        old_raw_ratio = (2.0 * math.log(2.0)) / (1.0 * math.log(2.0))
        self.assertEqual(old_raw_ratio, 2.0)
        with self.assertRaises(ValueError):
            a_exec(2.0 * math.log(2.0), n=1, n_A=2)
        self.assertEqual(a_exec(2.0 * math.log(2.0), n=2, n_A=2), 1.0)

    def test_T_R15_EXEC_zero_can_be_environment_decoupling_not_repertoire_collapse(self):
        # Both actions remain accessible, but the observation channel is the
        # same for each action: full repertoire, zero actionable coupling.
        channel = np.array([[0.5, 0.5], [0.5, 0.5]])
        self.assertEqual(empowerment_support(channel, (0, 1)), 0.0)


class R15CompatibilityCounterexamples(unittest.TestCase):
    def test_T_R15_T2_baseline_lambda_below_one_can_remain_compatible(self):
        before = {"org": 0.8, "goal": 0.7, "exec": 0.9, "epi": 0.6,
                  "Lambda": 0.5}
        after = dict(before)
        self.assertTrue(componentwise_compatible(before, after))
        # The retired four-track shortcut would reject this compatible case
        # merely because Lambda is not absolutely equal to one.
        self.assertNotEqual(after["Lambda"], 1.0)

    def test_T_R15_T2_honest_information_can_shift_fix_and_lower_goal(self):
        # F_ext=0, sound epistemic improvement and unchanged Lambda do not
        # control endorsement fixed points.  B changes Fix from {U_eff} to a
        # disjoint point; with fixed d_c=1 the goal channel falls.
        goal_before = goal_from_distance(0.0, 1.0)
        goal_after = goal_from_distance(0.4, 1.0)
        before = {"org": 1.0, "goal": goal_before, "exec": 1.0, "epi": 0.5,
                  "Lambda": 0.5}
        after = {"org": 1.0, "goal": goal_after, "exec": 1.0, "epi": 0.7,
                 "Lambda": 0.5}
        self.assertGreater(after["epi"], before["epi"])
        self.assertFalse(componentwise_compatible(before, after))

    def test_T_R15_T2_blindness_is_an_action_independent_witness_not_general_rule(self):
        # E and O are action-independent, B updates only from (B,O).  Execute
        # two different policy/action-support sequences and compare the witness.
        def action_independent(actions):
            environment = (0, 1, 1, 0)
            observation = tuple(environment)
            belief = []
            b = 0
            for obs in observation:
                b = obs
                belief.append(b)
            return environment, observation, tuple(belief)
        self.assertEqual(action_independent((0, 0, 0, 0)),
                         action_independent((1, 1, 1, 1)))
        # The same observation kernel O=E is not enough when E depends on A.
        def action_coupled(actions):
            environment = (0, *actions[:-1])
            return tuple(environment)
        self.assertNotEqual(action_coupled((0, 0, 0, 0)),
                            action_coupled((1, 1, 1, 1)))
        # A different environment with E_{t+1}=A_t would invalidate the old
        # general assertion even if the conditional observation kernel stayed
        # fixed; no universal blindness claim is made.  F_ext=0 also does not
        # freeze the R15 ratio when normative/innovation flows move.
        before = normative_org(1.0, 0.0, 0.0)
        after = normative_org(0.5, 0.5, 0.0)
        self.assertLess(after, before)


class R15NormativeSourceAndGoalIdentification(unittest.TestCase):
    def test_T_R15_RANDOM_L0_high_internal_causal_score_is_not_normative_autonomy(self):
        org_l0 = internal_causal_org(math.log(2.0), 0.0)
        old_l0 = composite_A(1.0, (org_l0, 1.0), (0.5, 0.5), 1.0)
        self.assertEqual(old_l0, 1.0)
        # At L1+, construct the actual N,R,A joint law: N is constant, R is
        # fair, and A=R.  Compute the one-step R,N chain rather than merely
        # supplying hand-selected flow values.
        joint = np.zeros((2, 2, 2))
        for r in (0, 1):
            joint[0, r, r] = 0.5
        f_rand = mi_nats(joint.sum(axis=0))
        f_norm = 0.0
        for r in (0, 1):
            conditional = joint[:, r, :]
            f_norm += conditional.sum() * mi_nats(conditional / conditional.sum())
        self.assertAlmostEqual(f_rand, math.log(2.0))
        self.assertEqual(f_norm, 0.0)
        org_norm = normative_org(f_norm, f_rand, 0.0)
        self.assertEqual(org_norm, 0.0)
        guarded = composite_A(1.0, (org_norm, 1.0), (0.5, 0.5), 1.0)
        self.assertEqual(guarded, 0.0)
        with self.assertRaises(ValueError):
            normative_org(0.0, 0.0, 0.0)

    def test_T_R15_RANDOM_L1_normative_policy_positive_control(self):
        joint = np.zeros((2, 2, 2))
        for n in (0, 1):
            for r in (0, 1):
                joint[n, r, n] = 0.25  # independent fair N,R; A=N
        f_rand = mi_nats(joint.sum(axis=0))
        f_norm = 0.0
        for r in (0, 1):
            conditional = joint[:, r, :]
            f_norm += conditional.sum() * mi_nats(conditional / conditional.sum())
        self.assertEqual(f_rand, 0.0)
        self.assertAlmostEqual(f_norm, math.log(2.0))
        self.assertEqual(normative_org(f_norm, f_rand, 0.0), 1.0)

    def test_T_R15_GOAL_structural_read_point_vs_irl_identified_set(self):
        self.assertEqual(goal_from_distance(0.2, 1.0), 0.8)
        lo, hi = goal_interval_from_distances((0.2, 0.4, 0.3), 1.0)
        self.assertEqual((lo, hi), (0.6, 0.8))
        self.assertLess(lo, hi)
        # Additive shifts are not free symmetries: with Theta=[0,1],
        # Fix={0.2}, U_eff=0.8, d_c=0.8 and A_goal=0.25.  Shifting only
        # U_eff by 0.1 changes it to 0.125; shifting Fix without translating
        # the domain also changes d_c.  Only a joint domain translation works.
        self.assertAlmostEqual(goal_from_distance(0.6, 0.8), 0.25)
        self.assertAlmostEqual(goal_from_distance(0.7, 0.8), 0.125)
        self.assertAlmostEqual(goal_from_distance(0.6, 0.7), 1.0 / 7.0)
        self.assertAlmostEqual(goal_from_distance(0.6, 0.8), 0.25)  # joint +0.1 translation

    def test_T_R15_GOAL_fixed_point_theorem_premises_not_interchangeable(self):
        # Compact convex domain alone is insufficient without continuity:
        # f(0)=1 and f(x)=0 for x>0 has no fixed point on [0,1].
        grid = np.linspace(0.0, 1.0, 1001)
        values = np.where(grid == 0.0, 1.0, 0.0)
        self.assertTrue(np.all(values != grid))


class R15ScopeAndProofGuards(unittest.TestCase):
    def test_T_R15_C2_recovery_threshold_separates_zero_and_positive_attack(self):
        s_c = 0.2347
        self.assertEqual(c2_recovery_threshold(0.0, s_c), s_c)
        self.assertAlmostEqual(c2_recovery_threshold(0.1, s_c), 0.3347)
        gamma = 2.0
        _, d_m = c2_roots(gamma)
        recovery = c2_r(1.0, gamma)
        s_c_actual = abs(recovery(d_m))
        delta = 0.1
        grid = np.linspace(1.0 / gamma + 1e-7, 1.0 - 1e-7, 2000)
        sufficient = delta + s_c_actual + 1e-9
        self.assertTrue(np.all(delta - recovery(grid) - sufficient < 0.0))
        # At D_m and s=s_c, persistent delta leaves a positive derivative;
        # with delta=0 the equality point is not strict descent either.
        self.assertGreater(delta - recovery(d_m) - s_c_actual, 0.0)
        self.assertEqual(-recovery(d_m) - s_c_actual, 0.0)
        spec = (Path(__file__).resolve().parents[1] / "SPEC_estimators.md").read_text(
            encoding="utf-8")
        self.assertIn("恢复须 $s>\\delta+s_c$", spec)

    def test_T_R15_VIABILITY_defense_zero_does_not_erase_current_state_autonomy(self):
        result = state_defense_split(0.8, resource_ratios=(1.0, 0.9),
                                     defense_margins=(0.0,))
        self.assertAlmostEqual(result["state_autonomy"], 0.72)
        self.assertEqual(result["defense_readiness"], 0.0)
        self.assertEqual(result["defense_adjusted_autonomy"], 0.0)
        self.assertGreater(result["state_autonomy"], 0.0)
        with self.assertRaises(ValueError):
            state_defense_split(0.8, resource_ratios=(1.0,), defense_margins=())

    def test_T_R15_OUTPUT_history_lambda_source_and_unknown_cap_are_mandatory(self):
        cert = make_audit_certificate(
            layer="L2", state_autonomy=0.95, viability_state=1.0,
            defense_readiness=0.2, surgery_history=None, lambda_value=1.0,
            lambda_status="DEFINED", source_registration="UNKNOWN")
        for key in ("surgery_history", "Lambda", "lambda_status", "source_registration",
                    "defense_readiness", "evidence_ceiling"):
            self.assertIn(key, cert)
        self.assertEqual(cert["evidence_ceiling"], "LIMITED")
        self.assertFalse(cert["integrity_certificate"])
        self.assertFalse(cert["external_construct_validation"])
        produced = produce_r15_certificate(
            layer="L1", channels=(1.0, 0.8, 0.9, 0.7), weights=(0.25,) * 4,
            resource_ratios=(1.0,), defense_margins=(0.0,), surgery_history=0,
            lambda_value=None, lambda_status="NOT_APPLICABLE",
            source_registration="COMPLETE")
        self.assertEqual(produced["lambda_status"], "NOT_APPLICABLE")
        self.assertEqual(produced["evidence_ceiling"], "SCM_AUDITED")
        self.assertGreater(produced["state_autonomy"], 0.0)
        self.assertEqual(produced["defense_readiness"], 0.0)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "certificate.json")
            write_r15_certificate(path, produced)
            loaded = json.loads(Path(path).read_text(encoding="utf-8"))
            self.assertEqual(validate_r15_certificate(loaded), [])
        unknown = produce_r15_certificate(
            layer="L1", channels=(1.0, 0.8, 0.9, 0.7), weights=(0.25,) * 4,
            resource_ratios=(1.0,), defense_margins=(1.0,), surgery_history=0,
            lambda_value=None, lambda_status="UNKNOWN", source_registration="COMPLETE")
        self.assertIsNone(unknown["Lambda"])
        self.assertEqual(unknown["evidence_ceiling"], "LIMITED")
        self.assertNotEqual(unknown["lambda_status"], produced["lambda_status"])

    def test_T_R15_ROUTE_B_nontrivial_weight_sum_has_slope_reciprocal(self):
        # If s=sum w_i, homogeneity gives phi(z+t)=phi(z)+t/s.  Normalizing
        # w first is therefore a real proof step, not a removable aside.
        w = np.array([2.0, 3.0])
        s = float(w.sum())
        normalized = w / s
        self.assertAlmostEqual(float(normalized.sum()), 1.0)
        self.assertAlmostEqual(1.0 / s, 0.2)
        z, t = 0.37, 0.19
        phi = lambda value: value / s
        self.assertAlmostEqual(phi(z + t) - phi(z), t / s)
        x = np.array([0.7, 0.9])
        scale = 2.3
        f = lambda value: float(np.prod(value ** normalized))
        self.assertAlmostEqual(f(scale * x), scale * f(x))
        # For g(u)=w.u, W={d:w.d=0}; if both q(d) and -q(d)
        # lie in the quotient cone, then w.d=0 and q(d)=0 (pointedness).
        d = np.array([3.0, -2.0])
        self.assertEqual(float(w @ d), 0.0)
        nonzero = np.array([1.0, 0.0])
        self.assertFalse(float(w @ nonzero) >= 0.0 and float(w @ (-nonzero)) >= 0.0)

    def test_T_R15_STATS_tau_b_reports_ties_and_rejects_constant_claim(self):
        result = kendall_tau_b((1.0, 1.0, 2.0, 3.0), (1.0, 2.0, 2.0, 3.0))
        self.assertEqual(result["ties_x_only"], 1)
        self.assertEqual(result["ties_y_only"], 1)
        self.assertEqual(result["ties_both"], 0)
        self.assertAlmostEqual(result["tau_b"], 0.8)
        self.assertGreater(result["tau_b"], 0.0)
        self.assertLess(result["tau_b"], 1.0)
        constant = kendall_tau_b((1.0, 1.0), (1.0, 2.0))
        self.assertTrue(math.isnan(constant["tau_b"]))
        paired = paired_mean_se((1.0, -1.0, 1.0, -1.0))
        self.assertEqual(paired["mean_difference"], 0.0)
        self.assertAlmostEqual(paired["paired_se"], math.sqrt(4.0 / 3.0) / 2.0)


if __name__ == "__main__":
    unittest.main()
