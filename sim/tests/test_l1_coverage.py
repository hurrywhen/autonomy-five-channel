"""L1 数学性质测试：干预覆盖与 T1（SPEC_tests §2 注册表 T-COV/T-T1a/T-T1d）。

- T-COV（附录定理 7.2.2/7.2.3）：覆盖表逐行见证——β_π⇒A_org 降（F_ext>0）；
  β_G⇒A_goal 降且 F_ext=0（A_org 盲）；γ⇒A_epi 降且 A_org 不动（盲见证）；
  δ⇒A_exec 严格降。β_Endorse 行登记推迟 ATK-5（T-COV 行注记）。
- T-T1a（附录 T1a）：随机配置扫描 0≤A≤1 恒成立＋E1 两侧反例（A=1/A=0 可达）。
- T-T1d（附录 T1d＋引理 2.4.1/推论 2.4.2）：TV≤ε 扰动 ⇒ 任意水平 α 检验功效 ≤α+ε；
  且存在非平凡 γ 使功效任意接近 α（ε 可任意小）。
"""
import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim import aggregate, components, di, empowerment, interventions, propagate, simulate  # noqa: E402
from autonomy_sim.di import entropy_nats
from autonomy_sim.fixtures import random_model, toy_model, toy_model_exec_deterministic  # noqa: E402
from autonomy_sim.rng import make_rng  # noqa: E402


def _g_marginal(model, T):
    al = model.alphabet
    aux = propagate.truth_step_joints(model, T)[-1]
    return aux["S"].reshape(al.n_G, al.n_B, al.n_M, al.n_R).sum(axis=(1, 2, 3))


def _o1_marginal(model):
    return propagate.truth_marginals(model, 1)[0].sum(axis=(0, 2))


def _best_power(p0, p1, alpha):
    """水平 α 最优（随机化 NP）检验功效：按似然比降序贪心填充（无穷比零成本拒绝）。"""
    n = len(p0)
    order = sorted(range(n), key=lambda o: (p1[o] / p0[o] if p0[o] > 0 else math.inf),
                   reverse=True)
    level = power = 0.0
    for o in order:
        if p0[o] <= 0:
            power += p1[o]  # P_0 零测集：拒绝不耗水平
            continue
        take = min(p0[o], alpha - level)
        if take <= 0:
            break
        power += (take / p0[o]) * p1[o]
        level += take
    return power


