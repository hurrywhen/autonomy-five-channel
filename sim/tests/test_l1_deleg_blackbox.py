"""L1 数学性质测试：委托与黑盒（SPEC_tests §2 注册表 T-T7/T-T8/T-C0/T-BB/T-BB2）。

- T-T7（定理 7.7.1/7.7.2）：H1' 下 A_org=(1−m)A_org^self 精确；非 H1' 夹逼界成立
  （E12.3 记账约定：干预流=脚本内容；构造同时满足字面 H1' 与精确前提 (i)–(iii)）。
- T-T8（定理 7.8）：β_G/δ 强制 ⇒ A 严格降；σ ⇒ δ* 与 A_min 不降。
- T-C0（命题 8.1.2）：注入 vs 同文指令——行为分布逐点相同而 A_epi^real、Λ 可区分。
- T-BB（命题 10.4）：内生背书与植入背书两构造 (O^T,A^T) 相同（不可辨识性回归锚）。
- T-BB2（§10.2/§10.3）：黑盒区间界包含真值（η 不足反面控制）；A_exec^obs 方向的协议双锚。
"""
import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim import aggregate, blackbox, components, delegation, di, dynamics, interventions, propagate  # noqa: E402
from autonomy_sim.di import entropy_nats
from autonomy_sim.fixtures import toy_model, toy_model_exec_deterministic  # noqa: E402
from autonomy_sim.graph import Alphabet, CausalModel, Kernels  # noqa: E402

LN4 = math.log(4.0)


def _g_marginal(model, T):
    al = model.alphabet
    aux = propagate.truth_step_joints(model, T)[-1]
    return aux["S"].reshape(al.n_G, al.n_B, al.n_M, al.n_R).sum(axis=(1, 2, 3))


def _t7_policies():
    """T7 构造（n_A=16=(a1·4+a2)）：self——a1=S 确定＋a2 均匀噪声；del——a1=均匀脚本、a2=0。

    两政策逐状态条件熵均 ln4（字面 H1' ✓）；等熵转移 I(S;A|self)=脚本逐步熵=ln4 ✓；
    脚本臂 state-independent（不经 S ✓，E12.3 前提 (i)–(iii) 全满足）。
    """
    pol_self = np.zeros((4, 16))
    pol_del = np.zeros((4, 16))
    for s in range(4):
        for a in range(16):
            a1, a2 = divmod(a, 4)
            if a1 == s:
                pol_self[s, a] = 0.25
            if a2 == 0:
                pol_del[s, a] = 0.25
    return pol_self, pol_del


def _t7_model(policy, params=None):
    """T7/S≡G iid 均匀的最小模型（n_G=4，其余分量平凡）。"""
    al = Alphabet(n_E=1, n_O=1, n_A=policy.shape[1], n_G=4, n_B=1, n_M=1, n_R=1, n_Z=1)
    n_A = policy.shape[1]
    kernels = Kernels(
        obs=np.ones((1, n_A, 1)), belief=np.ones((1, 1, 1)),
        internal=np.full((4, 4), 0.25), policy=policy,
        env=np.ones((1, n_A, 1, 1)), resource=np.ones((1, 1)),
        init_E=np.array([1.0]), init_S=np.full(4, 0.25),
        init_Z=np.array([1.0]), init_A=np.full(n_A, 1.0 / n_A),
    )
    m = CausalModel(alphabet=al, kernels=kernels, params=params or {"fixture": "t7"})
    m.validate()
    return m


