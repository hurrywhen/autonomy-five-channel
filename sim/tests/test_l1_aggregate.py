"""L1 数学性质测试：聚合模块（SPEC_tests §2 注册表 T-REP1/T-REP2/T-SIGMA/T-AX5）。

- T-REP1（附录定理 6.5/6.6）：几何聚合满足 (A1)–(A6) 的数值抽查（含 AX6b 逐坐标标度序不变）。
- T-REP2（附录命题 6.7）：反例见证——调和平均满足 (A1)–(A5) 但违反 (A6b)（注册 witness 序翻转）。
- T-SIGMA（附录 §6.5 E3）：σ=2 ⇒ p=1/2>0 ⇒ 零歼灭失效（压力测试正当性）。
- T-AX5（input AX5＝公理 (A4)）：σ 主带 [0.5,1] 内任一分量置 0 ⇒ A=0；全正值 ⇒ A>0。

σ–p 对应（附录 §6.5）：CES F_σ ↔ 幂均值指数 p=(σ−1)/σ；σ=1（p=0）几何，σ=0.5（p=−1）调和。
测试断言的对照值由独立路径计算（np.prod / 显式倒数和），不经被测模块。
"""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim import aggregate  # noqa: E402
from autonomy_sim.rng import make_rng  # noqa: E402

W2 = (0.5, 0.5)
W3 = (0.2, 0.3, 0.5)
W4 = (0.1, 0.2, 0.3, 0.4)
W5 = (0.2, 0.2, 0.2, 0.2, 0.2)


def _bipartitions(n):
    """{0..n-1} 的全部非平凡双划分（固定 0∈K 去镜像），共 2^(n-1)−1 个。"""
    out = []
    for mask in range(1 << (n - 1)):
        K = [0] + [i for i in range(1, n) if mask >> (i - 1) & 1]
        L = [i for i in range(1, n) if not (mask >> (i - 1) & 1)]
        if L:
            out.append((K, L))
    return out


def _renorm(w, idx):
    s = sum(w[i] for i in idx)
    return tuple(w[i] / s for i in idx), s


class TestTREP1(unittest.TestCase):
    """表示定理 6.5/6.6：几何聚合 ∏ x_i^{w_i} 满足 (A1)–(A6)。"""

    def test_TREP1_form_matches_independent_product(self):
        cases = [
            ((0.5, 0.25, 1.0), W3),
            ((0.9, 0.7, 0.3), W3),
            ((1.0, 1.0, 1.0, 1.0), W4),
            ((0.05, 0.99, 0.42, 0.77), W4),
        ]
        for x, w in cases:
            expect = float(np.prod(np.array(x) ** np.array(w)))
            self.assertAlmostEqual(aggregate.geometric_mean(x, w), expect, places=12)
            self.assertAlmostEqual(aggregate.F_sigma(x, w, 1.0), expect, places=12)
        # 路线 B 规范化：F(1,…,1)=1
        self.assertAlmostEqual(aggregate.geometric_mean((1.0,) * 4, W4), 1.0, places=12)

    def test_TREP1_A1_continuity(self):
        x = [0.4, 0.6, 0.8]
        base = aggregate.geometric_mean(x, W3)
        # 单坐标扰动：∂F/∂x_1=w_1·F/x_1≤w_1/x_1=0.5 ⇒ |ΔF|≲0.5δ（宽松界 10δ）
        for delta in (1e-6, 1e-8, 1e-10):
            xp = list(x)
            xp[0] += delta
            self.assertLess(abs(aggregate.geometric_mean(xp, W3) - base), 10.0 * delta)
        # 扰动序列 ⇒ 函数值收敛
        diffs = [abs(aggregate.geometric_mean([x[0] + 10.0 ** (-k), x[1], x[2]], W3) - base)
                 for k in (4, 6, 8)]
        self.assertTrue(diffs[0] > diffs[1] > diffs[2])

    def test_TREP1_A2_strict_coordinate_increase(self):
        x = [0.8, 0.5, 0.6]
        base = aggregate.geometric_mean(x, W3)
        for i in range(3):
            xh = list(x)
            xh[i] *= 0.5
            fh = aggregate.geometric_mean(xh, W3)
            self.assertLess(fh, base)  # 严格递增（AX4：排除 Leontief/min）
            # 几何聚合的精确弹性：F(x_i 减半)=F·2^{−w_i}
            self.assertAlmostEqual(fh / base, 0.5 ** W3[i], places=10)

    def test_TREP1_A3_biseparability(self):
        rng = make_rng(910003)
        x = tuple(0.05 + 0.95 * float(v) for v in rng.random(4))
        fx = aggregate.geometric_mean(x, W4)
        for K, L in _bipartitions(4):
            wK, WK = _renorm(W4, K)
            wL, WL = _renorm(W4, L)
            fK = aggregate.geometric_mean(tuple(x[i] for i in K), wK)
            fL = aggregate.geometric_mean(tuple(x[i] for i in L), wL)
            # G(u,v)=u^{W_K}·v^{W_L}：子群聚合顺序无关
            self.assertAlmostEqual(fK ** WK * fL ** WL, fx, places=12)

    def test_TREP1_A4_zero_annihilation(self):
        self.assertGreater(aggregate.geometric_mean((0.8, 0.5, 0.6), W3), 0.0)
        for i in range(3):
            x = [0.8, 0.5, 0.6]
            x[i] = 0.0
            self.assertEqual(aggregate.geometric_mean(x, W3), 0.0)

    def test_TREP1_A5_homogeneity(self):
        x = (0.7, 0.45, 0.9)
        for t in (0.37, 0.99, 0.01):
            tx = tuple(t * v for v in x)
            self.assertAlmostEqual(
                aggregate.geometric_mean(tx, W3), t * aggregate.geometric_mean(x, W3), places=12)

    def test_TREP1_A6b_scale_order_invariance(self):
        rng = make_rng(910006)
        for _ in range(20):
            x = 0.05 + 0.95 * rng.random(3)
            y = 0.05 + 0.95 * rng.random(3)
            lam = 0.05 + 0.95 * rng.random(3)
            fx, fy = (aggregate.geometric_mean(v, W3) for v in (x, y))
            flx, fly = (aggregate.geometric_mean(lam * v, W3) for v in (x, y))
            # 序不变：F(x)≥F(y) ⟺ F(λ⊙x)≥F(λ⊙y)
            self.assertEqual(fx >= fy, flx >= fly)
            # 几何聚合更强：比率精确不变 F(λx)/F(λy)=F(x)/F(y)
            self.assertAlmostEqual(flx / fly, fx / fy, places=9)


