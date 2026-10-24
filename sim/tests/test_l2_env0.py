"""L2 平台冒烟：ENV-0 与分量束接线（SPEC_tests §3 注册表 X-ENV0；SPEC_platform §9）。

- 构建合法且决定性（同一配置两次构建 config_hash 一致）；
- S 分量语义往返（split_S/join_S）；Endorse 量化压缩使 G 边际向 θ* 集中；
- 基线分量束锚：A_org=A_goal=Λ=1、A_epi=实测精度锚<1（观测噪声特性，2026-10-15 精度化口径），A∈[0,1]，AI≈0；
- β_G 接线：F_ext≡0（A_org 盲）、Λ=1−η、G 移位至植入目标、行为边际改变；
- γ 接线：A_epi 低于基线精度 而 Â_phen 不降 ⇒ AI>0（幻觉签名）、Λ=1−s(γ)。
"""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim import di, interventions, propagate  # noqa: E402
from autonomy_sim.env0 import ACTIONS, Env0Config, build_env0, endorse_table  # noqa: E402
from autonomy_sim.wiring import law_level_lambda, truth_bundle  # noqa: E402


def _g_marginal(model, T):
    al = model.alphabet
    aux = propagate.truth_step_joints(model, T)[-1]
    return aux["S"].reshape(al.n_G, al.n_B, al.n_M, al.n_R).sum(axis=(1, 2, 3))


