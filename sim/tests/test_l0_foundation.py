"""L0 基础测试（sim/SPEC_tests.md §1 注册表：T-SEED/T-LOG/T-TENSOR/T-RNG/T-MODE）。

TDD 第 1 步：本文件先于实现建立（红→绿）。
依据：sim/SPEC_platform.md P1.1/P1.2（内核与因子化）、P1.4（双模式）、§6（种子协议）、§8（日志 schema）。
"""
import hashlib
import json
import os
import re
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np

from autonomy_sim import fixtures, logschema, rng as rngmod
from autonomy_sim.propagate import truth_marginals
from autonomy_sim.simulate import simulate_trajectories, sample_marginal_counts


class TestTSEED(unittest.TestCase):
    """T-SEED（SPEC_platform P6.2/P6.3）：种子派生公式与逐比特复现。"""

    def test_TSEED_derivation_formula(self):
        # P6.2: seed = 30000 + scenario*1000 + config*97 + rep
        self.assertEqual(rngmod.derive_seed(0, 0, 0), 30000)
        self.assertEqual(rngmod.derive_seed(6, 5, 29), 30000 + 6000 + 485 + 29)
        self.assertEqual(rngmod.derive_seed(13, 7, 29), 30000 + 13000 + 679 + 29)

    def test_TSEED_derivation_injective_over_registry(self):
        seen = {}
        for scenario in range(0, 14):
            for config in range(0, 8):
                for rep in range(0, 30):
                    s = rngmod.derive_seed(scenario, config, rep)
                    self.assertNotIn(s, seen, f"seed 冲突: {s}")
                    seen[s] = (scenario, config, rep)

    def test_TSEED_rep_bounds(self):
        with self.assertRaises(ValueError):
            rngmod.derive_seed(1, 0, 30)
        with self.assertRaises(ValueError):
            rngmod.derive_seed(1, 0, -1)

    def test_TSEED_trajectory_bitwise_determinism(self):
        model = fixtures.toy_model()
        seed = rngmod.derive_seed(0, 0, 0)
        r1 = simulate_trajectories(model, seed=seed, T=50, n_traj=2)
        r2 = simulate_trajectories(model, seed=seed, T=50, n_traj=2)
        s1 = json.dumps(r1, sort_keys=True)
        s2 = json.dumps(r2, sort_keys=True)
        self.assertEqual(s1, s2)

    def test_TSEED_different_seed_differs(self):
        model = fixtures.toy_model()
        r1 = simulate_trajectories(model, seed=rngmod.derive_seed(0, 0, 0), T=50, n_traj=2)
        r3 = simulate_trajectories(model, seed=rngmod.derive_seed(0, 0, 1), T=50, n_traj=2)
        self.assertNotEqual(json.dumps(r1, sort_keys=True), json.dumps(r3, sort_keys=True))


