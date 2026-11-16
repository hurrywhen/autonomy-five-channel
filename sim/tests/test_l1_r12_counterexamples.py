"""R12 审稿反例回归（SPEC_tests T-R12-*）。

钉住命题量词、T7(iv) 的诚实前提和 T8(ii) 的逐参数方向；
数值测试不是对完整顺序检测或委托模型的形式化认证。
"""
import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim import aggregate, dynamics  # noqa: E402


class TestR12DetectionQuantifiers(unittest.TestCase):
    def test_T_R12_DET_constant_stop_defeats_fixed_alpha_weak_drift(self):
        for alpha in (0.5, 0.2, 0.1, 0.05):
            k = math.ceil(1.0 / alpha)
            # T≡K 是合法停止规则，E∞[T]=K≥1/α，Lorden 延迟至多 K。
            self.assertGreaterEqual(k, 1.0 / alpha)
            damages = [delta * k for delta in (0.1, 0.01, 0.001, 0.0001)]
            self.assertTrue(all(x > y for x, y in zip(damages, damages[1:])))
            self.assertLess(damages[-1], 0.01)
            # 即使要求依赖观测，T=K+1{X1>0} 的延迟也至多 K+1。
            delayed = [delta * (k + 1) for delta in (0.1, 0.01, 0.001, 0.0001)]
            self.assertLess(delayed[-1], 0.01)


class TestR12DefenseMonotonicity(unittest.TestCase):
    def test_T_R12_T8_lowering_theta_lowers_delta_star_and_raises_floor(self):
        # W=1、κ=2、冗余项 slack；θ:0.8→0.4 时 δ*:0.8→0.4。
        common = dict(W=1.0, kappa=2.0, r=1.0, c0=5.0)
        ds_hi = dynamics.delta_star(theta=0.8, **common)
        ds_lo = dynamics.delta_star(theta=0.4, **common)
        self.assertAlmostEqual(ds_hi, 0.8, places=12)
        self.assertAlmostEqual(ds_lo, 0.4, places=12)
        am_hi = dynamics.a_min(0.9, (1.0,), (1.0,), (ds_hi,), (2.0,))
        am_lo = dynamics.a_min(0.9, (1.0,), (1.0,), (ds_lo,), (2.0,))
        self.assertLess(ds_lo, ds_hi)
        self.assertGreater(am_lo, am_hi)

    def test_T_R12_T8_redundancy_can_raise_delta_star_and_lower_floor(self):
        # κ=10、c0=W=1、θ/W≥2；r:1→2 使冗余项 1→2。
        ds1 = dynamics.delta_star(theta=2.0, W=1.0, kappa=10.0, r=1.0, c0=1.0)
        ds2 = dynamics.delta_star(theta=2.0, W=1.0, kappa=10.0, r=2.0, c0=1.0)
        am1 = dynamics.a_min(0.9, (1.0,), (1.0,), (ds1,), (10.0,))
        am2 = dynamics.a_min(0.9, (1.0,), (1.0,), (ds2,), (10.0,))
        self.assertAlmostEqual(ds1, 1.0, places=12)
        self.assertAlmostEqual(ds2, 2.0, places=12)
        self.assertAlmostEqual(am1, 0.9 * 0.9, places=12)
        self.assertAlmostEqual(am2, 0.9 * 0.8, places=12)
        self.assertLess(am2, am1)

    def test_T_R12_T8_repair_capacity_control_remains_valid(self):
        # 注册的 κ-improvement 臂：κ 跨过 binding 边界，两个量可以同升。
        ds0 = dynamics.delta_star(0.5, 2.0, 0.2, 2.0, 0.4)
        ds1 = dynamics.delta_star(0.5, 2.0, 0.3, 2.0, 0.4)
        am0 = dynamics.a_min(0.9, (0.8,), (1.0,), (ds0,), (0.2,))
        am1 = dynamics.a_min(0.9, (0.8,), (1.0,), (ds1,), (0.3,))
        self.assertGreater(ds1, ds0)
        self.assertGreater(am1, am0)

    def test_T_R12_T8_strict_composite_loss_requires_positive_baseline(self):
        # off-Fix 距离或任一通道严格下降，若另一因子基线已为零，复合仍可保持 0。
        weights = (0.5, 0.5)
        a0_zero = aggregate.composite_A(0.0, (0.5, 1.0), weights, 1.0)
        a1_zero = aggregate.composite_A(0.0, (0.25, 1.0), weights, 1.0)
        self.assertEqual(a0_zero, 0.0)
        self.assertEqual(a1_zero, 0.0)
        a0_positive = aggregate.composite_A(1.0, (0.5, 1.0), weights, 1.0)
        a1_positive = aggregate.composite_A(1.0, (0.25, 1.0), weights, 1.0)
        self.assertGreater(a0_positive, 0.0)
        self.assertLess(a1_positive, a0_positive)


class TestR12DelegationAndInformation(unittest.TestCase):
    def test_T_R12_T7_transparency_does_not_imply_accuracy(self):
        # 透明、可逆、可背书只描述路径；虚假的 α 内容仍可让真实桶质量 1→0。
        transparent = reversible = endorsable = True
        q = float(transparent) * float(reversible) * float(endorsable)
        self_mass_before, self_mass_after = 1.0, 0.0
        self.assertEqual(q, 1.0)
        self.assertLess(self_mass_after, self_mass_before)

    def test_T_R12_EPI_zero_prior_mass_is_not_strictly_improved(self):
        # B(k)=0 时即使 q_e≠p，后验真实桶质量仍为 0；严格结论需 0<B(k)<1。
        b = 0.0
        p_k = np.array([0.8, 0.2])
        p_not = np.array([0.2, 0.8])
        predictive = b * p_k + (1.0 - b) * p_not
        self.assertTrue(np.all((predictive > 0) | (p_k == 0)))  # support coverage
        posterior = np.divide(b * p_k, predictive, out=np.zeros(2), where=predictive > 0)
        expected = float(p_k @ posterior)
        self.assertEqual(expected, b)
        self.assertFalse(np.array_equal(p_k, predictive))

    def test_T_R12_COPULA_jensen_lower_bound_is_generally_non_sharp(self):
        # A1∈{1,2}、A2∈{1,3} 均均匀且非退化。四个联合乘积 1,2,3,6 全不同；
        # 若 (log A1+log A2)/2 在 support 上恒定，则 A1A2 恒定，support 至多一格，
        # 与两个非退化边际矛盾。因此该例中 Jensen 等号对任何 copula 都不成立。
        a1 = np.array([1.0, 2.0])
        a2 = np.array([1.0, 3.0])
        products = np.outer(a1, a2)
        self.assertEqual(len(set(products.ravel())), 4)
        g1 = math.exp(float(np.log(a1).mean()))
        g2 = math.exp(float(np.log(a2).mean()))
        jensen_lower = math.sqrt(g1 * g2)
        self.assertAlmostEqual(jensen_lower, 6.0 ** 0.25, places=12)
        # 同序（comonotone）耦合给出严格大于下端的期望。
        comonotone_mean = 0.5 * (math.sqrt(1.0) + math.sqrt(6.0))
        self.assertGreater(comonotone_mean, jensen_lower)
        # 旧对称例 A2=1/A1 反而达到等号，不能再用于证明非可达性。
        symmetric = np.array([math.exp(-1.0), math.exp(1.0)])
        self.assertAlmostEqual(float((symmetric * (1.0 / symmetric))[0]), 1.0, places=12)


if __name__ == "__main__":
    unittest.main()