class TestTREP2(unittest.TestCase):
    """命题 6.7：调和平均满足 (A1)–(A5) 但违反 (A6b)——E2 反例的数值见证。"""

    def test_TREP2_registered_witness_order_flip(self):
        # 附录 §6.4 注册 witness：x=(0.25,1), y=(0.5,0.5), λ=(1,0.25)
        x, y, lam = (0.25, 1.0), (0.5, 0.5), (1.0, 0.25)
        hx = aggregate.harmonic_mean(x, W2)
        hy = aggregate.harmonic_mean(y, W2)
        hlx = aggregate.harmonic_mean(tuple(l * v for l, v in zip(lam, x)), W2)
        hly = aggregate.harmonic_mean(tuple(l * v for l, v in zip(lam, y)), W2)
        # 精确值锚（独立路径：(Σ w/x)^{-1}）
        self.assertAlmostEqual(hx, 0.4, places=12)
        self.assertAlmostEqual(hy, 0.5, places=12)
        self.assertAlmostEqual(hlx, 0.25, places=12)
        self.assertAlmostEqual(hly, 0.2, places=12)
        # 序翻转：y≻x 但 λx≻λy ⇒ (A6b) 违反
        self.assertGreater(hy, hx)
        self.assertGreater(hlx, hly)

    def test_TREP2_harmonic_keeps_A2_A4_A5(self):
        x = (0.8, 0.5, 0.6)
        expect = 1.0 / sum(wi / vi for wi, vi in zip(W3, x))  # 独立路径
        hx = aggregate.harmonic_mean(x, W3)
        self.assertAlmostEqual(hx, expect, places=12)
        # A2 严格单调
        for i in range(3):
            xh = list(x)
            xh[i] *= 0.5
            self.assertLess(aggregate.harmonic_mean(xh, W3), hx)
        # A4 零歼灭（调和保持零歼灭——它违反的只是 A6b）
        for i in range(3):
            xz = list(x)
            xz[i] = 0.0
            self.assertEqual(aggregate.harmonic_mean(xz, W3), 0.0)
        # A5 一次齐次
        t = 0.37
        self.assertAlmostEqual(
            aggregate.harmonic_mean(tuple(t * v for v in x), W3), t * hx, places=12)

    def test_TREP2_harmonic_biseparable_A3(self):
        # 拟算术生成元 φ(x)=−1/x ⇒ 双可分：G(u,v)=(W_K/u+W_L/v)^{-1}
        rng = make_rng(910023)
        x = tuple(0.05 + 0.95 * float(v) for v in rng.random(4))
        hx = aggregate.harmonic_mean(x, W4)
        for K, L in _bipartitions(4):
            wK, WK = _renorm(W4, K)
            wL, WL = _renorm(W4, L)
            hK = aggregate.harmonic_mean(tuple(x[i] for i in K), wK)
            hL = aggregate.harmonic_mean(tuple(x[i] for i in L), wL)
            self.assertAlmostEqual(1.0 / (WK / hK + WL / hL), hx, places=12)


