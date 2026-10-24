"""L1 数学性质测试：DI 模块（SPEC_tests §2 注册表 T-DI1/T-DI2/T-ORG/T-MED）。

- T-DI2：Kramer Property 2 反例双构造锚（IEEE 原文方向笔误已核验订正，
  见 docs/R2_文献待查证事项.md §4.6）。
- T-DI1：引理 2.3.1（随机化外源干预 ⇒ MI=DI），真值精确＋采样两路径。
- T-ORG：命题 5.2（AX0 下 F_int>0；A_org∈(0,1]；零点语义）。
- T-MED：引理 7.2.1（α/σ 干预下 F_ext=0 精确成立）＋中介见证（非空判据）。
- T-AX0：引理 4.1 双向显式见证（第 3 步补登——原推进线漏分配，SPEC_tests §5 已登记）。

全部信息量为 nats（SPEC_estimators 总原则）；1 bit = ln2 nats。
"""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim import di, interventions, simulate  # noqa: E402
from autonomy_sim.fixtures import toy_model, toy_model_uniform_policy  # noqa: E402

LN2 = float(np.log(2.0))


def _kramer_printed_construction():
    """Kramer (2003) 附录 B Property 2 后的印刷构造：X1,Y1 iid Ber(1/2)；X2=X1；Y2=X1⊕Y1。

    联合分布 4 个等概原子。返回 shape (2,2,2,2)，轴序 (x1,x2,y1,y2)。
    """
    j = np.zeros((2, 2, 2, 2))
    for x1 in range(2):
        for y1 in range(2):
            j[x1, x1, y1, x1 ^ y1] = 0.25
    return j


def _feedback_construction():
    """反馈构造：X1,Y1 iid Ber(1/2)；X2=Y1；Y2=X2。轴序 (x1,x2,y1,y2)。"""
    j = np.zeros((2, 2, 2, 2))
    for x1 in range(2):
        for y1 in range(2):
            j[x1, y1, y1, y1] = 0.25
    return j


class TestTDI2(unittest.TestCase):
    """Kramer Property 2 反例——闭环/反馈下 MI≠DI 且 MI 无方向的回归锚。"""

    def test_TDI2_kramer_printed_example_true_direction(self):
        j = _kramer_printed_construction()
        mi = di.mi_seq(j, T=2, nx=2, ny=2)
        di_xy = di.massey_di_seq(j, T=2, nx=2, ny=2)
        di_yx = di.massey_di_seq(j.transpose(2, 3, 0, 1), T=2, nx=2, ny=2)
        self.assertAlmostEqual(mi, LN2, places=12)
        # 无反馈（X2=X1 不依赖 Y）⇒ DI=MI（Massey 定理 1）
        self.assertAlmostEqual(di_xy, LN2, places=12)
        # 原文印刷 "I(X²→Y²)=0" 系方向笔误：为 0 的是反向 DI
        self.assertAlmostEqual(di_yx, 0.0, places=12)

    def test_TDI2_feedback_strict_inequality(self):
        j = _feedback_construction()
        di_xy = di.massey_di_seq(j, T=2, nx=2, ny=2)
        di_yx = di.massey_di_seq(j.transpose(2, 3, 0, 1), T=2, nx=2, ny=2)
        mi = di.mi_seq(j, T=2, nx=2, ny=2)
        # 反馈（X2=Y1）⇒ Property 2 右严格不等式：DI(X→Y)=0 而 MI=1 bit
        self.assertAlmostEqual(di_xy, 0.0, places=12)
        self.assertAlmostEqual(mi, LN2, places=12)
        self.assertAlmostEqual(di_yx, LN2, places=12)