class TestTCOV(unittest.TestCase):
    """定理 7.2.2/7.2.3 覆盖表：四行数值见证（ceteris paribus）。"""

    def test_TCOV_beta_pi_a_org_drops(self):
        # β_π：iid 旗标 0.5/0.5 切换原策略与确定性对抗策略 ⇒ F_ext>0 ⇒ A_org 严格降
        m0 = toy_model()
        al = m0.alphabet
        alt = np.zeros((al.n_S, al.n_A))
        for s in range(al.n_S):
            alt[s, (2 * s + 1) % al.n_A] = 1.0
        mb = interventions.apply_beta_pi(
            m0, interventions.BetaPiSpec.switch([alt], flag_dist=(0.5, 0.5)))
        self.assertGreater(di.truth_F_int(mb, T=4), 1e-6)  # 内部流存活（部分篡改非全遥控）
        f_ext = di.truth_F_ext(mb, T=4)
        # 独立锚：Jensen 间隙 E_{S_t}[H(π̄)−Σ_i flag_i H(π_i)]，由输入 π_0/alt 直接计算
        pi0 = m0.kernels.policy
        expected = 0.0
        for aux in propagate.truth_step_joints(mb, 4):
            p_s = aux["S"]
            for s in range(al.n_S):
                mix = 0.5 * pi0[s] + 0.5 * alt[s]
                js = (entropy_nats(mix) - 0.5 * entropy_nats(pi0[s])
                      - 0.5 * entropy_nats(alt[s]))
                expected += float(p_s[s]) * js
        self.assertAlmostEqual(f_ext, expected, places=9)
        self.assertGreater(f_ext, 1e-3)
        a_org = di.truth_A_org(mb, T=4)
        self.assertLess(a_org, 1.0 - 1e-9)  # 覆盖行：β_π ⇒ A_org 严格降
        self.assertGreater(a_org, 0.0)
        # 基线对照：无干预 ⇒ F_ext=0、A_org=1
        self.assertAlmostEqual(di.truth_F_ext(m0, T=4), 0.0, places=12)
        self.assertAlmostEqual(di.truth_A_org(m0, T=4), 1.0, places=12)
        # 日志契约（P4.5）：β 旗标由 A_flat 解码，α/σ 字段为 0
        dec = interventions.make_i_decoder(mb)
        trajs = simulate.simulate_trajectories(mb, seed=910052, T=3, n_traj=10, i_decoder=dec)
        betas = [rec["I_t"]["beta"] for tr in trajs for rec in tr]
        self.assertEqual(set(betas), {0.0, 1.0})
        self.assertTrue(all(rec["I_t"]["alpha"] == 0.0 for tr in trajs for rec in tr))
        self.assertTrue(all(0 <= rec["A_t"] < al.n_A * 2 for tr in trajs for rec in tr))

    def test_TCOV_beta_g_blind_a_org_and_goal_drop(self):
        # β_G：internal 混合替换把 G 牵引至植入目标（静态手术）⇒ F_ext≡0（A_org 盲见证）
        m0 = toy_model()
        al = m0.alphabet
        g_init = _g_marginal(m0, 1)
        target = int(np.argmin(g_init))  # 植入目标取基线低概率 G（保证模态翻转可检）
        fix = int(np.argmax(g_init))
        mg = interventions.apply_beta_g(m0, interventions.BetaGSpec.plant(eta=0.4, target_g=target))
        self.assertAlmostEqual(di.truth_F_ext(mg, T=6), 0.0, places=12)  # E2.5(ii) 平凡零
        self.assertGreater(di.truth_F_int(mg, T=6), 1e-6)
        self.assertAlmostEqual(di.truth_A_org(mg, T=6), 1.0, places=12)  # 定理 7.2.3(i)：A_org 对 β_G 盲
        # A_goal 通道载体：G 边缘被牵向植入目标
        g0, g6 = _g_marginal(m0, 6), _g_marginal(mg, 6)
        self.assertGreater(float(g6[target]), 0.6)  # 植入质量主导
        self.assertGreater(0.5 * float(np.abs(g0 - g6).sum()), 0.1)
        # A_goal 代理（测试局部：Θ≡G 字母表，Fix=基线模态；完整 IRL 管线 E4.5 登记场景步）
        d_c = al.n_G - 1
        a_goal_base = 1.0 - abs(int(np.argmax(g0)) - fix) / d_c
        a_goal_beta = 1.0 - abs(int(np.argmax(g6)) - fix) / d_c
        self.assertEqual(a_goal_base, 1.0)
        self.assertLess(a_goal_beta, a_goal_base)  # 覆盖行：β_G ⇒ A_goal 降

    def test_TCOV_gamma_blind_a_org_epi_drops(self):
        # γ：通道操纵 ⇒ A_epi^real（精度化口径：相对真值精度）降而 A_org 不动（定理 7.2.3(i) 盲见证）
        m0 = toy_model()
        mg = interventions.apply_gamma(m0, interventions.GammaSpec.mix_constant(0.6, symbol=0))
        self.assertAlmostEqual(di.truth_F_ext(mg, T=4), 0.0, places=12)  # F_ext 可=0（B 中介）
        self.assertAlmostEqual(di.truth_A_org(mg, T=4), 1.0, places=12)  # A_org 不动（盲）
        # κ(e)=e mod n_B（与 toy 通道的粗粒化同构，显式传入）；基线因通道噪声精度 <1
        bmap = np.arange(m0.alphabet.n_E) % m0.alphabet.n_B
        epi_0 = components.truth_A_epi_real(m0, 4, bmap)
        epi_g = components.truth_A_epi_real(mg, 4, bmap)
        self.assertLess(epi_0.a_epi_real, 1.0)  # 基线精度 <1（观测噪声，特性非 bug）
        self.assertGreater(epi_g.d_bar, epi_0.d_bar + 1e-3)  # 失真由精度口径捕捉（实测 +0.10）
        self.assertLess(epi_g.a_epi_real, epi_0.a_epi_real - 1e-9)  # 覆盖行：γ ⇒ A_epi 降

    def test_TCOV_delta_a_exec_drops(self):
        # δ：可行集收缩 ⇒ ℰ^Π 严格降（确定性 fixture 解析锚：one-hot 移位信道族）
        m0 = toy_model_exec_deterministic()
        al = m0.alphabet
        aux = propagate.truth_step_joints(m0, 3)[2]
        channels, mask = empowerment.step_channels_from_esz(m0, aux["ESZ"])
        p_s = aux["S"]
        e_full = e_sub = 0.0
        for s, w_s in enumerate(channels):
            if not mask[s] or p_s[s] <= 0:
                continue
            # 解析锚：p(e|s)=δ_s ⇒ W_s 的行为 (s+a−1) mod 4 的 one-hot
            expect = np.zeros((al.n_A, al.n_O))
            for a in range(al.n_A):
                expect[a, (s + a - 1) % al.n_O] = 1.0
            self.assertTrue(np.allclose(w_s, expect))  # E3.7 信道导出逐元素核验
            c_full = empowerment.empowerment_support(w_s, (0, 1, 2))
            c_sub = empowerment.empowerment_support(w_s, (0, 1))
            self.assertAlmostEqual(c_full, math.log(3.0), places=9)
            self.assertAlmostEqual(c_sub, math.log(2.0), places=9)  # Faith：严格降逐状态成立
            self.assertEqual(empowerment.empowerment_support(w_s, (0,)), 0.0)  # 坍缩归零精确
            e_full += float(p_s[s]) * c_full
            e_sub += float(p_s[s]) * c_sub
        self.assertAlmostEqual(e_full, math.log(3.0), places=9)
        self.assertAlmostEqual(e_sub, math.log(2.0), places=9)
        self.assertLess(e_sub, e_full - 1e-6)  # 覆盖行：δ ⇒ A_exec 严格降（基线边缘加权，E3.7）
        # δ 算子契约：支撑收缩模型合法、强度登记、静态手术 F_ext≡0
        md = interventions.apply_delta(m0, interventions.DeltaSpec.contract((0, 1)))
        self.assertTrue(np.all(md.kernels.policy[:, 2] == 0.0))
        self.assertAlmostEqual(md.params["delta"]["strength"], 1 - 2 / 3, places=12)
        self.assertAlmostEqual(di.truth_F_ext(md, T=3), 0.0, places=12)


