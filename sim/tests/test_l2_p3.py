"""L1/L2/L3 混合：P3 审稿包测试（SPEC_tests v0.5 注册——T-AVIA-ENV／T-OBS-N4／T-DEL1-F／
X-EROSION／X-EXEC1／X-P3-ANALYSIS）。

- T-AVIA-ENV：扩展 A_via 闸门（SPEC_estimators §7 v0.5）——默认 m=1 回归锚（逐点等于
  资源型旧式）、κ/R 单因子归零、min 绑定、clip 上界、登记需求正性校验；
- T-OBS-N4：n_O 泛化（SPEC_platform P9.1 v0.2）——默认 n_O=2 逐点还原 v1 公式（后退兼容锚）、
  n_O=4 构建合法且 I(O;E)>0；
- T-DEL1-F：DEL-1⑤⑥（SPEC_experiments v0.5）——f>0 臂旗标熵进入 F_ext 律级路径、
  线性律失效、φ-松弛双侧夹逼含实测；ρ=1.5 臂夹逼含真值；
- X-EROSION／X-EXEC1：场景冒烟（小网格，判据全 CONFIRMED）；
- X-P3-ANALYSIS：analysis_p3.py 在微型矩阵产出上跑通，X1–X4 schema 与数值域合法。
"""
import json
import math
import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from autonomy_sim import di, interventions, propagate  # noqa: E402
from autonomy_sim.env0 import Env0Config, build_env0  # noqa: E402
from autonomy_sim.scenarios import (  # noqa: E402
    _calibrate_script, scenario_erosion, scenario_exec1)
from autonomy_sim.wiring import truth_bundle  # noqa: E402


class TestAViaEnvelope(unittest.TestCase):
    """T-AVIA-ENV：扩展闸门 A_via=min{1, z̄/s_crit, m} 的包络语义。"""

    def test_default_m1_regression(self):
        """默认配置 m=1 ⇒ A_via 逐点等于资源型旧式 min(1, z_occ/s_crit)。"""
        cfg = Env0Config()
        m0 = build_env0(cfg)
        b = truth_bundle(m0, T=2)
        joints = propagate.truth_step_joints(m0, 2)
        # n_I=1（无 σ 手术）：Z 边缘 (n_Z,)=(2,)，高位占时=z[1]
        z_occ = float(np.mean([aux["Z"][1] for aux in joints]))
        resource_only = min(1.0, z_occ / cfg.s_crit)
        self.assertAlmostEqual(b.a_via, resource_only, places=12)

    def test_envelope_binding_and_zero(self):
        """κ_eff=0.4（比 0.8）⇒ A_via=0.8 精确；κ_eff=0 或 R_eff=0 ⇒ A_via=0。"""
        b = truth_bundle(build_env0(Env0Config(kappa_eff=0.4)), T=2)
        self.assertAlmostEqual(b.a_via, 0.8, places=12)
        self.assertEqual(truth_bundle(build_env0(Env0Config(kappa_eff=0.0)), T=2).a_via, 0.0)
        self.assertEqual(truth_bundle(build_env0(Env0Config(r_eff=0.0)), T=2).a_via, 0.0)
        # 共模归零：闸门零 ⇒ 复合零（T5-via 扩展析取项）
        self.assertEqual(truth_bundle(build_env0(Env0Config(kappa_eff=0.0)), T=2).a_obj, 0.0)

    def test_clip_upper_and_min_structure(self):
        """clip 上界：κ_eff=2.0（比 4）⇒ m=1（不超 1）；min 结构：R 单因子绑定生效。"""
        b0 = truth_bundle(build_env0(Env0Config()), T=2)
        b_hi = truth_bundle(build_env0(Env0Config(kappa_eff=2.0)), T=2)
        self.assertAlmostEqual(b_hi.a_via, b0.a_via, places=12)
        b_r = truth_bundle(build_env0(Env0Config(r_eff=0.25)), T=2)  # R 比 0.5 绑定
        self.assertAlmostEqual(b_r.a_via, 0.5, places=12)

    def test_req_positive_validation(self):
        with self.assertRaises(ValueError):
            build_env0(Env0Config(kappa_req=0.0))