class TestTDI1(unittest.TestCase):
    """引理 2.3.1：随机化外源探针 ⇒ I(Ĩ^T;A^T)=I(Ĩ^T→A^T)。"""

    @classmethod
    def setUpClass(cls):
        # 纯随机化探针（q 与 E 无关）⇒ 非预期条件成立（Ĩ_{t+1:T} 与 A^t 独立）
        cls.model = interventions.apply_alpha(
            toy_model(), interventions.AlphaSpec.probe_uniform(n_I=2, response=9.0))
        cls.n_I = 2
        cls.T = 5

    def test_TDI1_randomized_probe_mi_eq_di_exact(self):
        mi, di_val = di.truth_probe_mi_di(self.model, T=self.T)
        self.assertGreater(mi, 5e-3)  # 非空见证：探针确实影响行动
        self.assertAlmostEqual(mi, di_val, places=9)

    def test_TDI1_randomized_probe_sampled(self):
        T, n_I = self.T, self.n_I
        n_traj = 200_000
        seqs = simulate.sample_symbol_sequences(
            self.model, seed=910001, T=T, n_traj=n_traj)
        iseq = (seqs["O"] % n_I).astype(np.int64)  # 探针符号解码（O_flat = o*n_I + i）
        aseq = seqs["A"].astype(np.int64)

        # MI 插件估计：I(Ĩ^T; A^T)
        iw = (n_I ** np.arange(T - 1, -1, -1)).astype(np.int64)
        aw = (3 ** np.arange(T - 1, -1, -1)).astype(np.int64)
        joint = np.zeros((n_I ** T, 3 ** T))
        np.add.at(joint, (iseq @ iw, aseq @ aw), 1.0 / n_traj)
        mi_hat = di.mi_nats(joint)

        # DI 插件估计：Σ_t I(Ĩ^t; A_t | A^{t−1})
        di_hat = 0.0
        for t in range(T):
            # 直方图 (i^t, a^{t−1}, a_t)
            ki = (iseq[:, : t + 1] @ iw[T - 1 - t:]).astype(np.int64)
            ka = (aseq[:, :t] @ aw[T - t:]).astype(np.int64) if t > 0 else np.zeros(n_traj, dtype=np.int64)
            j3 = np.zeros((n_I ** (t + 1), 3 ** t, 3))
            np.add.at(j3, (ki, ka, aseq[:, t]), 1.0 / n_traj)
            # I(Ĩ^t; A_t | A^{t−1}) = H(A_t|A^{t−1}) − H(A_t|A^{t−1},Ĩ^t)
            h_a_given_aprev = di.entropy_nats(j3.sum(axis=0)) - di.entropy_nats(j3.sum(axis=(0, 2)))
            h_a_given_both = di.entropy_nats(j3) - di.entropy_nats(j3.sum(axis=2))
            di_hat += h_a_given_aprev - h_a_given_both

        self.assertGreater(mi_hat, 5e-3)
        self.assertLess(abs(mi_hat - di_hat), 0.01)  # 采样容差内（注册表语义）

    def test_TDI1_log_contract_i_decoder(self):
        """P8.2 契约：干预模型的 I_t 字段记录探针符号（α），其余类为 0。"""
        dec = interventions.make_i_decoder(self.model)
        trajs = simulate.simulate_trajectories(self.model, seed=910002, T=3, n_traj=20,
                                               i_decoder=dec)
        n_I = self.n_I
        for tr in trajs:
            for rec in tr:
                self.assertEqual(rec["I_t"]["alpha"], float(rec["O_t"] % n_I))
                for cls in ("sigma", "beta", "gamma", "delta"):
                    self.assertEqual(rec["I_t"][cls], 0.0)


