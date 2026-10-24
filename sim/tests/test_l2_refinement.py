"""L2 平台：R8 构造效度敏感性臂的平台前提（SPEC_tests §5 步骤 7h；SPEC_platform v0.3）。

T-REF×7（X5 臂，SPEC_experiments v0.6 §8）：
①κ 派生逐点还原锚：默认档与 EXEC-1 档 = v0.2 半环桶；细化档（n_B=n_O=4）= 位置精确；
  退化档（n_B=1）≡ 0（P2.4）。
②桶先验 p_e 与策略张量在默认/EXEC-1 配置下与 v0.2 内联旧式逐点一致（零漂移回归钉）。
③endorse_step 表式锚：step=1 默认表 [1,1,1,2]；step=2 粗化表 [1,1,1,1]；
  细化网格（n_θ=7,θ*=2）表 [1,2,2,2,3,3,4]（P3.2）。
④植入目标通用化：默认网格 → 3（逐点还原 (θ*+2) mod n_θ）；细化网格 → 最大疏离端点 6（P9.3）。
⑤退化档见证：n_B=1 下 A_epi≡1 对全部 γ 强度（κ 登记义务非空洞的边界见证）。
⑥细化档预检：n_B=n_O=4 下 ATK-2 网格 A_epi 对 s(γ) 严格降（x-b 证伪器方向）。
"""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim import interventions  # noqa: E402
from autonomy_sim.env0 import (  # noqa: E402
    Env0Config, bucket_index, bucket_map, build_env0, endorse_table,
    refined_theta_table, utility_tables)
from autonomy_sim.scenarios import maximal_alienation_target  # noqa: E402
from autonomy_sim.wiring import truth_bundle  # noqa: E402


def _legacy_bucket_map(cfg):
    """v0.2 旧式（半环桶）——测试内对照实现，钉死逐点还原。"""
    return np.array([bucket_index(e, cfg.L, cfg.U) for e in range(cfg.L * cfg.U)],
                    dtype=int)


def _legacy_policy(cfg):
    """v0.2 旧式策略张量内联复现（半环均匀桶先验 + softmax(Q)）——零漂移回归钉。"""
    L, U = cfg.L, cfg.U
    n_E = L * U
    etab = endorse_table(cfg)
    u_tabs = utility_tables(cfg)
    n_S = cfg.n_theta * cfg.n_B * cfg.n_M * cfg.n_R
    p_e = np.zeros((cfg.n_B, n_E))
    for b in range(cfg.n_B):
        cells = [e for e in range(n_E) if bucket_index(e, L, U) == b]
        for e in cells:
            p_e[b, e] = 1.0 / len(cells)
    n_A = 5
    q_tab = np.zeros((n_S, n_A))
    for s in range(n_S):
        g, rem = divmod(s, cfg.n_B * cfg.n_M * cfg.n_R)
        b, _ = divmod(rem, cfg.n_M * cfg.n_R)
        for a in range(n_A):
            q_tab[s, a] = sum(p_e[b, e] * u_tabs[g, e, a] for e in range(n_E))
    q_tab -= q_tab.max(axis=1, keepdims=True)
    policy = np.exp(q_tab / cfg.alpha_temp)
    return policy / policy.sum(axis=1, keepdims=True)


