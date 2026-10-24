"""L1 数学性质测试：动力学模块（SPEC_tests §2 注册表 T-T6a/T-T6b/T-T6c/T-C1/T-C2）。

- T-T6a（定理 7.6.3）：Ḋ≤δ−κD ⇒ limsup D≤δ/κ；δ<δ* ⇒ A≥A_min（显式公式逐 run 核对）。
- T-T6b（推论 7.6.6＋盲区预测）：θ/W≤κ ⇒ 全域有界；θ/W>κ 且 δ∈(κ,θ/W) ⇒ 俘获（正反两面）。
- T-T6c（命题 7.6.5）：检测时刻损伤随 δ→0 发散（log(1/α)/δ 标度趋势）。
- T-C1（命题 8.2.1）：fold 平衡公式数值核对；T_rec∝(δ_c−δ)^{−1/2} 标度律。
- T-C2（命题 8.3.1）：双稳区间；δ_down 与 s_c 独立为正（回环不闭合）。
"""
import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim import aggregate, dynamics  # noqa: E402
from autonomy_sim.rng import make_rng  # noqa: E402


class TestTT6A(unittest.TestCase):
    """定理 7.6.3：limsup D≤δ/κ 与 A_min 显式下界逐 run 核对。"""

    def test_TT6a_limsup_constant_delta(self):
        # 常值 δ：精确解 D=δ/κ(1−e^{−κt})，limsup=δ/κ
        kappa, delta = 0.5, 0.2
        ts, ds, n_reg = dynamics.simulate_damage(lambda t: delta, kappa, T=60.0, dt=0.02)
        self.assertEqual(n_reg, 0)  # 无 M1 配置
        self.assertTrue(np.all(ds <= delta / kappa + 1e-9))  # D0=0 ⇒ 全程不超 limsup
        self.assertAlmostEqual(ds[-1], delta / kappa, places=6)
        # 时变 δ 有界于 δ̄：limsup ≤ δ̄/κ（比较原理）
        d_bar = 0.3
        _, ds2, _ = dynamics.simulate_damage(
            lambda t: d_bar * (0.5 + 0.5 * math.sin(t)), kappa, T=200.0, dt=0.02)
        self.assertTrue(np.all(ds2 <= d_bar / kappa + 1e-6))
        self.assertLess(ds2[-1], d_bar / kappa + 1e-6)

    def test_TT6a_a_min_formula_per_run(self):
        # δ_j<δ*_j 多通道：D_j≤δ_j/κ_j ∀t（D0=0）⇒ A(t)≥A_min ∀t（逐 run 核对显式公式）
        rng = make_rng(910061)
        for _ in range(4):
            kappas = 0.6 + 0.4 * rng.random(5)          # κ∈[0.6,1.0]（非 binding，保证 A_min>0）
            thetas = 0.1 + 0.2 * rng.random(5)
            Ws = np.ones(5)
            rs = np.ones(5)
            c0s = 0.1 + 0.2 * rng.random(5)             # θ/W、⌈(r+1)/2⌉c₀/W ∈[0.1,0.3] < κ（r=1）
            d_stars = np.array([dynamics.delta_star(th, w, k, r, c)
                                for th, w, k, r, c in zip(thetas, Ws, kappas, rs, c0s)])
            self.assertTrue(np.all(d_stars < kappas))   # δ*<κ ⇒ A_min 显式下界为正
            deltas = 0.9 * d_stars  # δ_j(t)<δ*_j（定理前提）
            a_base = 0.5 + 0.5 * rng.random(5)
            weights = rng.random(5)
            weights /= weights.sum()
            a_via_min = 0.9
            a_min_val = dynamics.a_min(a_via_min, tuple(a_base), tuple(weights),
                                       tuple(d_stars), tuple(kappas))
            self.assertGreater(a_min_val, 0.0)  # 显式下界为正（δ*<κ 的分量亦含于乘积）
            trajs = [dynamics.simulate_damage(lambda t, dj=dj: dj, kj, T=80.0, dt=0.05)[1]
                     for dj, kj in zip(deltas, kappas)]
            for dj, kj, ds_j in zip(deltas, kappas, trajs):
                self.assertTrue(np.all(ds_j <= dj / kj + 1e-6))  # (ii) limsup 界逐通道
            for k in range(0, len(trajs[0]), 100):
                comps = tuple(a_base[j] * (1.0 - trajs[j][k]) for j in range(5))
                a_t = aggregate.composite_A(a_via_min, comps, tuple(weights), 1.0)
                self.assertGreaterEqual(a_t, a_min_val - 1e-9)  # (iii) A≥A_min 逐时刻