class TestTT1A(unittest.TestCase):
    """T1a（范围）：恒有 0≤A≤1——E1 两侧反例锚＋随机配置扫描。"""

    def test_TT1a_boundary_attained(self):
        # E1 上界反例（确定性全驱动＋完备自我拷贝＋无干预＋资源充裕）⇒ A=1
        ones = (1.0, 1.0, 1.0, 1.0, 1.0)
        for sigma in (0.5, 1.0):
            self.assertAlmostEqual(
                aggregate.composite_A(1.0, ones, (0.2,) * 5, sigma), 1.0, places=12)
        # E1 下界反例（AX0–2 满足但资源断供）⇒ A_via=0 ⇒ A=0
        for sigma in (0.5, 1.0):
            self.assertEqual(aggregate.composite_A(0.0, ones, (0.2,) * 5, sigma), 0.0)

    def test_TT1a_random_config_sweep(self):
        rng = make_rng(910051)
        n_skip = 0
        for _ in range(60):
            m = random_model(rng)
            f_int = di.truth_F_int(m, T=3)
            self.assertGreaterEqual(f_int, -1e-12)
            self.assertAlmostEqual(di.truth_F_ext(m, T=3), 0.0, places=9)  # 无干预零残余
            try:
                a_org = di.truth_A_org(m, T=3)
            except ValueError:
                n_skip += 1  # F_int≈0（0/0 病态，AX0 排除）——允许极少数跳过
                continue
            self.assertTrue(0.0 < a_org <= 1.0 + 1e-12)
            # 随机 A_goal（随机压缩 Endorse）
            grid = [i * 0.25 for i in range(5)]
            u_star = grid[int(rng.integers(5))]
            c = 0.3 + 0.6 * float(rng.random())
            g = components.truth_A_goal(float(rng.random()),
                                        lambda u: u_star + c * (u - u_star), grid)
            self.assertTrue(0.0 <= g.point <= 1.0)
            # 随机 A_exec（随机信道容量，支撑枚举＋KKT 证书）
            w_ch = rng.random((3, 4))
            w_ch /= w_ch.sum(axis=1, keepdims=True)
            c_ch, _ = empowerment.channel_capacity(w_ch)
            a_exec = empowerment.a_exec(c_ch, n=1, n_A=3)
            self.assertTrue(-1e-12 <= a_exec <= 1.0 + 1e-12)
            # 随机 A_epi（随机 γ 强度的 real 轨；精度化口径，κ(e)=e mod n_B 显式映射）
            s = float(rng.random())
            mg = interventions.apply_gamma(m, interventions.GammaSpec.mix_constant(s, symbol=0))
            bmap = np.arange(m.alphabet.n_E) % m.alphabet.n_B
            a_epi = components.truth_A_epi_real(mg, 3, bmap).a_epi_real
            self.assertTrue(-1e-12 <= a_epi <= 1.0 + 1e-12)
            # 随机 A_ref（非退化联合）
            joint = rng.random((3, 3)) + 0.01
            r = components.truth_A_ref(joint, float(rng.random()), float(rng.random()))
            self.assertFalse(r.degenerate)
            self.assertTrue(0.0 <= r.point <= 1.0)
            # 复合：T1a 主断言（分量数学上均在 [0,1]，1e-15 浮点残差归位）
            a_via = float(rng.random())
            w = rng.random(5)
            w /= w.sum()
            clip01 = lambda v: min(1.0, max(0.0, float(v)))
            comps = tuple(clip01(v) for v in (a_org, g.point, a_exec, a_epi, r.point))
            for sigma in (0.5, 1.0):
                a = aggregate.composite_A(a_via, comps, w, sigma)
                self.assertTrue(0.0 <= a <= 1.0 + 1e-12,
                                f"T1a 违例: A={a}, comps={comps}, σ={sigma}")
        self.assertLessEqual(n_skip, 3)


