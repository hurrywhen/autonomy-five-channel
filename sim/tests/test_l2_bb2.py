"""T-BB2：自适应对手臂（scenario_bb2；SPEC_experiments §8 补充实验）。

回归锚（unittest 风格；pytest 亦可收集 TestCase）：
- T-BB2-EQUIV：flag_by_state 各行相同 ⇒ 广义 Jensen 路径退化为 iid 旗标路径（一致性）。
- T-BB2-INDEP：逐状态 F_ext 与独立复实现（propagate 边缘 × 重建 π_i 的逐状态条件 MI）一致。
- T-BB2-MISS：自适应臂朴素外生插值高估 F_ext（bias>0）且区间失含（§10.2 适用域边界）。
- T-BB2-CTRL：外生对照臂区间含真值（BB-1 口径在收获脚本下复验）。
"""
import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from autonomy_sim import di, interventions, propagate  # noqa: E402
from autonomy_sim.blackbox import a_org_interval, probe_flow_obs  # noqa: E402
from autonomy_sim.env0 import Env0Config, build_env0  # noqa: E402
from autonomy_sim.scenarios import scenario_bb2  # noqa: E402


def _H(row):
    row = np.asarray(row, float)
    nz = row[row > 0]
    return float(-np.sum(nz * np.log(nz)))


def _harvest_script(al, bias=0.8):
    script = np.full((al.n_S, al.n_A), (1.0 - bias) / (al.n_A - 1))
    script[:, 2] = bias
    return script


def _adaptive_flag(al, g0, p):
    fs = np.zeros((al.n_S, 2))
    for s in range(al.n_S):
        fs[s, 1] = p if al.split_S(s)[0] == g0 else 0.0
        fs[s, 0] = 1.0 - fs[s, 1]
    return fs


class TestBB2(unittest.TestCase):
    def test_equiv_constant_rows_match_iid(self):
        """T-BB2-EQUIV：逐状态旗标退化为常数行 ⇒ 与 iid 旗标路径数值一致。"""
        m0 = build_env0(Env0Config())
        al = m0.alphabet
        script = _harvest_script(al)
        p = 0.2
        mi = interventions.apply_beta_pi(
            m0, interventions.BetaPiSpec.switch([script], flag_dist=(1.0 - p, p)))
        fs_const = np.tile([1.0 - p, p], (al.n_S, 1))
        ms = interventions.apply_beta_pi(
            m0, interventions.BetaPiSpec.switch([script], flag_dist=(1.0 - p, p),
                                                flag_by_state=fs_const))
        for T in (1, 2, 3):
            self.assertAlmostEqual(di.truth_F_ext(mi, T), di.truth_F_ext(ms, T), places=12)
            self.assertAlmostEqual(di.truth_F_int(mi, T), di.truth_F_int(ms, T), places=12)

    def test_state_flag_fext_independent_recompute(self):
        """T-BB2-INDEP：广义 F_ext 与独立复实现一致（不同代码路径重算同一数学量）。"""
        m0 = build_env0(Env0Config())
        al = m0.alphabet
        script = _harvest_script(al)
        fs = _adaptive_flag(al, Env0Config().theta_star, 0.5)
        ma = interventions.apply_beta_pi(
            m0, interventions.BetaPiSpec.switch([script], flag_dist=(1.0, 0.0),
                                                flag_by_state=fs))
        T = 2
        pol = ma.kernels.policy.reshape(al.n_S, al.n_A, 2)
        h_bar = np.array([_H(row) for row in pol.sum(axis=2)])
        h_js = h_bar.copy()
        for i in (0, 1):
            w = fs[:, i]
            active = w > 0
            h_i = np.zeros(al.n_S)
            h_i[active] = [_H(row) for row in pol[active, :, i] / w[active, None]]
            h_js -= w * h_i
        indep = sum(float(aux["S"] @ h_js) for aux in propagate.truth_step_joints(ma, T))
        self.assertAlmostEqual(di.truth_F_ext(ma, T), indep, places=12)
        self.assertGreater(di.truth_F_ext(ma, T), 0)

    def test_adaptive_misses_and_bias(self):
        """T-BB2-MISS：自适应臂（朴素外生插值）高估 F_ext 且区间失含；方向固定为正。"""
        res = scenario_bb2()
        self.assertEqual(res.overall.value, "CONFIRMED")
        ad = res.metrics["adaptive"]
        self.assertTrue(all(d["bias"] > 0 for d in ad), "朴素插值应系统性高估外部流")
        self.assertTrue(all(d["miss"] for d in ad), "三个自适应强度档的区间应全部失含")

    def test_exogenous_control_holds(self):
        """T-BB2-CTRL：外生对照臂（iid 旗标 × state-independent 脚本）区间含真值。"""
        m0 = build_env0(Env0Config())
        al = m0.alphabet
        f_base = di.truth_F_int(m0, T=2)
        script = _harvest_script(al)
        for p in (0.1, 0.2):
            mp = interventions.apply_beta_pi(
                m0, interventions.BetaPiSpec.switch([script], flag_dist=(1.0 - p, p)))
            f_obs = probe_flow_obs(mp, T=2)
            a_true = di.truth_A_org(mp, T=2)
            lo, hi = a_org_interval(f_base, 0.3, f_obs)
            self.assertLessEqual(lo, a_true)
            self.assertLessEqual(a_true, hi)


if __name__ == "__main__":
    unittest.main(verbosity=2)