def _c0_model(init_E):
    """T-C0/T-BB 共享构造：确定性环境/观察/信念吸收（B_t=O_t=E_t），A 均匀。"""
    al = Alphabet(n_E=2, n_O=2, n_A=2, n_G=1, n_B=2, n_M=1, n_R=1, n_Z=1)
    obs = np.zeros((2, 2, 2))
    for e in range(2):
        obs[e, :, e] = 1.0
    belief = np.zeros((2, 2, 2))
    for b in range(2):
        for o in range(2):
            belief[b, o, o] = 1.0
    env = np.zeros((2, 2, 1, 2))
    for e in range(2):
        env[e, :, 0, e] = 1.0
    kernels = Kernels(
        obs=obs, belief=belief, internal=np.ones((1, 1)),
        policy=np.full((al.n_S, 2), 0.5), env=env, resource=np.ones((1, 1)),
        init_E=init_E, init_S=np.full(al.n_S, 1.0 / al.n_S),
        init_Z=np.array([1.0]), init_A=np.array([0.5, 0.5]),
    )
    m = CausalModel(alphabet=al, kernels=kernels, params={"fixture": "c0"})
    m.validate()
    return m


def _oa_marginals(model, T):
    """(O_t,A_t) 逐步精确边缘列表。"""
    return [marg.sum(axis=0) for marg in propagate.truth_marginals(model, T)]


class TestTT7(unittest.TestCase):
    """定理 7.7.1/7.7.2：委托治理律的线性律与夹逼界。"""

    def test_TT7_h1_linear_law_exact(self):
        pol_self, pol_del = _t7_policies()
        m_self = _t7_model(pol_self)
        T = 3
        f_self = di.truth_F_int(m_self, T)
        self.assertAlmostEqual(f_self, T * LN4, places=9)  # 自臂每步 I(S;A)=ln4（a1=S 全揭示）
        # 前提核验：字面 H1'（逐状态条件熵相等）＋脚本臂 state-independent
        for s in range(4):
            self.assertAlmostEqual(entropy_nats(pol_self[s]), LN4, places=12)
            self.assertAlmostEqual(entropy_nats(pol_del[s]), LN4, places=12)
        self.assertTrue(np.allclose(pol_del, pol_del[0]))
        for m in (0.0, 0.3, 0.5, 0.9, 1.0):
            md = interventions.apply_beta_pi(
                m_self, interventions.BetaPiSpec.switch([pol_del], flag_dist=(1.0 - m, m)))
            f_int = di.truth_F_int(md, T)
            # 内部流按 (1−m) 缩放（脚本臂无 S 流）
            self.assertAlmostEqual(f_int, delegation.f_int_mixed(f_self, m), places=9)
            # 外部流=脚本熵转移 m·C̃·T ⇒ A_org=(1−m)·A_org^self 精确（A_org^self=1）
            f_ext = delegation.f_ext_script(LN4, m, T)
            a_org = f_int / (f_int + f_ext)
            self.assertAlmostEqual(a_org, delegation.a_org_h1(1.0, m), places=9)

    def test_TT7_bracket_non_h1(self):
        # 非 H1'：脚本熵转移 C_del=ln2 ≠ C_self=ln4 ⇒ ρ=0.5，夹逼界逐点精确
        pol_self, _ = _t7_policies()
        pol_del2 = np.zeros((4, 16))
        for a in (0, 4):
            pol_del2[:, a] = 0.5  # 脚本均匀于 2 符号（a1∈{0,1}、a2=0），熵 ln2
        m_self = _t7_model(pol_self)
        T = 3
        f_self = di.truth_F_int(m_self, T)
        rho = math.log(2.0) / LN4
        for m in (0.2, 0.5, 0.8):
            md = interventions.apply_beta_pi(
                m_self, interventions.BetaPiSpec.switch([pol_del2], flag_dist=(1.0 - m, m)))
            f_int = di.truth_F_int(md, T)
            f_ext = delegation.f_ext_script(math.log(2.0), m, T)
            a_org = f_int / (f_int + f_ext)
            # ρ 精确 ⇒ 夹逼两端重合于编译值
            lo, hi = delegation.a_org_bracket(1.0, m, rho, rho)
            self.assertAlmostEqual(a_org, lo, places=9)
            self.assertAlmostEqual(lo, hi, places=12)
            # ρ 区间估计 ⇒ 编译值被严格包含
            lo2, hi2 = delegation.a_org_bracket(1.0, m, 0.4, 0.6)
            self.assertLess(lo2, a_org)
            self.assertGreater(hi2, a_org)