class TestTLOG(unittest.TestCase):
    """T-LOG（SPEC_platform §8）：日志 schema 校验器。"""

    def setUp(self):
        self.model = fixtures.toy_model()
        self.al = self.model.alphabet
        self.meta = logschema.make_metadata(self.model, seed=30000, scenario_code=0, mode="sample")
        self.rec = {
            "t": 0, "E_t": 1, "O_t": 2,
            "S_t": {"G": 0, "B": 1, "M": 0, "R": 1},
            "A_t": 1, "Z_t": 0,
            "I_t": {"sigma": 0.0, "alpha": 0.0, "beta": 0.0, "gamma": 0.0, "delta": 0.0},
            "defense_events": [],
            "damage_D": {},
        }

    def test_TLOG_valid_log_accepted(self):
        errors = logschema.validate_log(self.meta, [self.rec], self.al)
        self.assertEqual(errors, [])

    def test_TLOG_missing_field_rejected(self):
        bad = {k: v for k, v in self.rec.items() if k != "A_t"}
        errors = logschema.validate_log(self.meta, [bad], self.al)
        self.assertTrue(any("A_t" in e for e in errors))

    def test_TLOG_alphabet_violation_rejected(self):
        bad = dict(self.rec, A_t=99)
        errors = logschema.validate_log(self.meta, [bad], self.al)
        self.assertTrue(any("A_t" in e for e in errors))

    def test_TLOG_unnormalized_distribution_rejected(self):
        bad = dict(self.rec, belief_dist=[0.5, 0.6, 0.0][: self.al.n_B])
        if self.al.n_B < 3:
            bad["belief_dist"] = [0.5, 0.6]
        errors = logschema.validate_log(self.meta, [bad], self.al)
        self.assertTrue(any("belief_dist" in e for e in errors))

    def test_TLOG_metadata_fields_required(self):
        for field in ("spec_version", "config_hash", "seed", "scenario_code", "mode"):
            bad = {k: v for k, v in self.meta.items() if k != field}
            errors = logschema.validate_log(bad, [self.rec], self.al)
            self.assertTrue(any(field in e for e in errors), f"缺 metadata 字段 {field} 未被拒绝")

    def test_TLOG_roundtrip_with_simulated_run(self):
        model = fixtures.toy_model()
        recs = simulate_trajectories(model, seed=30000, T=20, n_traj=1)[0]
        meta = logschema.make_metadata(model, seed=30000, scenario_code=0, mode="sample")
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "run.ndjson")
            logschema.write_run(path, meta, [recs])
            meta2, trajs = logschema.read_run(path)
        self.assertEqual(meta2["config_hash"], meta["config_hash"])
        errors = logschema.validate_log(meta2, trajs[0], model.alphabet)
        self.assertEqual(errors, [])


class TestTTENSOR(unittest.TestCase):
    """T-TENSOR（SPEC_platform P1.1/P1.2）：转移张量归一与字母表闭合。"""

    def test_TTENSOR_valid_model_passes(self):
        fixtures.toy_model().validate()

    def test_TTENSOR_unnormalized_kernel_rejected(self):
        model = fixtures.toy_model()
        model.kernels.obs[0, 0, 0] += 0.5
        with self.assertRaises(AssertionError):
            model.validate()

    def test_TTENSOR_bad_shape_rejected(self):
        model = fixtures.toy_model()
        model.kernels.policy = model.kernels.policy[:-1]
        with self.assertRaises(AssertionError):
            model.validate()


class TestTRNG(unittest.TestCase):
    """T-RNG（SPEC_platform P6.1）：代码库禁用 random 模块与 numpy 全局随机 API。"""

    FORBIDDEN = [
        re.compile(r"^\s*import\s+random\b", re.M),
        re.compile(r"^\s*from\s+random\b", re.M),
        re.compile(r"np\.random\.(random|rand|randn|randint|choice|seed|uniform|normal|shuffle)\b"),
    ]

    def test_TRNG_no_forbidden_random_usage(self):
        src = os.path.join(os.path.dirname(__file__), "..", "src")
        offenders = []
        for root, _dirs, files in os.walk(src):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, encoding="utf-8") as fh:
                        text = fh.read()
                    for pat in self.FORBIDDEN:
                        if pat.search(text):
                            offenders.append(f"{path}: {pat.pattern}")
        self.assertEqual(offenders, [])


class TestTMODE(unittest.TestCase):
    """T-MODE（SPEC_platform P1.4）：真值模式与采样模式边缘分布一致（采样容差内）。"""

    def test_TMODE_marginal_agreement(self):
        model = fixtures.toy_model()
        T = 30
        truth = truth_marginals(model, T)[-1]  # (n_E, n_O, n_A) at t=T-1
        n = 30000
        counts = sample_marginal_counts(model, seed=rngmod.derive_seed(0, 0, 7), T=T, n_traj=n)
        freq = counts[-1] / n
        max_dev = float(np.max(np.abs(truth - freq)))
        self.assertLess(max_dev, 0.02, f"真值-采样边缘偏差过大: {max_dev}")


if __name__ == "__main__":
    unittest.main()
