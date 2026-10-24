"""L2 场景冒烟测试（SPEC_tests §3 注册表 X-ATK1…X-ATK6、X-DEL1、X-C0、X-LH1、X-RES1、
X-FORCE1、X-BB1、X-C0CORR）：场景可运行、判据函数产出合法 verdict、方向正确。

防御方向断言（P9.5）：同攻击强度下防御臂损伤 < 无防御臂。
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim import scenarios  # noqa: E402
from autonomy_sim.scenarios import SCENARIOS, Verdict  # noqa: E402


class TestScenariosSmoke(unittest.TestCase):
    """每场景一测：可运行、verdict 合法且参考实现下方向正确（判据见 SPEC_experiments §1）。"""

    def _check_legal(self, res):
        self.assertTrue(res.verdicts)
        for v in res.verdicts.values():
            self.assertIn(v, (Verdict.CONFIRMED, Verdict.REFUTED, Verdict.INCONCLUSIVE))
        self.assertIn(res.overall, (Verdict.CONFIRMED, Verdict.REFUTED, Verdict.INCONCLUSIVE))

    def test_XATK1_reward_hijack(self):
        res = SCENARIOS[1]()
        self._check_legal(res)
        self.assertEqual(res.overall, Verdict.CONFIRMED)
        gs = [r["a_goal"] for r in res.metrics["rows"]]
        self.assertTrue(all(x >= y - 1e-9 for x, y in zip(gs, gs[1:])))
        self.assertEqual(gs[-1], 0.0)
        # 防御方向：同 η=0.5 下 M2+M4 臂的 a_goal 高于无防御臂
        undef = SCENARIOS[1](etas=(0.5,))
        deffed = SCENARIOS[1](etas=(0.5,), defense=(0, 1, 1))
        self.assertGreater(deffed.metrics["rows"][0]["a_goal"],
                           undef.metrics["rows"][0]["a_goal"])

    def test_XATK2_infococoon(self):
        res = SCENARIOS[2]()
        self._check_legal(res)
        self.assertEqual(res.overall, Verdict.CONFIRMED)
        rows = res.metrics["rows"]
        self.assertLess(rows[-1]["a_epi"], rows[0]["a_epi"])  # A_epi 降
        self.assertTrue(all(abs(r["a_org"] - 1.0) < 1e-9 for r in rows))  # A_org 盲
        self.assertGreaterEqual(res.metrics["t4_damage"][0], res.metrics["t4_damage"][1])

    def test_XATK3_dependency_lockin(self):
        res = SCENARIOS[3]()
        self._check_legal(res)
        self.assertEqual(res.overall, Verdict.CONFIRMED)
        self.assertGreater(res.metrics["e_env"], res.metrics["e_pi"])  # 无助签名
        self.assertGreater(res.metrics["delta_down"], 0.0)
        self.assertGreater(res.metrics["s_c"], 0.0)  # 回环不闭合

    def test_XATK4_prompt_injection(self):
        res = SCENARIOS[4]()
        self._check_legal(res)
        # 【登记 REFUTED 已结案（2026-10-16）：A_epi 精度化首跑 C1 曾翻转——α 臂探针
        # 内容错位在正交坐标（i≡e mod 2=u），粗粒信念核误投倾斜 ⇒ 位置桶精度 −0.0158。
        # 根因=场景操作化缺陷（说服臂应投递被测坐标的诚实信息），非理论反例、非判据编辑。
        # 修复：探针内容对齐 i=κ(e)（fidelity 0.9），判据阈值未动；C1 恢复 CONFIRMED。
        # 全过程按 SPEC_experiments §8 / SPEC_tests 7f 登记。】
        self.assertEqual(res.overall, Verdict.CONFIRMED)
        self.assertEqual(res.verdicts["C1_persuasion_four_tracks"], Verdict.CONFIRMED)
        self.assertEqual(res.verdicts["C2_hijack_a_org_down"], Verdict.CONFIRMED)
        self.assertEqual(res.verdicts["C3_multichannel_necessity"], Verdict.CONFIRMED)
        a_orgs = [r["a_org"] for r in res.metrics["rows"]]
        self.assertLess(a_orgs[-1], a_orgs[0])  # 成功注入 ⇒ A_org 降
        self.assertAlmostEqual(res.metrics["f_ext_alpha"], 0.0, places=12)  # 说服臂 F_ext=0
        self.assertAlmostEqual(res.metrics["f_ext_gamma"], 0.0, places=12)  # γ 臂单轨盲
        # 修复后核心锚：坐标对齐的诚实信息不降低被测坐标精度（兼容性判据第三轨）
        self.assertGreaterEqual(res.metrics["a_epi_alpha"], res.metrics["a_epi_base"] - 1e-9)

    def test_XATK5_urgency(self):
        res = SCENARIOS[5]()
        self._check_legal(res)
        self.assertEqual(res.overall, Verdict.CONFIRMED)
        refs = [r["a_ref"] for r in res.metrics["rows"]]
        self.assertTrue(all(x >= y - 1e-12 for x, y in zip(refs, refs[1:])))
        gates = [r["d_star_gate"] for r in res.metrics["rows"]]
        self.assertTrue(all(x <= y + 1e-12 for x, y in zip(gates, gates[1:])))
        self.assertLess(refs[-1], 0.01)  # τ→0 ⇒ A_ref→0

    def test_XATK6_subthreshold_drift(self):
        res = SCENARIOS[6]()
        self._check_legal(res)
        self.assertEqual(res.overall, Verdict.CONFIRMED)
        self.assertGreater(res.metrics["damages_detect"][1],
                           res.metrics["damages_detect"][0])  # 检测损伤发散

    def test_XDEL1_delegation_grid(self):
        res = SCENARIOS[7]()
        self._check_legal(res)
        self.assertEqual(res.overall, Verdict.CONFIRMED)
        for r in res.metrics["rows"]:
            self.assertAlmostEqual(r["a_org"], 1.0 - r["m"], places=1)  # 线性律（5% 容差带内）

    def test_XC0_injection_vs_instruction(self):
        res = SCENARIOS[8]()
        self._check_legal(res)
        self.assertEqual(res.overall, Verdict.CONFIRMED)
        self.assertLess(res.metrics["tv_sampled"], 0.05)  # 行为 TV 检验通过
        lam1, lam2 = res.metrics["lam"]
        self.assertEqual(lam1, 1.0)
        self.assertLess(lam2, lam1)  # A 分量可区分

    def test_XLH1_learned_helplessness(self):
        res = SCENARIOS[9]()
        self._check_legal(res)
        self.assertEqual(res.overall, Verdict.CONFIRMED)
        # 无助签名三段：诱导期不可控（信道容量=0）；诱导后 ℰ^env 完好；ℰ^Π 坍缩为 0
        self.assertEqual(res.metrics["e_env_induced"], 0.0)
        self.assertGreater(res.metrics["e_env_post"], 1e-3)
        self.assertEqual(res.metrics["e_pi_collapsed"], 0.0)
        self.assertGreater(res.metrics["recovery_lag"], 0.0)

    def test_XRES1_resource_cutoff(self):
        res = SCENARIOS[10]()
        self._check_legal(res)
        self.assertEqual(res.overall, Verdict.CONFIRMED)
        a0 = res.metrics["baseline"]["a_obj"]
        arms = res.metrics["arms"]
        self.assertLess(arms["dead"]["a_obj"], arms["low"]["a_obj"])
        self.assertLess(arms["low"]["a_obj"], a0)
        self.assertGreaterEqual(arms["hi"]["a_obj"], a0 - 1e-9)  # σ⁺ 恢复
        self.assertEqual(arms["dead"]["a_org"], 1.0)  # 独立于其余通道

    def test_XFORCE1_coercion_paradox(self):
        res = SCENARIOS[11]()
        self._check_legal(res)
        self.assertEqual(res.overall, Verdict.CONFIRMED)
        a0, a_g, a_d, a_s = res.metrics["a_obj"]
        self.assertLess(a_g, a0)   # β_G 强制 ⇒ 降
        self.assertLess(a_d, a0)   # δ 强制 ⇒ 降
        self.assertGreaterEqual(a_s, a0 - 1e-9)  # σ 臂即期不降
        ds0, ds1 = res.metrics["d_star"]
        am0, am1 = res.metrics["a_min"]
        self.assertGreater(ds1, ds0)
        self.assertGreater(am1, am0)

    def test_XBB1_blackbox_degradation(self):
        res = SCENARIOS[12]()
        self._check_legal(res)
        self.assertEqual(res.overall, Verdict.CONFIRMED)
        self.assertEqual(res.metrics["hits"], 3)  # 区间界全命中
        i_obs, i_cond = res.metrics["a_exec_obs_cond"]
        self.assertGreaterEqual(i_obs, i_cond - 1e-9)  # A_exec^obs≥A_exec（被动观察协议）
        lam_e, lam_i = res.metrics["lam"]
        self.assertGreater(lam_e, lam_i)  # 黑盒不可区分而 Λ 不同（命题 10.4）

    def test_XC0CORR_projection_consistency(self):
        res = SCENARIOS[13]()
        self._check_legal(res)
        self.assertEqual(res.overall, Verdict.CONFIRMED)
        for dim, tau in res.metrics["taus"].items():
            self.assertGreater(tau, 0.95)  # 序一致性（合法统计量）
        self.assertLessEqual(res.metrics["tau_mismatch"],
                             min(res.metrics["taus"].values()) + 1e-12)  # 投影方向


if __name__ == "__main__":
    unittest.main()