class TestTT8(unittest.TestCase):
    """定理 7.8（强制悖论）：β_G/δ ⇒ A 严格降；σ ⇒ δ* 与 A_min 不降。"""

    def test_TT8_coercion_and_scaffold(self):
        W5 = (0.2,) * 5
        m0 = toy_model()
        a_org0 = di.truth_A_org(m0, T=4)
        a0 = aggregate.composite_A(1.0, (a_org0, 1.0, 1.0, 1.0, 1.0), W5, 1.0)
        # (i-a) β_G 强制（植入目标）：A_goal 代理严格降（T-COV 见证）⇒ A 严格降
        al = m0.alphabet
        g_init = _g_marginal(m0, 1)
        target, fix = int(np.argmin(g_init)), int(np.argmax(g_init))
        mg = interventions.apply_beta_g(m0, interventions.BetaGSpec.plant(0.4, target))
        g6 = _g_marginal(mg, 6)
        a_goal_proxy = 1.0 - abs(int(np.argmax(g6)) - fix) / (al.n_G - 1)
        self.assertLess(a_goal_proxy, 1.0)
        a_g = aggregate.composite_A(1.0, (a_org0, a_goal_proxy, 1.0, 1.0, 1.0), W5, 1.0)
        self.assertLess(a_g, a0)
        # (i-b) δ 强制（行动约束）：A_exec 降（解析锚 ℰ: log3→log2）⇒ A 严格降
        a_exec_delta = math.log(2.0) / math.log(3.0)
        a_d = aggregate.composite_A(1.0, (a_org0, 1.0, a_exec_delta, 1.0, 1.0), W5, 1.0)
        self.assertLess(a_d, a0)
        # (ii) σ 脚手架：δ* 与 A_min 不降
        th, W, r, c0 = 0.5, 2.0, 2.0, 0.4
        kap0, kap1 = 0.2, 0.3  # σ 提升 ε ⇒ κ=χεv 升
        ds0 = dynamics.delta_star(th, W, kap0, r, c0)  # min(0.25,0.2,0.4)=0.2（κ binding）
        ds1 = dynamics.delta_star(th, W, kap1, r, c0)  # min(0.25,0.3,0.4)=0.25（θ/W binding）
        self.assertGreater(ds1, ds0)  # ∂δ*/∂ε>0 于 κ-binding 段（命题 7.6.7）
        ds2 = dynamics.delta_star(th, W, 0.5, r, c0)  # 平台段（θ/W 持续 binding）
        self.assertGreaterEqual(ds2, ds1)
        am0 = dynamics.a_min(0.9, (0.8,) * 5, W5, (ds0,) * 5, (kap0,) * 5)
        am1 = dynamics.a_min(0.9, (0.8,) * 5, W5, (ds1,) * 5, (kap1,) * 5)
        am2 = dynamics.a_min(0.9, (0.8,) * 5, W5, (ds2,) * 5, (0.5,) * 5)
        self.assertGreater(am1, am0)  # binding 切换：δ*/κ=1 ⇒ 0 → 正（严格升）
        self.assertGreaterEqual(am2, am1)  # κ 续升使 (1−δ*/κ) 增大 ⇒ 不降