class TestObsNO(unittest.TestCase):
    """T-OBS-N4：观察分辨率 n_O 泛化（默认逐点还原 v1）。"""

    def test_default_obs_belief_legacy_exact(self):
        cfg = Env0Config()
        m0 = build_env0(cfg)
        obs, bel = m0.kernels.obs, m0.kernels.belief
        L, U = cfg.L, cfg.U
        for e in range(L * U):
            bucket = 0 if (e // U) < (L + 1) // 2 else 1
            for a in range(m0.alphabet.n_A):
                self.assertAlmostEqual(obs[e, a, bucket], 1.0 - cfg.obs_noise, places=15)
                self.assertAlmostEqual(obs[e, a, 1 - bucket], cfg.obs_noise, places=15)
        for b in range(al_nB := m0.alphabet.n_B):
            for o in range(m0.alphabet.n_O):
                for b2 in range(al_nB):
                    expect = (0.85 if b2 == o else 0.0) + (0.15 if b2 == b else 0.0)
                    self.assertAlmostEqual(bel[b, o, b2], expect, places=15)

    def test_n4_build_valid_and_informative(self):
        cfg = Env0Config(n_O=4, obs_noise=0.05)
        m = build_env0(cfg)
        m.validate()  # 张量归一/字母表闭合
        self.assertEqual(m.alphabet.n_O, 4)
        # I(O;E)>0（AX2 平台性质）：obs 逐行与 a 无关 ⇒ 直接由先验计算
        p_e = m.kernels.init_E
        p_oe = m.kernels.obs[:, 0, :]                      # (n_E, n_O)
        p_o = p_e @ p_oe
        h_o = -float(sum(p * math.log(p) for p in p_o if p > 0))
        h_oe = float(sum(p_e[e] * (-sum(p * math.log(p) for p in p_oe[e] if p > 0))
                         for e in range(m.alphabet.n_E)))
        self.assertGreater(h_o - h_oe, 0.0)


class TestDel1F(unittest.TestCase):
    """T-DEL1-F：f>0／ρ≠1 非退化夹逼（DEL-1⑤⑥ 的单元级锚）。"""

    @classmethod
    def setUpClass(cls):
        cls.m0 = build_env0(Env0Config())
        cls.T = 2
        cls.f_self = di.truth_F_int(cls.m0, cls.T)
        cls.c_self = cls.f_self / cls.T
        cls.b0 = truth_bundle(cls.m0, T=cls.T)

    def test_f_pos_arm(self):
        m = 0.5
        q_cal = _calibrate_script(self.c_self, self.m0.alphabet.n_A, self.m0.alphabet.n_S)
        md = interventions.apply_beta_pi(
            self.m0, interventions.BetaPiSpec.switch([q_cal], flag_dist=(1.0 - m, m)))
        f_int_t = di.truth_F_int(md, self.T)
        f_ext_t = di.truth_F_ext(md, self.T)
        f_direct = f_ext_t - m * self.c_self * self.T
        # (a) 旗标选择熵进入律级路径：直接流严格为正
        self.assertGreater(f_direct, 1e-6)
        # 旗标逐步 MI ≤ H(flag) ≤ ln2（φ 上界的数学依据）
        self.assertLessEqual(f_direct, self.T * math.log(2.0) + 1e-9)
        a_org_t = f_int_t / (f_int_t + f_ext_t)
        # (b) 严格低于 H1' 线性律（直接流侵蚀超出内容记账）
        self.assertLess(a_org_t, (1.0 - m) * self.b0.a_org - 1e-9)
        # (c) φ-松弛双侧夹逼（审计方信息集 ρ∈[0.9,1.1]、φ≤T·ln2/F_self）含实测
        phi_max = self.T * math.log(2.0) / self.f_self
        lo = (1.0 - m) / (1.0 - m + 1.1 * m + phi_max)
        hi = (1.0 - m) / (1.0 - m + 0.9 * m)
        self.assertLessEqual(lo - 1e-9, a_org_t)
        self.assertLessEqual(a_org_t, hi + 1e-9)

    def test_rho_neq1_arm(self):
        m = 0.5
        q15 = _calibrate_script(1.5 * self.c_self, self.m0.alphabet.n_A,
                                self.m0.alphabet.n_S)
        md = interventions.apply_beta_pi(
            self.m0, interventions.BetaPiSpec.switch([q15], flag_dist=(1.0 - m, m)))
        f_int_t = di.truth_F_int(md, self.T)
        f_ext_t = di.truth_F_ext(md, self.T)
        a_org_t = f_int_t / (f_int_t + f_ext_t)
        phi_max = self.T * math.log(2.0) / self.f_self
        lo = (1.0 - m) / (1.0 - m + 1.65 * m + phi_max)
        hi = (1.0 - m) / (1.0 - m + 1.35 * m)
        self.assertLessEqual(lo - 1e-9, a_org_t)
        self.assertLessEqual(a_org_t, hi + 1e-9)
        # 线性律同域失效（夹逼界必要性）
        self.assertGreater(abs(a_org_t - (1.0 - m) * self.b0.a_org), 0.05)


class TestXErosionExec1(unittest.TestCase):
    """X-EROSION／X-EXEC1：新场景冒烟（小网格）。"""

    def test_erosion_small_grid(self):
        res = scenario_erosion(eps=(0.0, 0.6, 1.0))
        for name, v in res.verdicts.items():
            self.assertEqual(v.value, "CONFIRMED", f"erosion {name}: {v}")

    def test_exec1(self):
        res = scenario_exec1()
        for name, v in res.verdicts.items():
            self.assertEqual(v.value, "CONFIRMED", f"exec1 {name}: {v}")
        self.assertLessEqual(res.metrics["arms"]["delta_nm"]["a_exec"], 1e-9)
        self.assertGreaterEqual(res.metrics["arms"]["rich"]["a_exec"],
                                max(0.15, 5.0 * res.metrics["a_exec_v1"]))


class TestXP3Analysis(unittest.TestCase):
    """X-P3-ANALYSIS：analysis_p3 在微型矩阵产出上的链路核验（schema＋数值域）。"""

    def test_analysis_runs_on_tiny_matrix(self):
        from autonomy_sim.matrix import run_matrix
        import analysis_p3
        with tempfile.TemporaryDirectory() as td:
            for mid, codes in (("quick_main", (1, 2, 4, 5)), ("erosion", (15,)),
                               ("exec1", (16,))):
                run_matrix(scenarios=codes, defenses=((0, 0, 0),), sigmas=(1.0,), reps=1,
                           out_dir=os.path.join(td, mid), matrix_id=mid)
            result = {"X1_external_validity": analysis_p3.x1_external(td),
                      "X2_channel_ablation": analysis_p3.x2_ablation(td),
                      "X3_alternative_aggregations": analysis_p3.x3_aggregations(td),
                      "X4_faith_rows": analysis_p3.x4_faith(td)}
            # schema：四节齐＋verdict 块在
            for sec in result.values():
                self.assertIn("verdicts", sec)
            # 数值域：τ∈[−1,1]（或 nan=恒定列）、确认率∈[0,1]、计数非负
            for v in result["X1_external_validity"]["regimes"].values():
                if "mean_tau" in v and v["n_series"] > 0 and not math.isnan(v["mean_tau"]):
                    self.assertTrue(-1.0 - 1e-9 <= v["mean_tau"] <= 1.0 + 1e-9)
            self.assertGreaterEqual(result["X3_alternative_aggregations"]["n_bundles"], 1)
            self.assertGreaterEqual(
                result["X3_alternative_aggregations"]["t5_counterexamples_arith"], 0)
            for name, v in result["X4_faith_rows"].items():
                if isinstance(v, dict) and "rate" in v and not math.isnan(v["rate"]):
                    self.assertTrue(0.0 <= v["rate"] <= 1.0, f"{name}: {v['rate']}")
            # X4 实质锚：微型矩阵上 ATK-1/2/4/5＋EXEC-1 单调性应全确认（真值模式精确）
            self.assertTrue(result["X4_faith_rows"]["verdicts"]["faith_all_rows"],
                            json.dumps(result["X4_faith_rows"], ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
