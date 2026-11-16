"""R11 审稿反例回归（SPEC_tests T-R11-*）。

这些测试钉住定理边界，不把数值通过当作证明：归一化、幂等性、局部似然、
检测分布前提、Aepi 信念质量、双误差 bracket、被动条件 MI 与连续归一化。
"""
import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim import delegation  # noqa: E402


class TestR11Representation(unittest.TestCase):
    def test_T_R11_REP_normalization_is_necessary(self):
        f = lambda x, y: 0.5 * math.sqrt(x * y)
        t, x, y = 0.2, 0.3, 0.7
        self.assertAlmostEqual(f(t * x, t * y), t * f(x, y), places=12)
        self.assertAlmostEqual(f(1.0, 1.0), 0.5, places=12)
        self.assertNotAlmostEqual(f(1.0, 1.0), 1.0, places=12)

    def test_T_R11_REP_biseparability_does_not_give_idempotency(self):
        f = lambda x, y: (x + y) / 4.0
        self.assertAlmostEqual(f(0.8, 0.8), 0.4, places=12)
        self.assertNotAlmostEqual(f(0.8, 0.8), 0.8, places=12)


class TestR11Epistemic(unittest.TestCase):
    def test_T_R11_EPI_support_coverage_counterexample(self):
        b, eps = 0.5, 0.1
        # 真观测恒 O=0；代理人 p(0|k)=eps、p(0|not k)=1-eps，支撑覆盖成立。
        predictive_o0 = b * eps + (1.0 - b) * (1.0 - eps)
        posterior = b * eps / predictive_o0
        self.assertAlmostEqual(posterior, eps, places=12)
        self.assertLess(posterior, b)
        self.assertGreater(1.0 - posterior, 1.0 - b)  # TV 到真值点质量增大

    def test_T_R11_EPI_local_likelihood_fidelity_restores_cauchy_step(self):
        b = 0.5
        p_k = np.array([0.8, 0.2])
        p_not = np.array([0.2, 0.8])
        predictive = b * p_k + (1.0 - b) * p_not
        posterior = b * p_k / predictive
        expected = float(p_k @ posterior)  # q_e=p_k：局部似然一致
        self.assertAlmostEqual(expected, 0.68, places=12)
        self.assertGreater(expected, b)

    def test_T_R11_EPI_true_bucket_mass_not_distribution_indicator(self):
        belief = np.array([0.2, 0.8])
        true_bucket = 1
        mass = belief[true_bucket]
        self.assertAlmostEqual(mass, 0.8, places=12)
        # B_t 是分布时，“分布对象等于桶标签”不是有效命中定义；点质量才是特例。
        self.assertFalse(np.array_equal(belief, np.array([0.0, 1.0])))
        point_belief = np.array([0.0, 1.0])
        self.assertAlmostEqual(point_belief[true_bucket], 1.0, places=12)


class TestR11DetectionAndExecution(unittest.TestCase):
    def test_T_R11_DET_uniform_shift_has_no_gaussian_divergence(self):
        # U[0,1]→U[δ,1+δ]：首次 X>1 即报警，几何等待 EDD=1/δ。
        for delta in (0.5, 0.25, 0.125, 0.0625):
            edd = 1.0 / delta
            self.assertAlmostEqual(delta * edd, 1.0, places=12)
        # 两分布在任意 δ>0 的支撑不互相绝对连续，KL=∞，不能套 Gaussian 展开。

    def test_T_R11_EXEC_passive_conditioning_can_increase_information(self):
        p_n = 0.25
        rows = []
        for s in (0, 1):
            for n in (0, 1):
                prob = 0.5 * (p_n if n else 1.0 - p_n)
                a = s ^ n
                o = a if s == 0 else 1 - a
                rows.append((prob, s, a, o, n))
        self.assertTrue(all(o == n for _, _, _, o, n in rows))
        p_ao = np.zeros((2, 2))
        for prob, _, a, o, _ in rows:
            p_ao[a, o] += prob
        pa, po = p_ao.sum(axis=1), p_ao.sum(axis=0)
        independent = np.outer(pa, po)
        self.assertTrue(np.allclose(p_ao, independent))  # I(A;O)=0
        h_n = -p_n * math.log(p_n) - (1.0 - p_n) * math.log(1.0 - p_n)
        conditional = 0.0
        for s in (0, 1):
            # 给定 S 后 O=N 且 A 与 N 一一对应，所以每项 MI=H(N)。
            conditional += 0.5 * h_n
        self.assertGreater(conditional, 0.0)

    def test_T_R11_EXEC_log_volume_is_not_generic_mi_bound(self):
        self.assertLess(math.log(0.5), 0.0)  # 参考体积 <1 时归一化甚至为负


class TestR11Delegation(unittest.TestCase):
    def test_T_R11_T7_two_error_counterexample_and_corrected_bracket(self):
        m = 0.1
        eta = -(1.0 - m) * math.log(1.0 - m) - m * math.log(m)
        u, v = -0.25, 0.25
        actual = (1.0 - m + u) / (1.0 - m + u + m + v)
        old_lower = (1.0 - m) / (1.0 - m + m + eta)
        self.assertAlmostEqual(actual, 0.65, places=12)
        self.assertGreater(old_lower, actual)  # 旧端点失效
        lo, hi = delegation.a_org_two_error_bracket(m, 1.0, 1.0, 0.0, 0.0, eta)
        self.assertAlmostEqual(lo, 0.5749170266085518, places=12)
        self.assertAlmostEqual(hi, 1.0, places=12)
        self.assertLessEqual(lo, actual)
        self.assertLessEqual(actual, hi)

    def test_T_R11_T7_zero_slack_recovers_legacy_bracket(self):
        lo, hi = delegation.a_org_two_error_bracket(0.4, 0.8, 1.2, 0.1, 0.1, 0.0)
        expected_lo = 0.6 / (0.6 + 0.4 * 1.2 + 0.1)
        expected_hi = 0.6 / (0.6 + 0.4 * 0.8 + 0.1)
        self.assertAlmostEqual(lo, expected_lo, places=12)
        self.assertAlmostEqual(hi, expected_hi, places=12)


if __name__ == "__main__":
    unittest.main()