class TestTC0(unittest.TestCase):
    """命题 8.1.2：注入 vs 同文指令——行为相同而 A_epi^real、Λ 可区分。"""

    def test_TC0_injection_vs_instruction(self):
        c = 1
        # Z1（同文指令）：E_t≡c（指令即在环境中），obs 忠实 ⇒ 诚实信念形成（机制完整）
        z1 = _c0_model(init_E=np.array([0.0, 1.0]))
        # Z2（隐蔽注入，ATK-4 语义）：γ 把 obs 替换为常值 c（与 e 无关，绕过登记）
        z2_base = _c0_model(init_E=np.array([0.5, 0.5]))
        z2 = interventions.apply_gamma(z2_base, interventions.GammaSpec.mix_constant(1.0, symbol=c))
        # 行为分布 (O^T,A^T) 逐步逐点相同（TV=0 精确；三框架行为基剖面随之相同——推论 8.1.3）
        T = 4
        for j1, j2 in zip(_oa_marginals(z1, T), _oa_marginals(z2, T)):
            self.assertTrue(np.allclose(j1, j2, atol=1e-12), f"行为边缘不同: {j1} vs {j2}")
        # A_epi^real（2026-10-15 精度化口径，κ=恒等映射 n_E=n_B=2）：Z1 无 γ 且 E≡c 忠实 ⇒ 1；
        # Z2 信念被钉到常值桶 c 而 E 均匀 ⇒ P(B=κ(E))=0.5
        self.assertNotIn("gamma", z1.params)
        self.assertAlmostEqual(components.truth_A_epi_real(z1, T, np.arange(2)).a_epi_real, 1.0, places=12)
        epi2 = components.truth_A_epi_real(z2, T, np.arange(2))
        self.assertAlmostEqual(epi2.d_bar, 0.5, places=12)  # B=δ_c 钉死 vs κ(E) 均匀
        self.assertAlmostEqual(epi2.a_epi_real, 0.5, places=12)
        # Λ（E12.6 标记级）：Z2 手术史含未登记 γ ⇒ 0.5；Z1 ⇒ 1.0
        self.assertEqual(blackbox.lambda_history(z1.params), 1.0)
        self.assertLess(blackbox.lambda_history(z2.params), blackbox.lambda_history(z1.params))


class TestTBB(unittest.TestCase):
    """命题 10.4：内生背书 vs 植入背书——观测不可辨识性回归锚。"""

    def test_TBB_endo_vs_implanted_identical_behavior(self):
        g_star = 1
        al = Alphabet(n_E=2, n_O=2, n_A=2, n_G=2, n_B=2, n_M=1, n_R=1, n_Z=1)
        obs = np.zeros((2, 2, 2))
        for e in range(2):
            obs[e, :, e] = 1.0
        belief = np.zeros((2, 2, 2))
        for b in range(2):
            for o in range(2):
                belief[b, o, o] = 1.0
        policy = np.zeros((al.n_S, 2))
        for s in range(al.n_S):
            g, b, _m, _r = al.split_S(s)
            policy[s, b] = 1.0  # 行为规范 π*：A_t=B_t（两构造共用）
        env = np.zeros((2, 2, 1, 2))
        for e in range(2):
            env[e, :, 0, e] = 1.0
        init_S = np.zeros(al.n_S)
        for b in range(2):
            init_S[al.join_S(g_star, b, 0, 0)] = 0.5  # G₀=g*（内生收敛终点=植入目标）
        # M_endo：internal 收敛锚定 g*（从任意 G 一步到 g*）；M_impl：t=0 β 植入＋internal≡id
        internal_endo = np.zeros((al.n_GMR, al.n_GMR))
        for gmr in range(al.n_GMR):
            _g, rem = divmod(gmr, al.n_M * al.n_R)
            m_, r_ = divmod(rem, al.n_R)
            internal_endo[gmr, (g_star * al.n_M + m_) * al.n_R + r_] = 1.0
        internal_impl = np.eye(al.n_GMR)

        def build(internal, params):
            kernels = Kernels(
                obs=obs, belief=belief, internal=internal, policy=policy,
                env=env, resource=np.ones((1, 1)),
                init_E=np.array([0.5, 0.5]), init_S=init_S,
                init_Z=np.array([1.0]), init_A=np.array([0.5, 0.5]),
            )
            m = CausalModel(alphabet=al, kernels=kernels, params=params)
            m.validate()
            return m

        m_endo = build(internal_endo, {"fixture": "bb_endo"})
        m_impl = build(internal_impl,
                       {"fixture": "bb_impl", "beta_G": {"kind": "implant_t0", "target_g": g_star}})
        # (E,O,A) 全联合逐步逐点相同（命题 10.4 的 P(O^T,A^T) 相同为其推论）
        T = 5
        for me, mi in zip(propagate.truth_marginals(m_endo, T), propagate.truth_marginals(m_impl, T)):
            self.assertTrue(np.allclose(me, mi, atol=1e-12))
        # 白盒 A_org 亦相同（静态手术史无持续 I 流 ⇒ F_ext≡0 两者）——黑盒泛函更无从区分
        self.assertAlmostEqual(di.truth_A_org(m_endo, T), di.truth_A_org(m_impl, T), places=12)
        # 唯一区分在因果史：Λ（E12.6 标记级）endo=1 vs impl=0.5
        self.assertEqual(blackbox.lambda_history(m_endo.params), 1.0)
        self.assertLess(blackbox.lambda_history(m_impl.params), 1.0)