class TestTSIGMA(unittest.TestCase):
    """附录 §6.5（E3）：σ=2 ⇒ p=1/2>0 ⇒ 零歼灭失效——压力测试的正当性见证。"""

    def test_TSIGMA_sigma_p_conversion(self):
        self.assertEqual(aggregate.p_of_sigma(1.0), 0.0)    # 几何
        self.assertEqual(aggregate.p_of_sigma(0.5), -1.0)   # 调和
        self.assertEqual(aggregate.p_of_sigma(2.0), 0.5)    # p>0：越出公理容许域
        with self.assertRaises(ValueError):
            aggregate.p_of_sigma(0.0)  # σ→0（Leontief）被 (A2) 排除，不提供

    def test_TSIGMA_sigma2_breaks_zero_annihilation(self):
        x = (1.0, 0.0)
        # 精确见证：F_2((1,0); ½,½)=(0.5·√1+0.5·0)^2=0.25>0（AX5 失效）
        f2 = aggregate.F_sigma(x, W2, 2.0)
        self.assertAlmostEqual(f2, 0.25, places=12)
        self.assertGreater(f2, 0.0)
        # 同输入在公理主带内零歼灭成立
        self.assertEqual(aggregate.F_sigma(x, W2, 1.0), 0.0)
        self.assertEqual(aggregate.F_sigma(x, W2, 0.5), 0.0)
        # 闸门复合：σ=2 时通道置零不再归零（压力测试语义——须显式标注违反公理）
        comps = (0.8, 0.0, 0.7)
        self.assertGreater(aggregate.composite_A(0.9, comps, (1 / 3, 1 / 3, 1 / 3), sigma=2.0), 0.0)
        # 但存续闸门与 σ 无关：A_via=0 ⇒ A=0 恒成立（附录 §6.6）
        self.assertEqual(aggregate.composite_A(0.0, comps, (1 / 3, 1 / 3, 1 / 3), sigma=2.0), 0.0)


class TestTAX5(unittest.TestCase):
    """input AX5＝公理 (A4)：σ 主带内任一分量置 0 ⇒ A=0；全正值 ⇒ A>0。"""

    def test_TAX5_zero_annihilation_main_band(self):
        comps = (0.8, 0.6, 0.9, 0.7, 0.5)  # (A_org, A_goal, A_exec, A_epi, A_ref)
        for sigma in (0.5, 0.75, 1.0):
            a = aggregate.composite_A(0.95, comps, W5, sigma=sigma)
            self.assertGreater(a, 0.0)   # 全正值 ⇒ A>0（不歼灭正值）
            self.assertLessEqual(a, 1.0)
            # 存续闸门置零
            self.assertEqual(aggregate.composite_A(0.0, comps, W5, sigma=sigma), 0.0)
            # 逐通道置零 ⇒ A=0（合取必要）
            for i in range(5):
                cz = list(comps)
                cz[i] = 0.0
                self.assertEqual(aggregate.composite_A(0.95, cz, W5, sigma=sigma), 0.0)

    def test_TAX5_all_ones_gives_one(self):
        # F(1,…,1)=1（路线 B 规范化）＋闸门全开 ⇒ A=1
        self.assertAlmostEqual(aggregate.composite_A(1.0, (1.0,) * 5, W5, sigma=1.0), 1.0, places=12)
        self.assertAlmostEqual(aggregate.composite_A(1.0, (1.0,) * 5, W5, sigma=0.5), 1.0, places=12)


if __name__ == "__main__":
    unittest.main()