class TestTT1D(unittest.TestCase):
    """T1d＋引理 2.4.1/推论 2.4.2：TV≤ε ⇒ 水平 α 检验功效 ≤α+ε；ε 可任意小。"""

    def test_TT1d_power_bound_all_tests(self):
        m0 = toy_model()
        p0 = _o1_marginal(m0)
        n_O = m0.alphabet.n_O
        for s in (0.05, 0.3):
            mg = interventions.apply_gamma(m0, interventions.GammaSpec.mix_constant(s, symbol=0))
            p1 = _o1_marginal(mg)
            tv = 0.5 * float(np.abs(p1 - p0).sum())
            self.assertGreater(tv, 0.0)
            self.assertLessEqual(tv, s + 1e-12)  # 边缘 TV ≤ 核强度（压缩性）
            # 全部确定性检验（引理 2.4.1 的事件形式：power − level ≤ TV）
            for mask in range(1, 1 << n_O):
                region = np.array([(mask >> o) & 1 for o in range(n_O)], bool)
                level = float(p0[region].sum())
                power = float(p1[region].sum())
                self.assertLessEqual(power, level + tv + 1e-12)
            # 水平 α 最优随机化检验（推论 2.4.2：功效 ≤ α+ε）
            for alpha in (0.01, 0.05, 0.1):
                self.assertLessEqual(_best_power(p0, p1, alpha), alpha + tv + 1e-12)

    def test_TT1d_undetectable_gamma_exists(self):
        # T1d 存在性：s(γ)>0 非平凡而功效 − 水平 ≤ TV 可任意小
        m0 = toy_model()
        p0 = _o1_marginal(m0)
        alpha = 0.05
        advantages = {}
        for s in (0.02, 0.3):
            mg = interventions.apply_gamma(m0, interventions.GammaSpec.mix_constant(s, symbol=0))
            p1 = _o1_marginal(mg)
            tv = 0.5 * float(np.abs(p1 - p0).sum())
            self.assertGreater(tv, 0.0)  # 非平凡 γ（s(γ)>0 ⇒ 边缘可区分但任意弱）
            advantages[s] = _best_power(p0, p1, alpha) - alpha
        self.assertLessEqual(advantages[0.02], 0.02 + 1e-12)  # 功效 ≤ α+ε，ε=TV≤s
        self.assertLess(advantages[0.02], advantages[0.3])  # 随 s→0 不可检测性增强


if __name__ == "__main__":
    unittest.main()