class TestTORG(unittest.TestCase):
    """命题 5.2：AX0 下 F_int>0；A_org∈(0,1]；零点语义。"""

    def test_TORG_wellposedness(self):
        m = toy_model()
        f_int = di.truth_F_int(m, T=6)
        self.assertGreater(f_int, 1e-6)  # AX0 ⇒ F_int>0（首项引理）
        a_org = di.truth_A_org(m, T=6)
        self.assertGreater(a_org, 0.0)
        self.assertLessEqual(a_org, 1.0 + 1e-12)
        # 无干预 ⇒ F_ext=0 ⇒ A_org=1
        self.assertAlmostEqual(a_org, 1.0, places=12)

    def test_TORG_zero_point_semantics(self):
        # π 不依赖 S（遥控/覆写见证）⇒ F_int=0
        m = toy_model_uniform_policy()
        self.assertAlmostEqual(di.truth_F_int(m, T=4), 0.0, places=12)
        # F_int+F_ext=0（0/0 病态，AX0 排除）⇒ A_org 显式报错
        with self.assertRaises(ValueError):
            di.truth_A_org(m, T=4)


class TestTMED(unittest.TestCase):
    """引理 7.2.1：α/σ 干预下 F_ext=0 精确成立（真值模式，容差 1e-12）＋中介见证。"""

    @classmethod
    def setUpClass(cls):
        m = interventions.apply_alpha(
            toy_model(), interventions.AlphaSpec.honest(n_I=2, response=1.0, fidelity=0.8))
        cls.model = interventions.apply_sigma(m, interventions.SigmaSpec.scaffold(flag_prob=0.5))

    def test_TMED_mediation_witnesses(self):
        # 非空判据：α 确实进入信念、σ 确实作用于资源（中介路径存活）
        mi_ib = di.probe_belief_mi(self.model, T=4)
        self.assertGreater(mi_ib[0], 1e-3)
        mi_iz = di.sigma_resource_mi(self.model, T=4)
        # σ 旗标在 t≥1 的资源抽取中生效（index 0 为初始分布，旗标与 z 独立）
        self.assertGreater(mi_iz[1], 1e-3)
        # 内部因果流存活（AX0 未被干预破坏）
        self.assertGreater(di.truth_F_int(self.model, T=4), 1e-6)

    def test_TMED_alpha_sigma_zero_residual(self):
        f_ext = di.truth_F_ext(self.model, T=4)
        self.assertAlmostEqual(f_ext, 0.0, places=12)  # 引理 7.2.1 精确成立
        self.assertAlmostEqual(di.truth_A_org(self.model, T=4), 1.0, places=12)


class TestTAX0(unittest.TestCase):
    """引理 4.1（SPEC_tests §2 T-AX0，第 3 步补登）：活性边＋全支撑 ⟺ I(S₁;A₁)>0。

    t=1 时 A₁ 只依赖 S₁：P(S₁,A₁)=init_S[s]·policy[s,a]，真值模式直接列表。
    """

    def test_TAX0_active_edge_full_support_positive_mi(self):
        m = toy_model()
        k = m.kernels
        self.assertTrue(np.all(k.init_S > 0.0))  # 全支撑先验
        # 活性边见证：存在两状态行的策略 TV 差 > 0（π(·|s) 两两不同于正测度集）
        tv = 0.5 * np.abs(k.policy[:, None, :] - k.policy[None, :, :]).sum(axis=-1)
        self.assertGreater(float(tv.max()), 0.0)
        joint = k.init_S[:, None] * k.policy  # P(S₁,A₁)
        i_sa = di.mi_nats(joint)
        self.assertGreater(i_sa, 1e-6)  # 引理 4.1(ii)：熵严格凹 ⇒ I(S₁;A₁)>0
        # 命题 5.2(i) 首项不等式：F_int ≥ I(S₁;A₁)>0
        self.assertGreaterEqual(di.truth_F_int(m, T=4), i_sa - 1e-12)

    def test_TAX0_no_active_edge_zero_mi(self):
        # 无活性边（π 行全同）⇒ A₁⫫S₁ ⇒ I=0（引理 4.1(i) 逆否方向）
        m = toy_model_uniform_policy()
        k = m.kernels
        joint = k.init_S[:, None] * k.policy
        self.assertAlmostEqual(di.mi_nats(joint), 0.0, places=12)


if __name__ == "__main__":
    unittest.main()
