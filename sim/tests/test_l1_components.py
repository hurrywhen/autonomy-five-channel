"""L1 数学性质测试：分量真值模块（SPEC_tests §2 注册表 T-EXEC/T-GOAL/T-EPI/T-REF）。

- T-EXEC（附录命题 5.6＋SPEC_estimators E3.6）：ℰ^Π ≤ n·log|𝒜|；无助签名（Π 收缩 ⇒ ℰ^Π→0 而 ℰ^env 不变）。
- T-GOAL（附录命题 5.4＋E9＋SPEC_estimators E4.5）：d=d_c ⇒ A_goal=0；部分俘获分级；Fix=∅ 退化预案良构。
- T-EPI（input D-epi E11＋SPEC_estimators E5.4；2026-10-15 精度化口径）：信念钉到非真值桶 ⇒ A_epi^real=0；real/rob 双轨输出分离。
- T-REF（input D-ref E10＋SPEC_estimators E6.4）：系综退化（H(θ_π)=0）⇒ 报区间而非 0/0。

锚点：BSC/Z 信道容量解析值（nats）；epi 确定性 fixture 下 D(s)=s 精确；goal 退化区间手算值。
"""
import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim import components, empowerment, interventions  # noqa: E402
from autonomy_sim.di import entropy_nats, mi_nats  # noqa: E402
from autonomy_sim.fixtures import toy_model_epi_deterministic  # noqa: E402
from autonomy_sim.rng import make_rng  # noqa: E402

LN2 = math.log(2.0)


def _hb(p):
    """二元熵（nats）。"""
    return -(p * math.log(p) + (1 - p) * math.log(1 - p))


class TestTEXEC(unittest.TestCase):
    """命题 5.6：ℰ^Π ≤ n·log|𝒜|（上界与规范化）；无助签名（E3.3）。"""

    def test_TEXEC_ba_capacity_anchors(self):
        # BSC(0.11)：C = ln2 − H_b(0.11)（对称信道，解析锚）
        p = 0.11
        bsc = np.array([[1 - p, p], [p, 1 - p]])
        c_bsc, q_bsc = empowerment.blahut_arimoto(bsc)
        self.assertAlmostEqual(c_bsc, LN2 - _hb(p), places=8)
        self.assertAlmostEqual(float(q_bsc[0]), 0.5, places=10)
        # Z 信道（p=0.5）：C = ln(1+(1−p)·p^{p/(1−p)}) = ln(1.25)（非对称收敛锚）
        z = np.array([[1.0, 0.0], [0.5, 0.5]])
        c_z, _ = empowerment.blahut_arimoto(z)
        self.assertAlmostEqual(c_z, math.log(1.25), places=6)

    def test_TEXEC_bound_and_normalizer(self):
        # 无噪信道界可达：C = log|𝒜|，A_exec=1（n=1）
        eye4 = np.eye(4)
        c_eye, _ = empowerment.blahut_arimoto(eye4)
        self.assertAlmostEqual(c_eye, math.log(4.0), places=8)
        self.assertAlmostEqual(empowerment.a_exec(c_eye, n=1, n_A=4), 1.0, places=10)
        # n 步规范化：二重无噪信道 C=2·log|𝒜| ⇒ A_exec(n=2)=1（n·log|𝒜| 的语义锚）
        eye16 = np.kron(eye4, eye4)
        c16, _ = empowerment.blahut_arimoto(eye16)
        self.assertAlmostEqual(c16, 2.0 * math.log(4.0), places=8)
        self.assertAlmostEqual(empowerment.a_exec(c16, n=2, n_A=4), 1.0, places=10)
        # 随机信道：命题 5.6(i) 上界 ℰ ≤ n·log|𝒜| 恒成立
        rng = make_rng(910041)
        for _ in range(10):
            w = rng.random((4, 6))
            w /= w.sum(axis=1, keepdims=True)
            c, _ = empowerment.channel_capacity(w)
            self.assertLessEqual(c, math.log(4.0) + 1e-9)
            self.assertGreaterEqual(c, -1e-12)

    def test_TEXEC_helplessness_signature(self):
        # 无助签名（附录 §5.4/E3.3）：Π 收缩至常量策略 ⇒ ℰ^Π→0 而 ℰ^env 不变
        noisy = 0.7 * np.eye(4) + 0.3 / 4.0
        e_env = empowerment.empowerment_support(noisy, (0, 1, 2, 3))
        self.assertGreater(e_env, 1e-3)  # 环境容量完好
        e_collapsed = empowerment.empowerment_support(noisy, (0,))
        self.assertEqual(e_collapsed, 0.0)  # 行为库坍缩 ⇒ ℰ^Π=0 精确
        # 鉴别器语义：ℰ^env 不因 Π 收缩而改变（两次计算同一环境信道）
        self.assertAlmostEqual(e_env, empowerment.empowerment_support(noisy, (0, 1, 2, 3)), places=15)
        # 部分收缩：无噪信道支撑 {0,1} ⇒ C=ln2（< ln4）
        self.assertAlmostEqual(empowerment.empowerment_support(np.eye(4), (0, 1)), LN2, places=8)


