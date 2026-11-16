"""R13 审稿反例回归（SPEC_tests T-R13-*）。

钉住 T6 上比较不能推出俘获、C0 注册映射不能支持完整画像相等、
L1 非退化分离证人、注册域方向及 D1/Aepi 口径。数值测试不是 Lean 认证。
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim import dynamics  # noqa: E402


class TestR13T6UpperComparison(unittest.TestCase):
    def test_T_R13_T6_zero_damage_satisfies_band_but_is_not_captured(self):
        # kappa<delta<theta/W 的 certificate-failure band 内，D(t)=0 始终合法。
        kappa, delta, theta_over_w = 0.1, 0.15, 0.2
        self.assertTrue(kappa < delta < theta_over_w)
        for _ in range(100):
            damage = 0.0
            derivative = 0.0
            self.assertLessEqual(derivative, delta - kappa * damage)
            self.assertLess(delta * 2.0, 0.4)  # 本例 W=2、theta=0.4，M1 不触发
        self.assertEqual(damage, 0.0)
        self.assertNotEqual(damage, 1.0)

    def test_T_R13_T6_same_upper_bound_admits_zero_and_saturating_trajectories(self):
        # 零轨迹与精确饱和轨迹都满足同一上比较式，故该式本身不确定实际轨迹。
        kappa, delta = 0.2, 0.3
        for damage in (0.0, 0.2, 0.8):
            zero_derivative = 0.0
            saturating_derivative = delta - kappa * damage
            self.assertLessEqual(zero_derivative, delta - kappa * damage)
            self.assertLessEqual(saturating_derivative, delta - kappa * damage)
        _, saturated, registrations = dynamics.simulate_damage(
            lambda t: delta, kappa, T=30.0, dt=0.01, theta=0.8, W=2.0, lag=0.1)
        self.assertEqual(registrations, 0)
        self.assertGreater(saturated[-1], 0.999)


class TestR13C0Mappings(unittest.TestCase):
    def test_T_R13_C0_dung_and_kg_profiles_can_change(self):
        # Dung: acting_for_reasons=Aepi*Aref；Aepi 下降且 Aref>0 不变时必变。
        a_ref = 0.8
        self.assertNotEqual(1.0 * a_ref, 0.5 * a_ref)
        # KG: F=Aorg^w1*Agoal^w2*Aref^w3 严格递增；Lambda 经 Aref 下降时必变。
        a_org, a_goal = 0.9, 0.8
        weights = (0.2, 0.3, 0.5)

        def kg(a_ref_value):
            return ((a_org ** weights[0]) * (a_goal ** weights[1])
                    * (a_ref_value ** weights[2]))

        self.assertLess(kg(0.0), kg(0.8))

    def test_T_R13_C0_nondegenerate_l1_witness_separates_without_full_profile_claim(self):
        # L1 无 Aref 复合入口；仅 Aepi:1→0.5 改变，Lambda 是额外的 composite-silent 证据。
        a_z1 = 0.37447724184027475
        w_epi = 0.2
        a_z2 = a_z1 * 0.5 ** w_epi
        # Z1 常量真桶+忠实信念精度 1；Z2 公平真桶+独立钉住信念精度恰为 1/2。
        true_z1, belief_z1 = 0, 0
        self.assertEqual(true_z1, belief_z1)
        fair_truth = (0, 1)
        pinned_belief = (1, 1)
        accuracy_z2 = sum(int(e == b) for e, b in zip(fair_truth, pinned_belief)) / 2
        self.assertEqual(accuracy_z2, 0.5)
        # 解析证人的代数核验（不是 C0-DEMO 可执行反事实实现）：非退化背书下，
        # 实际/无手术反事实律逐时 TV=1 直接给 Lambda=0；不用 Endorse=id 退化约定。
        surgery_present, endorsement_nondegenerate = True, True
        actual_counterfactual_tvs = (1.0, 1.0, 1.0)
        self.assertTrue(surgery_present and endorsement_nondegenerate)
        lambda_z2 = 1.0 - sum(actual_counterfactual_tvs) / len(actual_counterfactual_tvs)
        lambda_z1 = 1.0  # 空手术史约定
        passive_behavior_z1 = passive_behavior_z2 = (0.25, 0.25, 0.25, 0.25)
        self.assertEqual(passive_behavior_z1, passive_behavior_z2)
        self.assertGreater(a_z1, 0.0)
        self.assertGreater(a_z2, 0.0)
        self.assertLess(a_z2, a_z1)
        self.assertNotEqual(lambda_z1, lambda_z2)


class TestR13ScopeAndDirections(unittest.TestCase):
    def test_T_R13_T6_pointwise_floor_requires_viability_factor(self):
        # 单通道、无损伤、A_base=1，但 A_via=1/2：pointwise floor 必须含 A_via^min，不能为 1。
        a_via_min, a_base, weight = 0.5, 1.0, 1.0
        bar_delta, kappa = 0.0, 1.0
        floor = a_via_min * (a_base * (1.0 - bar_delta / kappa)) ** weight
        actual_liminf = a_via_min * a_base ** weight
        self.assertEqual(floor, 0.5)
        self.assertEqual(actual_liminf, 0.5)

    def test_T_R13_T6_positive_floor_requires_nondegenerate_baseline(self):
        # 即使 kappa 不 binding 且 A_via^min>0，A_base=0 仍使 floor 为 0；故需 H4''。
        floor = dynamics.a_min(0.9, (0.0,), (1.0,), (0.2,), (0.5,))
        self.assertEqual(floor, 0.0)
        positive = dynamics.a_min(0.9, (0.8,), (1.0,), (0.2,), (0.5,))
        self.assertGreater(positive, 0.0)

    def test_T_R13_T6_m1_registration_alone_is_not_retention_certificate(self):
        # delta>=theta/W 只给注册；theta+ell*delta 超过俘获阈时不能推出非俘获。
        theta, w, lag, delta = 0.4, 2.0, 0.1, 20.0
        self.assertGreaterEqual(delta, theta / w)
        self.assertGreater(theta + lag * delta, 1.0)
        # 满足阈值时也只有 per-channel 正下界；另一因子为零仍可使全复合为零。
        small_delta = 0.5
        component_floor = 1.0 * (1.0 - theta - lag * small_delta)
        self.assertGreater(component_floor, 0.0)
        other_channel_factor = 0.0
        self.assertEqual(component_floor * other_channel_factor, 0.0)

    def test_T_R13_T6_raising_theta_shrinks_registration_domain(self):
        w = 2.0
        theta_lo, theta_hi = 0.2, 0.4
        domain_lo = {delta: None for delta in (0.05, 0.1, 0.15, 0.2, 0.25)
                     if delta >= theta_lo / w}
        domain_hi = {delta: None for delta in (0.05, 0.1, 0.15, 0.2, 0.25)
                     if delta >= theta_hi / w}
        self.assertTrue(set(domain_hi).issubset(set(domain_lo)))
        self.assertTrue(set(domain_hi) < set(domain_lo))

    def test_T_R13_EPI_orthogonal_noise_does_not_imply_coordinate_accuracy_loss(self):
        # D1 作用于 execution；只扰动与 kappa(E) 正交的资源坐标，注册桶可始终完全准确。
        states = ((0, 0), (0, 1), (1, 0), (1, 1))  # (position, resource)
        noisy_states = ((0, 1), (0, 0), (1, 1), (1, 0))
        kappa = lambda state: state[0]
        accuracy = sum(kappa(e) == kappa(obs) for e, obs in zip(states, noisy_states)) / len(states)
        self.assertEqual(accuracy, 1.0)
        self.assertNotEqual(states, noisy_states)


if __name__ == "__main__":
    unittest.main()