class TestXENV0(unittest.TestCase):
    """X-ENV0：场景层基础设施冒烟（7a 子步）。"""

    @classmethod
    def setUpClass(cls):
        cls.cfg = Env0Config()
        cls.m0 = build_env0(cls.cfg)

    def test_XENV0_build_valid_and_deterministic(self):
        m1 = build_env0(Env0Config())
        m1.validate()
        # 决定性：纯配置构建（无 RNG）⇒ config_hash 一致
        self.assertEqual(self.m0.to_dict(), m1.to_dict())
        # 字母表与配置一致
        al = self.m0.alphabet
        self.assertEqual(al.n_E, self.cfg.L * self.cfg.U)
        self.assertEqual(al.n_A, len(ACTIONS))
        self.assertEqual(al.n_S, self.cfg.n_theta * self.cfg.n_B * self.cfg.n_M * self.cfg.n_R)

    def test_XENV0_s_semantics_and_endorse_contraction(self):
        al = self.m0.alphabet
        # S 语义往返
        for s in range(al.n_S):
            g, b, m, r = al.split_S(s)
            self.assertEqual(al.join_S(g, b, m, r), s)
        # Endorse 表：θ* 吸收、其余向 θ* 收缩（一步 |Δ|≥1 减）
        etab = endorse_table(self.cfg)
        self.assertEqual(etab[self.cfg.theta_star], self.cfg.theta_star)
        for g in range(al.n_G):
            self.assertLessEqual(abs(etab[g] - self.cfg.theta_star),
                                 abs(g - self.cfg.theta_star))
        # G 边际向 θ* 集中（量化压缩数值核验）
        p_g1 = _g_marginal(self.m0, 1)[self.cfg.theta_star]
        p_g2 = _g_marginal(self.m0, 2)[self.cfg.theta_star]
        self.assertGreater(p_g2, p_g1)
        self.assertGreater(p_g2, 0.9)

    def test_XENV0_baseline_bundle(self):
        b = truth_bundle(self.m0, T=2)
        self.assertAlmostEqual(b.a_org, 1.0, places=9)   # 无干预 ⇒ F_ext=0
        # 精度锚（2026-10-15 精度化口径）：观测噪声 ⇒ 基线 A_epi<1（特性非 bug，T1c D1）。
        # 数值来源：wiring 新语义实现后 REPL 复核（逐步精度 [0.7975, 0.824495] 的均值）
        self.assertAlmostEqual(b.a_epi, 0.810997748751, places=9)
        self.assertLess(b.a_epi, 1.0)
        self.assertAlmostEqual(b.a_goal, 1.0, places=12)  # 模态 G=θ*（Endorse 收敛）
        self.assertAlmostEqual(b.lam, 1.0, places=12)
        self.assertGreater(b.a_exec, 0.0)
        self.assertGreater(b.a_ref, 0.0)
        self.assertGreater(b.a_via, 0.0)
        self.assertTrue(0.0 < b.a_obj <= 1.0)
        self.assertTrue(0.0 < b.a_phen <= 1.0)
        self.assertAlmostEqual(b.ai, 0.0, places=9)     # 基线无幻觉（phen 参照轨=自身 ⇒ 精确 0）

    def test_XENV0_beta_g_blind_lambda_goal(self):
        target = (self.cfg.theta_star + 2) % self.cfg.n_theta  # 最大疏离方向
        mg = interventions.apply_beta_g(
            self.m0, interventions.BetaGSpec.plant(eta=1.0, target_g=target))
        self.assertAlmostEqual(di.truth_F_ext(mg, T=2), 0.0, places=12)  # 静态手术平凡零
        self.assertAlmostEqual(di.truth_A_org(mg, T=2), 1.0, places=12)  # A_org 盲
        self.assertAlmostEqual(law_level_lambda(mg.params), 0.0, places=12)  # Λ=1−η=0
        # G 全移位至植入目标（η=1 ⇒ G_t≡target）⇒ A_goal=0（d=d_c 完全俘获）
        g2 = _g_marginal(mg, 2)
        self.assertEqual(int(np.argmax(g2)), target)
        self.assertGreater(float(g2[target]), 0.99)
        b = truth_bundle(mg, T=2, baseline=self.m0)
        self.assertAlmostEqual(b.a_goal, 0.0, places=12)
        self.assertAlmostEqual(b.a_obj, 0.0, places=12)  # AX5：通道归零 ⇒ A=0
        self.assertGreater(b.ai, 0.0)  # Â_phen 不随植入降 ⇒ AI>0
        # 行为改变：A 边际 TV>0（θ 权重变 ⇒ Q 变 ⇒ π 变）
        a0 = propagate.truth_marginals(self.m0, 2)[-1].sum(axis=(0, 1))
        a1 = propagate.truth_marginals(mg, 2)[-1].sum(axis=(0, 1))
        self.assertGreater(0.5 * float(np.abs(a0 - a1).sum()), 1e-3)

    def test_XENV0_gamma_hallucination_signature(self):
        s = 0.5
        mg = interventions.apply_gamma(
            self.m0, interventions.GammaSpec.mix_constant(s, symbol=0))
        b = truth_bundle(mg, T=2, baseline=self.m0)
        # 精度化口径：γ garbling ⇒ 精度严格低于基线（实测 0.810998→0.655843，损失 0.155）
        self.assertLess(b.a_epi, truth_bundle(self.m0, T=2).a_epi - 0.05)
        self.assertAlmostEqual(b.a_phen, truth_bundle(self.m0, T=2).a_phen, places=12)
        # 自我模型只认已登记影响 ⇒ Â_phen 不降 ⇒ AI>0（幻觉签名，T3b 胚胎）
        self.assertGreater(b.ai, 1e-9)
        # s(γ)=ess sup TV（核依赖，独立核验：TV=s·(1−p_row[symbol])）⇒ Λ=1−s(γ)
        obs0 = self.m0.kernels.obs
        one_hot = np.eye(self.m0.alphabet.n_O)[0]
        expect_s = max(0.5 * float(np.abs(obs0[e, 0] - ((1 - s) * obs0[e, 0] + s * one_hot)).sum())
                       for e in range(self.m0.alphabet.n_E))
        self.assertAlmostEqual(mg.params["gamma"]["s"], expect_s, places=12)
        self.assertAlmostEqual(b.lam, 1.0 - expect_s, places=12)


if __name__ == "__main__":
    unittest.main()