class TestTRef(unittest.TestCase):
    """T-REF×7：X5 敏感性臂的平台前提（7h）。"""

    def test_TREF1_kappa_derivation_anchors(self):
        # ①默认档：逐点还原 v0.2 半环桶
        d = Env0Config()
        np.testing.assert_array_equal(bucket_map(d), _legacy_bucket_map(d))
        np.testing.assert_array_equal(bucket_map(d), [0, 0, 0, 0, 1, 1, 1, 1])
        # EXEC-1 档（n_O=4, n_B=2）：仍逐点还原半环桶（v0.2 行为零漂移）
        ex = Env0Config(n_O=4)
        np.testing.assert_array_equal(bucket_map(ex), _legacy_bucket_map(ex))
        # 细化档（n_B=n_O=4）：位置精确 κ(e)=x
        fine = Env0Config(n_B=4, n_O=4)
        np.testing.assert_array_equal(bucket_map(fine), [0, 0, 1, 1, 2, 2, 3, 3])
        # 退化档（n_B=1）：κ≡0
        deg = Env0Config(n_B=1)
        np.testing.assert_array_equal(bucket_map(deg), np.zeros(8, dtype=int))

    def test_TREF2_bucket_prior_policy_zero_drift(self):
        # ②默认与 EXEC-1 配置：策略张量与 v0.2 内联旧式逐点一致
        for cfg in (Env0Config(), Env0Config(n_O=4)):
            m = build_env0(cfg)
            np.testing.assert_allclose(m.kernels.policy, _legacy_policy(cfg),
                                       rtol=0, atol=1e-15)
        # 细化档：信念吸收核 b_of_o = min(o·n_B//n_O, n_B−1) = o（n_B=n_O=4）；
        # o≠b：吸收 0.85 至 b_of_o=o＋惯性 0.15 留在 b；o=b：叠加为 1.0
        m4 = build_env0(Env0Config(n_B=4, n_O=4))
        self.assertAlmostEqual(float(m4.kernels.belief[0, 0, 0]), 1.0, places=12)
        for o in (1, 2, 3):
            self.assertAlmostEqual(float(m4.kernels.belief[0, o, o]), 0.85, places=12)
            self.assertAlmostEqual(float(m4.kernels.belief[0, o, 0]), 0.15, places=12)

    def test_TREF3_endorse_step_table_anchors(self):
        # ③step=1（默认）：[1,1,1,2]（v0.2 逐点还原）
        np.testing.assert_array_equal(endorse_table(Env0Config()), [1, 1, 1, 2])
        # step=2（粗化档）：地板平台加倍 ⇒ 常值 [1,1,1,1]
        np.testing.assert_array_equal(endorse_table(Env0Config(endorse_step=2)),
                                      [1, 1, 1, 1])
        # 细化网格（n_θ=7, θ*=2, step=1）：[1,2,2,2,3,3,4]
        # （g=0: d=−2 ⇒ ⌊2·0.5⌋=1 ⇒ 1；g=6: d=4 ⇒ ⌊4·0.5⌋=2 ⇒ 4；θ*=2 吸收）
        fine = Env0Config(n_theta=7, theta_star=2,
                          theta_table=refined_theta_table(2))
        np.testing.assert_array_equal(endorse_table(fine), [1, 2, 2, 2, 3, 3, 4])

    def test_TREF4_alienation_target_generalization(self):
        # ④默认网格：逐点还原 (θ*+2) mod n_θ = 3
        self.assertEqual(maximal_alienation_target(Env0Config()), 3)
        # 细化网格（n_θ=7, θ*=2）：最大疏离端点 6；（n_θ=13, θ*=4）：12
        self.assertEqual(maximal_alienation_target(
            Env0Config(n_theta=7, theta_star=2,
                       theta_table=refined_theta_table(2))), 6)
        self.assertEqual(maximal_alienation_target(
            Env0Config(n_theta=13, theta_star=4,
                       theta_table=refined_theta_table(4))), 12)

    def test_TREF5_degenerate_kappa_epi_identity_one(self):
        # ⑤n_B=1：κ≡0 ⇒ P(B_t=κ(E_t))≡1 ⇒ A_epi≡1 对全部 γ 强度（构造性无信息见证）
        cfg = Env0Config(n_B=1)
        m0 = build_env0(cfg)
        for s in (0.0, 0.3, 0.6, 1.0):
            mg = interventions.apply_gamma(
                m0, interventions.GammaSpec.mix_constant(s, 0))
            b = truth_bundle(mg, T=2, baseline=m0)
            self.assertAlmostEqual(b.a_epi, 1.0, places=12)

    def test_TREF6_refined_kappa_epi_strictly_down(self):
        # ⑥细化档（n_B=n_O=4）：A_epi 对 s(γ) 严格降（x-b 证伪器方向预检）
        cfg = Env0Config(n_B=4, n_O=4)
        m0 = build_env0(cfg)
        epis = []
        for s in (0.0, 0.3, 0.6, 1.0):
            mg = interventions.apply_gamma(
                m0, interventions.GammaSpec.mix_constant(s, 0))
            epis.append(truth_bundle(mg, T=2, baseline=m0).a_epi)
        for x, y in zip(epis, epis[1:]):
            self.assertGreater(x, y + 1e-9)
        # 细化 ⇒ 精度任务变难 ⇒ 基线低于默认档（κ 敏感性报告义务的方向锚）
        m0d = build_env0(Env0Config())
        base_default = truth_bundle(m0d, T=2).a_epi
        self.assertLess(epis[0], base_default)

    def test_TREF7_goal_float_clip_contract(self):
        # ⑦A_goal 数值裁剪契约（沿 di.truth_A_org 的 E3 约定）：u_eff 在网格凸包内
        # ⇒ d≤d_c 为数学事实；浮点残差（~1e-16）致 a_goal 越出 [0,1] 时 1e-9 容差内
        # 归位（细化档 η=1 实测触发：u_idx=12.000000000000005 → −6.7e-16）；
        # 更大越界保持原值交由调用方检出（不静默掩盖）。
        from autonomy_sim.components import truth_A_goal
        etab = np.array([1, 1, 1, 2])
        endorse = lambda u: float(etab[int(round(u))])
        grid = [0.0, 1.0, 2.0, 3.0]
        # 完全俘获端的浮点残差：裁剪为精确 0
        g = truth_A_goal(3.0 + 5e-16, endorse, grid)
        self.assertEqual(g.point, 0.0)
        # θ* 下方的微小距离是合法读数（非越界）——保持在 1 的 1e-9 邻域内即可
        g = truth_A_goal(1.0 - 5e-16, endorse, grid)
        self.assertGreaterEqual(g.point, 1.0 - 1e-9)
        self.assertLessEqual(g.point, 1.0)
        # 超容差越界：保持原值（负点值——由调用方/复合层检出）
        g = truth_A_goal(3.0 + 1e-7, endorse, grid)
        self.assertLess(g.point, 0.0)
        # 端到端：finest 档（n_θ=13）η=1.0 复合不再抛分量越界
        cfg = Env0Config(n_theta=13, theta_star=4,
                         theta_table=refined_theta_table(4))
        m0 = build_env0(cfg)
        from autonomy_sim.scenarios import maximal_alienation_target
        mg = interventions.apply_beta_g(
            m0, interventions.BetaGSpec.plant(1.0, maximal_alienation_target(cfg)))
        b = truth_bundle(mg, T=2, baseline=m0, sigma=1.0)
        self.assertEqual(b.a_goal, 0.0)
        self.assertEqual(b.a_obj, 0.0)  # AX5 零歼灭保持


if __name__ == "__main__":
    unittest.main(verbosity=2)