class TestTT6B(unittest.TestCase):
    """推论 7.6.6（设计规则）与盲区预测（正反两面）。"""

    def test_TT6b_design_rule_globally_bounded(self):
        # θ/W≤κ：全域有界——δ<θ/W 由 M3 处理；δ≥θ/W 由 M1 处理（登记触发且 D 不俘获）
        theta, W, kappa, lag = 0.4, 2.0, 0.2, 0.1  # θ/W=0.2=κ
        for delta, expect_reg in ((0.10, False), (0.19, False), (0.21, True), (0.5, True), (2.0, True)):
            _, ds, n_reg = dynamics.simulate_damage(
                lambda t, d=delta: d, kappa, T=60.0, dt=0.01,
                theta=theta, W=W, lag=lag)
            self.assertEqual(n_reg > 0, expect_reg, f"δ={delta} 登记触发预期 {expect_reg}")
            self.assertLess(float(ds.max()), 0.99, f"δ={delta} 全域有界（不俘获）")
            if not expect_reg:
                self.assertLessEqual(float(ds.max()), delta / kappa + 1e-6)  # M3 域：δ/κ 界

    def test_TT6b_blind_zone_capture(self):
        # θ/W>κ（设计失配）且 δ∈(κ,θ/W)：登记零触发＋修复不足 ⇒ D→1（有防御仍俘获）
        theta, W, kappa = 0.8, 2.0, 0.2  # θ/W=0.4>κ=0.2；盲区 (0.2,0.4)
        _, ds, n_reg = dynamics.simulate_damage(
            lambda t: 0.3, kappa, T=200.0, dt=0.01, theta=theta, W=W, lag=0.1)
        self.assertEqual(n_reg, 0)  # δ·W=0.6<θ=0.8 ⇒ M1 永不触发
        self.assertGreater(ds[-1], 0.999)  # 修复不足 ⇒ 单调走向俘获
        # 对照：δ=0.15<κ ⇒ M3 处理，有界不俘获
        _, ds2, n_reg2 = dynamics.simulate_damage(
            lambda t: 0.15, kappa, T=200.0, dt=0.01, theta=theta, W=W, lag=0.1)
        self.assertEqual(n_reg2, 0)
        self.assertLess(ds2[-1], 0.15 / kappa + 1e-3)
        self.assertLess(ds2[-1], 0.99)


class TestTT6C(unittest.TestCase):
    """命题 7.6.5：纯检测下检测时刻损伤随 δ→0 发散（log(1/α)/δ 标度）。"""

    def test_TT6c_detection_damage_diverges(self):
        rng = make_rng(910063)
        sigma, alpha = 1.0, 1e-3
        deltas = (0.5, 0.25, 0.125, 0.0625)
        damages = []
        for d in deltas:
            edd, rate = dynamics.cusum_edd(d, sigma, alpha, n_runs=400, rng=rng)
            self.assertGreater(rate, 0.99)  # 全部检出
            damages.append(d * edd)  # 检测时刻损伤 = δ·EDD
        damages = np.array(damages)
        # 发散：δ 减半 ⇒ 检测时刻损伤严格增大
        self.assertTrue(np.all(np.diff(damages) > 0))
        # 标度对照 2σ²·log(1/α)/δ：比值在同数量级（overshoot 常数域容差）
        scale = 2.0 * sigma**2 * math.log(1.0 / alpha) / np.array(deltas)
        ratio = damages / scale
        self.assertTrue(np.all(ratio > 0.5) and np.all(ratio < 3.0), f"比值 {ratio}")
        # log-log 斜率 ≈ −1（发散的 1/δ 形态）
        slopes = np.diff(np.log(damages)) / np.diff(np.log(np.array(deltas)))
        self.assertTrue(np.all((-1.6 < slopes) & (slopes < -0.6)), f"斜率 {slopes}")