class TestTGOAL(unittest.TestCase):
    """命题 5.4＋E9：完全俘获归零、部分俘获分级；Fix=∅ 退化预案良构。"""

    @staticmethod
    def _grid9():
        return [i * 0.125 for i in range(9)]

    def test_TGOAL_fixpoint_and_grading(self):
        grid = self._grid9()
        endorse = lambda u: 0.5 + 0.5 * (u - 0.5)  # Banach 压缩，c=0.5，U*=0.5
        # Fix 枚举与 Banach 迭代
        self.assertEqual(components.fix_points(endorse, grid), [0.5])
        self.assertAlmostEqual(components.banach_fixed_point(endorse, 0.0), 0.5, places=9)
        # 压缩率精确：逐次迭代距离比 = c
        u0, u1, u2 = 0.0, endorse(0.0), endorse(endorse(0.0))
        self.assertAlmostEqual(abs(u1 - 0.5) / abs(u0 - 0.5), 0.5, places=12)
        self.assertAlmostEqual(abs(u2 - 0.5) / abs(u1 - 0.5), 0.5, places=12)
        # d_c=0.5；完全俘获（d=d_c）⇒ A_goal=0；部分俘获分级
        anchors = {0.0: 0.0, 0.25: 0.5, 0.375: 0.75, 0.5: 1.0, 1.0: 0.0}
        for u_eff, expect in anchors.items():
            g = components.truth_A_goal(u_eff, endorse, grid)
            self.assertFalse(g.degenerate)
            self.assertAlmostEqual(g.point, expect, places=12)
            self.assertEqual(g.lo, g.hi)  # 真值路径区间退化为点（E0.2）
        vals = [components.truth_A_goal(u, endorse, grid).point
                for u in (0.0, 0.125, 0.25, 0.375, 0.5)]
        self.assertTrue(all(a < b for a, b in zip(vals, vals[1:])))  # 连续谱单调分级

    def test_TGOAL_degenerate_interval_wellformed(self):
        # Θ11，无不动点映射：ε_min=0.1 仅在 {0.0,0.1} 达到（其余位移 0.3）
        grid = [i / 10 for i in range(11)]
        mapping = {0: 1, 1: 0, 2: 5, 3: 6, 4: 7, 5: 2, 6: 3, 7: 4, 8: 5, 9: 6, 10: 7}
        endorse = lambda u: mapping[round(u * 10)] / 10
        self.assertEqual(components.fix_points(endorse, grid), [])  # Fix=∅
        em = components.eps_min(endorse, grid)
        self.assertAlmostEqual(em, 0.1, places=12)
        em2, fset = components.approx_fix_set(endorse, grid)
        self.assertAlmostEqual(em2, 0.1, places=12)
        self.assertEqual(sorted(fset), [0.0, 0.1])  # Fix_{ε_min} 非空（E9 良构前提）
        # d_c=max d(U,Fix_ε)=0.9（U=1.0）；U_eff=0.5 ⇒ d_H=0.4
        # 区间 = [1−0.5/0.9, 1−0.3/0.9] ≈ [0.444, 0.667]（严格子区间，不裁剪）
        g = components.truth_A_goal(0.5, endorse, grid)
        self.assertTrue(g.degenerate)
        self.assertIsNone(g.point)
        self.assertAlmostEqual(g.lo, 1 - 0.5 / 0.9, places=9)
        self.assertAlmostEqual(g.hi, 1 - 0.3 / 0.9, places=9)
        self.assertLess(g.lo, g.hi)
        self.assertFalse(g.clipped)
        # U_eff=1.0 ⇒ d_H=0.9=d_c：lo=1−1.0/0.9<0 ⇒ 裁剪到 0，hi=1−0.8/0.9
        g2 = components.truth_A_goal(1.0, endorse, grid)
        self.assertAlmostEqual(g2.lo, 0.0, places=12)
        self.assertAlmostEqual(g2.hi, 1 - 0.8 / 0.9, places=9)
        self.assertTrue(g2.clipped)
        # Fix_{ε_min}=Θ（全循环）⇒ d_c=0 ⇒ 区间约定 [0,1]（完全不定，E4.5）
        grid9 = self._grid9()
        cyc = lambda u: grid9[(round(u * 8) + 1) % 9]
        g3 = components.truth_A_goal(0.5, cyc, grid9)
        self.assertTrue(g3.degenerate)
        self.assertEqual((g3.lo, g3.hi), (0.0, 1.0))