class TestTBB2(unittest.TestCase):
    """§10.2 区间界与 §10.3 方向（协议双锚）。"""

    def test_TBB2_a_org_interval_contains_truth(self):
        m0 = toy_model()
        T = 4
        f_base = di.truth_F_int(m0, T)
        al = m0.alphabet
        script = np.full((al.n_S, al.n_A), 1.0 / al.n_A)  # state-independent 均匀脚本
        mp = interventions.apply_beta_pi(
            m0, interventions.BetaPiSpec.switch([script], flag_dist=(0.9, 0.1)))
        f_true = di.truth_F_int(mp, T)  # 测量期有效内部流（白盒）
        f_obs = blackbox.probe_flow_obs(mp, T)  # 黑盒可观测外部流（无需 S）
        self.assertAlmostEqual(f_obs, 0.1 * math.log(al.n_A) * T, places=9)
        a_true = f_true / (f_true + f_obs)
        # 语义前提：F_int 漂移 ≤η=0.2（含探针稀释与动力学偏移）
        self.assertGreaterEqual(f_true, f_base * 0.8)
        self.assertLessEqual(f_true, f_base * 1.2)
        lo, hi = blackbox.a_org_interval(f_base, 0.2, f_obs)
        self.assertLessEqual(lo, a_true)
        self.assertLessEqual(a_true, hi)
        # 反面控制：η=0.01 不覆盖探针稀释 ⇒ 下界高于真值（区间不含——η 的必要性）
        lo2, _ = blackbox.a_org_interval(f_base, 0.01, f_obs)
        self.assertGreater(lo2, a_true)

    def test_TBB2_a_exec_obs_direction_protocols(self):
        # 附录方向（策略驱动被动观察）：A 随 S 确定性变化 ⇒ 状态熵混入 ⇒ obs>cond
        m = toy_model_exec_deterministic()
        al = m.alphabet
        m.kernels.policy = np.array([[1.0 if a == s % al.n_A else 0.0 for a in range(al.n_A)]
                                     for s in range(al.n_S)])  # A_t = S_t mod |𝒜|（确定性 S 驱动）
        m.params = {**m.params, "fixture": "exec_policy_driven"}
        m.validate()
        i_obs_pd, i_cond_pd = blackbox.a_exec_blackbox(m, t=2, policy_driven=True)
        self.assertEqual(i_cond_pd, 0.0)  # 给定 S 行动恒定 ⇒ cond=0 精确
        self.assertGreater(i_obs_pd, 1e-3)  # obs>0=cond ⇒ A_exec^obs≥A_exec 严格（附录方向）
        # 独立探针协议（同一模型）：A⊥S ⇒ 条件化去噪 ⇒ obs≤cond（方向相反，协议前提）
        i_obs_pr, i_cond_pr = blackbox.a_exec_blackbox(m, t=2, policy_driven=False)
        self.assertLess(i_obs_pr, i_cond_pr + 1e-9)


if __name__ == "__main__":
    unittest.main()
