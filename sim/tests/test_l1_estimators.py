"""L1 估计路径两路径对照（SPEC_tests §2：T-EST-ORG/VIA/GOAL/EPI/EXEC；
SPEC_estimators §14 E14.1–E14.6 接口与 §13 数值记录载体）。

每分量在合成配置上"真值=估计（容差内）"：估计路径从 P8.2 步级日志（trajs）出发，
真值路径由 propagate/di/blackbox 精确给出。区间=8 块 95% 正态半宽（E14.6）。
"""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim import components, di, interventions, propagate, simulate  # noqa: E402
from autonomy_sim.blackbox import a_org_interval, probe_flow_obs  # noqa: E402
from autonomy_sim.env0 import Env0Config, build_env0  # noqa: E402
from autonomy_sim.estimators import (  # noqa: E402
    estimate_epi_accuracy, estimate_g_mean, estimate_mi_action_obs, estimate_probe_flow,
    estimate_z_high,
)
from autonomy_sim.fixtures import toy_model  # noqa: E402
from autonomy_sim.wiring import derive_bucket_map  # noqa: E402


class TestTEstOrg(unittest.TestCase):
    """T-EST-ORG（E14.1）：探针流采样插件 vs 真值闭式；A_org 区间含可观测重建真值。"""

    @classmethod
    def setUpClass(cls):
        cls.m0 = toy_model()
        al = cls.m0.alphabet
        script = np.tile(np.full(al.n_A, 1.0 / al.n_A), (al.n_S, 1))
        cls.mp = interventions.apply_beta_pi(
            cls.m0, interventions.BetaPiSpec.switch([script], flag_dist=(0.8, 0.2)))
        cls.T, cls.n_I = 3, 2
        dec = interventions.make_i_decoder(cls.mp)
        cls.trajs = simulate.simulate_trajectories(cls.mp, 910099, cls.T, 4000, i_decoder=dec)

    def test_TESTORG_probe_flow_two_paths(self):
        est = estimate_probe_flow(self.trajs, n_I=self.n_I, n_A=self.m0.alphabet.n_A)
        truth = probe_flow_obs(self.mp, self.T)
        self.assertGreater(truth, 0.1)  # 非空见证
        self.assertLessEqual(abs(est.point - truth),
                             est.half + est.diag["mm_bias"] + 0.01)

    def test_TESTORG_a_org_interval_contains_truth(self):
        est = estimate_probe_flow(self.trajs, n_I=self.n_I, n_A=self.m0.alphabet.n_A)
        f_base = di.truth_F_int(self.m0, self.T)
        f_int_true = di.truth_F_int(self.mp, self.T)
        f_obs_true = probe_flow_obs(self.mp, self.T)
        a_true = f_int_true / (f_int_true + f_obs_true)  # E2.4 可观测重建（BB-1 同式）
        lo, hi = a_org_interval(f_base, 0.3, est.point)
        self.assertLessEqual(lo - 1e-9, a_true)
        self.assertLessEqual(a_true, hi + 1e-9)


class TestTEstEnv0(unittest.TestCase):
    """env0 基线/γ 臂的四分量采样对照（E14.2–E14.5）。"""

    @classmethod
    def setUpClass(cls):
        cls.cfg = Env0Config()
        cls.m0 = build_env0(cls.cfg)
        cls.mg = interventions.apply_gamma(
            cls.m0, interventions.GammaSpec.mix_constant(0.5, symbol=0))
        cls.T, cls.n_traj = 3, 2000
        cls.trajs0 = simulate.simulate_trajectories(cls.m0, 910098, cls.T, cls.n_traj)
        cls.trajs_g = simulate.simulate_trajectories(cls.mg, 910098, cls.T, cls.n_traj)
        cls.j0 = propagate.truth_step_joints(cls.m0, cls.T)
        cls.jg = propagate.truth_step_joints(cls.mg, cls.T)

    def test_TESTVIA_z_high(self):
        est = estimate_z_high(self.trajs0, n_Z=self.m0.alphabet.n_Z)
        truth = float(np.mean([aux["Z"][1] for aux in self.j0]))  # n_is=1 ⇒ 高位=z≥1
        self.assertLessEqual(abs(est.point - truth), est.half + 0.02)

    def test_TESTGOAL_g_mean(self):
        est = estimate_g_mean(self.trajs0, self.m0.alphabet)
        s_fin = self.j0[-1]["S"].reshape(self.m0.alphabet.n_G, -1).sum(axis=1)
        truth = float(np.dot(s_fin, np.arange(self.m0.alphabet.n_G)))
        self.assertLessEqual(abs(est.point - truth), est.half + 0.02)

    def test_TESTEPI_accuracy(self):
        # E14.4 精度化口径（2026-10-15）：γ=0.5 臂日志直读命中率 ≈ 真值精度（κ 同真值路径）
        bmap = derive_bucket_map(self.mg)
        est = estimate_epi_accuracy(self.trajs_g, bmap)
        truth = components.truth_A_epi_real(self.mg, self.T, bmap).a_epi_real
        base = components.truth_A_epi_real(self.m0, self.T, bmap).a_epi_real
        self.assertGreater(base - truth, 0.05)  # 非空见证（γ=0.5 garbling 精度损失 ≈0.15，T=3）
        self.assertLessEqual(abs(est.point - truth), est.half + 0.03)

    def test_TESTEXEC_mi_action_obs(self):
        # 强 S 依赖域（锐化温度臂，BB-1 ② 同口径——附录方向的协议前提域）：
        # 基线臂 I(A;O)≈1e-4 退化（插件偏差主导），非空见证与定量对照取锐化臂
        al = self.m0.alphabet
        m_sharp = build_env0(Env0Config(alpha_temp=0.05))
        trajs = simulate.simulate_trajectories(m_sharp, 910097, 3, 8000)
        est = estimate_mi_action_obs(trajs, t=1, n_A=al.n_A, n_O=al.n_O)
        from autonomy_sim.blackbox import a_exec_blackbox
        i_obs, _ = a_exec_blackbox(m_sharp, t=1, policy_driven=True)
        self.assertGreater(i_obs, 1e-3)  # 非空见证
        self.assertLessEqual(abs(est.point - i_obs), est.half + est.diag["mm_bias"] + 0.005)


if __name__ == "__main__":
    unittest.main()