class TestTEPI(unittest.TestCase):
    """D-epi（E11 双轨；2026-10-15 精度化口径）：信念全程钉到非真值桶 ⇒ A_epi^real=0；
    real/rob 输出分离（E5.4 对抗族）。fixture n_E=n_B=2 ⇒ κ=恒等映射显式传入。"""

    BMAP = np.arange(2)  # κ(e)=e（toy_model_epi_deterministic 的通道语义）

    def test_TEPI_tv1_gives_zero_real(self):
        m0 = toy_model_epi_deterministic()
        mg = interventions.apply_gamma(m0, interventions.GammaSpec.mix_constant(1.0, symbol=1))
        self.assertAlmostEqual(mg.params["gamma"]["s"], 1.0, places=12)  # P4.4 强度登记
        r = components.truth_A_epi_real(mg, 4, self.BMAP)
        self.assertAlmostEqual(r.d_bar, 1.0, places=12)  # E≡0（κ(0)=0）而信念全程 B=δ_1
        self.assertAlmostEqual(r.a_epi_real, 0.0, places=12)  # 对真值桶赋零概率 ⇒ A_epi^real=0

    def test_TEPI_grading_monotone(self):
        m0 = toy_model_epi_deterministic()
        # 确定性 fixture 下精度损失 D̄_acc(s)=s 解析成立 ⇒ A_epi^real=1−s 精确
        for s in (0.0, 0.3, 0.7, 1.0):
            mg = interventions.apply_gamma(m0, interventions.GammaSpec.mix_constant(s, symbol=1))
            r = components.truth_A_epi_real(mg, 4, self.BMAP)
            self.assertAlmostEqual(r.a_epi_real, 1.0 - s, places=12)
            self.assertAlmostEqual(mg.params["gamma"]["s"], s, places=12)

    def test_TEPI_real_rob_separation(self):
        m0 = toy_model_epi_deterministic()
        # 实现轨：已实现的 γ 为 s=0.3 ⇒ real=0.7
        mg = interventions.apply_gamma(m0, interventions.GammaSpec.mix_constant(0.3, symbol=1))
        real = components.truth_A_epi_real(mg, 4, self.BMAP)
        self.assertAlmostEqual(real.a_epi_real, 0.7, places=12)
        # 稳健轨：预算 β=0.8 内最坏精度损失 ⇒ rob=1−0.8=0.2（sup 在边界达到）
        grid = [i / 10 for i in range(9)]  # 0.0..0.8
        rob = components.truth_A_epi_rob(m0, grid, T=4, symbol=1, bucket_map=self.BMAP)
        self.assertAlmostEqual(rob.d_sup, 0.8, places=12)
        self.assertAlmostEqual(rob.a_epi_rob, 0.2, places=12)
        profile_vals = [d for _, d in rob.profile]
        self.assertTrue(all(a <= b + 1e-12 for a, b in zip(profile_vals, profile_vals[1:])))
        # 双轨分离：real > rob（设计对偶量严于实现轨），且各自 ∈[0,1]
        self.assertGreater(real.a_epi_real, rob.a_epi_rob)
        for v in (real.a_epi_real, rob.a_epi_rob):
            self.assertTrue(0.0 <= v <= 1.0)