class TestTC1(unittest.TestCase):
    """命题 8.2.1：fold 分岔平衡公式与临界减慢标度。"""

    def test_TC1_fold_equilibria_and_stability(self):
        eps_v = 0.8
        for delta in (0.05, 0.10, 0.15):
            d_minus, d_plus = dynamics.c1_equilibria(delta, eps_v)
            # 公式锚：闭式根满足 f(D)=0（f(D)=δ−εv·D(1−D)）
            f = lambda D: delta - eps_v * D * (1.0 - D)
            self.assertAlmostEqual(f(d_minus), 0.0, places=12)
            self.assertAlmostEqual(f(d_plus), 0.0, places=12)
            # 稳定性：f′(D_−)=−εv(1−2D_−)<0，f′(D_+)>0
            fp = lambda D: -eps_v * (1.0 - 2.0 * D)
            self.assertLess(fp(d_minus), 0.0)
            self.assertGreater(fp(d_plus), 0.0)
            # 吸引域：D0<D_+ ⇒ 收敛 D_−；D0>D_+ ⇒ 失控至俘获
            _, ds = dynamics.simulate_ode(f, D0=d_plus - 0.05, T=200.0)
            self.assertAlmostEqual(ds[-1], d_minus, places=3)
            _, ds2 = dynamics.simulate_ode(f, D0=d_plus + 0.02, T=400.0)
            self.assertGreater(ds2[-1], 0.99)
        # δ>δ_c=εv/4：无内点平衡 ⇒ 灾变至俘获
        self.assertIsNone(dynamics.c1_equilibria(0.25, eps_v))
        _, ds3 = dynamics.simulate_ode(lambda D: 0.25 - eps_v * D * (1.0 - D), D0=0.0, T=400.0)
        self.assertGreater(ds3[-1], 0.99)

    def test_TC1_critical_slowing_scaling(self):
        eps_v = 0.8
        d_c = eps_v / 4.0
        deltas = np.array([0.10, 0.15, 0.18, 0.19])
        t_recs = np.array([dynamics.measure_t_rec(float(d), eps_v, T=500.0) for d in deltas])
        # 恢复时间随 δ→δ_c 发散
        self.assertTrue(np.all(np.diff(t_recs) > 0))
        # 标度律 T_rec∝(δ_c−δ)^{−1/2}：log-log 斜率 ∈[−0.65,−0.35]
        slope = float(np.polyfit(np.log(d_c - deltas), np.log(t_recs), 1)[0])
        self.assertTrue(-0.65 <= slope <= -0.35, f"斜率 {slope}")
        # 理论锚：特征值 |f′(D_−)|=εv√(1−4δ/εv)→0
        lam = [eps_v * math.sqrt(1.0 - 4.0 * float(d) / eps_v) for d in deltas]
        self.assertTrue(np.all(np.diff(lam) < 0))


class TestTC2(unittest.TestCase):
    """命题 8.3.1：双稳与滞后回环（崩溃由 δ 触发、恢复由 s>s_c 触发，回环不闭合）。"""

    def test_TC2_bistability_hysteresis(self):
        e0v, gamma = 1.0, 3.0
        d1, dm = dynamics.c2_roots(gamma)
        r = dynamics.c2_r(e0v, gamma)
        delta_down, s_c = r(d1), -r(dm)
        # 独立锚：密网格上 r 的极大/极小（不依赖模块的求根公式）⇒ δ_down=r(D₁)、s_c=|r(D_m)|
        grid_a = np.linspace(1e-9, 1.0 / gamma, 200001)
        grid_b = np.linspace(1.0 / gamma, 1.0, 200001)
        self.assertAlmostEqual(delta_down, max(r(float(d)) for d in grid_a), places=6)
        self.assertAlmostEqual(s_c, -min(r(float(d)) for d in grid_b), places=6)
        self.assertGreater(delta_down, 1e-3)
        self.assertGreater(s_c, 1e-3)
        # (i) 双稳：δ∈(0,δ_down)，自 0 ⇒ 稳定小平衡 A<D₁；自 ≈1 ⇒ 保持俘获（吸收）
        delta = 0.5 * delta_down
        f = lambda D, s=0.0: delta - r(D) - s
        _, ds_a = dynamics.simulate_ode(f, D0=0.0, T=300.0)
        self.assertLess(ds_a[-1], d1)
        _, ds_b = dynamics.simulate_ode(f, D0=0.999, T=300.0)
        self.assertGreater(ds_b[-1], 0.99)
        # (ii) δ↑超 δ_down ⇒ 灾变跳至俘获
        _, ds_c = dynamics.simulate_ode(lambda D: 1.5 * delta_down - r(D), D0=0.0, T=400.0)
        self.assertGreater(ds_c[-1], 0.99)
        # (iii) 滞后不闭合：δ 降回 0 ⇒ 仍锁滞于 1（自发恢复不可能）
        _, ds_d = dynamics.simulate_ode(lambda D: 0.0 - r(D), D0=0.999, T=300.0)
        self.assertGreater(ds_d[-1], 0.99)
        # (iv) 恢复须 s>s_c：s=1.5·s_c ⇒ 自发弛豫至 ≈0；s=0.5·s_c ⇒ 锁滞于高损伤平衡（不恢复）
        _, ds_e = dynamics.simulate_ode(lambda D: 0.0 - r(D) - 1.5 * s_c, D0=0.999, T=400.0)
        self.assertLess(ds_e[-1], 0.05)
        _, ds_f = dynamics.simulate_ode(lambda D: 0.0 - r(D) - 0.5 * s_c, D0=0.999, T=400.0)
        self.assertGreater(ds_f[-1], 0.8)  # 上稳定平衡（dm,1 内）⇒ 恢复失败


if __name__ == "__main__":
    unittest.main()