class TestTREF(unittest.TestCase):
    """D-ref（E10）：系综退化 ⇒ 报区间而非 0/0；三因子良构性与零点语义（命题 5.8）。"""

    def test_TREF_degenerate_ensemble_reports_interval(self):
        # H(θ_π)=0：系综集中于单一 θ（行 0），M 任意分布
        j = np.zeros((3, 2))
        j[0, :] = [0.5, 0.5]
        r = components.truth_A_ref(j, p_endorse=0.9, lam_ref=0.8)
        self.assertTrue(r.degenerate)
        self.assertIsNone(r.point)  # 禁止 0/0 静默
        self.assertEqual(r.lo, 0.0)
        self.assertAlmostEqual(r.hi, 0.9 * 0.8, places=12)  # E6.4：区间 [0, f2·f3]

    def test_TREF_wellposed_and_zero_semantics(self):
        # 完美读出：I(M;θ)=H(θ)=ln2 ⇒ 保真=1 ⇒ A_ref=f2·f3
        j_perfect = np.array([[0.5, 0.0], [0.0, 0.5]])
        r = components.truth_A_ref(j_perfect, p_endorse=0.9, lam_ref=0.8)
        self.assertFalse(r.degenerate)
        self.assertAlmostEqual(r.point, 0.72, places=12)
        # 含噪读出：保真因子 = I/H = 1−H(θ|M)/H(θ)（恒等式核验）
        j_noisy = np.array([[0.4, 0.1], [0.1, 0.4]])
        h_theta = entropy_nats(j_noisy.sum(axis=1))
        fid = mi_nats(j_noisy) / h_theta
        h_cond = entropy_nats(j_noisy) - entropy_nats(j_noisy.sum(axis=0))
        self.assertAlmostEqual(fid, 1.0 - h_cond / h_theta, places=12)
        r2 = components.truth_A_ref(j_noisy, p_endorse=0.9, lam_ref=0.8)
        self.assertAlmostEqual(r2.point, fid * 0.72, places=12)
        # 零点语义（命题 5.8）：M⫫θ ⇒ I=0 ⇒ A_ref=0；背书缺席 ⇒ 0；背书全污染 ⇒ 0
        j_indep = np.full((2, 2), 0.25)
        self.assertAlmostEqual(components.truth_A_ref(j_indep, 0.9, 0.8).point, 0.0, places=12)
        self.assertAlmostEqual(components.truth_A_ref(j_perfect, 0.0, 0.8).point, 0.0, places=12)
        self.assertAlmostEqual(components.truth_A_ref(j_perfect, 0.9, 0.0).point, 0.0, places=12)
        for f2 in (0.0, 0.5, 1.0):
            v = components.truth_A_ref(j_noisy, f2, 1.0).point
            self.assertTrue(0.0 <= v <= 1.0)


if __name__ == "__main__":
    unittest.main()
