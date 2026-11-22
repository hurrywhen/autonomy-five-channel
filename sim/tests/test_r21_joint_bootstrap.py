"""R21 joint trajectory bootstrap: sufficient-statistics correctness (reproduces
the plug-in channels exactly), determinism, structure/bounds, and the fidelity
formula anchor.  Software checks only; coverage/bias magnitudes are not pass
conditions."""
import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim.empowerment import channel_capacity  # noqa: E402
from autonomy_sim.native_benchmark import NativeConfig, _share_report  # noqa: E402
from autonomy_sim.native_joint_audit import (_fidelity_from_events,  # noqa: E402
                                             generate_execution_logs,
                                             generate_operating_logs)
from autonomy_sim.r19_joint_audit import estimate_from_logs_r19  # noqa: E402
from autonomy_sim.r21_joint_bootstrap import (  # noqa: E402
    JOINT_BOOTSTRAP_CONSTRUCTION, _execution_sufficient_stats, _fidelity_from_joint,
    _operating_sufficient_stats, joint_composite_bootstrap,
)


def _logs(n=512, seed=20261122):
    cfg = NativeConfig(surgery=0)
    rng = np.random.default_rng(seed)
    op = generate_operating_logs(cfg, n_trajectories=n, rng=rng)
    ex = generate_execution_logs(cfg, n_samples=n, rng=rng)
    return cfg, op, ex


class SufficientStatisticsCorrectness(unittest.TestCase):
    def test_operating_stats_reproduce_plugin_channels(self):
        cfg, op, ex = _logs()
        est = estimate_from_logs_r19(cfg, op, ex, n_bootstrap=10,
                                     rng=np.random.default_rng(1))
        st = _operating_sufficient_stats(op, cfg.horizon)
        idx = np.arange(len(op))
        reg = np.bincount(st["reg_idx"][idx], minlength=st["size"]).reshape(st["shape"])
        rep = _share_report(reg / reg.sum(), cfg.horizon)
        self.assertAlmostEqual(rep["normative_share_RNI"],
                               est["source"]["registered_partition"]["normative_share_RNI"],
                               places=12)
        self.assertAlmostEqual(float(st["epi_hits"][idx].mean()),
                               est["epistemic"]["sample_mean"], places=12)
        fid = _fidelity_from_joint(st["fid_contrib"][idx].sum(axis=0))
        pairs = [(e["theta"], e["self_report"]) for l in op for e in l["events"]
                 if e["type"] == "NORMATIVE_UPDATE"]
        self.assertAlmostEqual(fid, _fidelity_from_events(pairs), places=12)
        self.assertAlmostEqual(fid, est["reflection"]["fidelity"], places=12)
        cons = st["endorsements"][idx].sum() / st["updates"][idx].sum()
        lam = 1 - st["ctx_mismatch"][idx].sum() / st["ctx_count"][idx].sum()
        self.assertAlmostEqual(cons, est["reflection"]["endorsement_consistency"], places=12)
        self.assertAlmostEqual(lam, est["reflection"]["Lambda"], places=12)
        self.assertAlmostEqual(float(st["min_z"][idx].min()),
                               est["viability_state"], places=12)

    def test_execution_stats_reproduce_plugin_a_exec(self):
        cfg, op, ex = _logs()
        est = estimate_from_logs_r19(cfg, op, ex, n_bootstrap=10,
                                     rng=np.random.default_rng(1))
        seq, term = _execution_sufficient_stats(ex)
        self.assertEqual(seq, [0, 1, 2, 3])
        K = np.zeros((4, 2))
        for r, s in enumerate(seq):
            p1 = term[s].mean()
            K[r] = [1 - p1, p1]
        cap, _ = channel_capacity(K)
        a_exec = min(1.0, cap / (2 * math.log(2)))
        self.assertAlmostEqual(a_exec, est["execution_open_loop"]["sample_a_exec"], places=9)
        # Stratified design: each sequence has n samples.
        for s in seq:
            self.assertEqual(len(term[s]), len(op))

    def test_fidelity_helper_matches_event_function(self):
        rng = np.random.default_rng(3)
        for _ in range(5):
            pairs = [(int(rng.integers(0, 2)), int(rng.integers(0, 2)))
                     for _ in range(50)]
            joint = np.zeros((2, 2))
            for t, m in pairs:
                joint[t, m] += 1
            self.assertAlmostEqual(_fidelity_from_joint(joint),
                                   _fidelity_from_events(pairs), places=12)


class JointBootstrapStructure(unittest.TestCase):
    def test_intervals_valid_and_deterministic(self):
        cfg, op, ex = _logs()
        jb1 = joint_composite_bootstrap(cfg, op, ex, n_bootstrap=40,
                                        rng=np.random.default_rng([20261122, 512, 21]))
        jb2 = joint_composite_bootstrap(cfg, op, ex, n_bootstrap=40,
                                        rng=np.random.default_rng([20261122, 512, 21]))
        self.assertEqual(jb1, jb2)  # deterministic given seed
        self.assertEqual(jb1["construction"], JOINT_BOOTSTRAP_CONSTRUCTION)
        self.assertTrue(jb1["scope"].startswith("SUPPLEMENTARY_JOINT_DIAGNOSTIC"))
        for partition, conventions in jb1["composite_intervals"].items():
            for convention, iv in conventions.items():
                self.assertIsNotNone(iv)
                lo, hi = iv["percentile_95"]
                self.assertTrue(0.0 <= lo <= hi <= 1.0)
                self.assertTrue(math.isfinite(iv["bootstrap_se"]))
        for key, iv in jb1["channel_intervals"].items():
            if iv is not None:
                lo, hi = iv["percentile_95"]
                self.assertTrue(0.0 <= lo <= hi <= 1.0)

    def test_constant_channels_have_degenerate_intervals(self):
        # viability (resource ratios) and Lambda (surgery=0 => y=u) are deterministic
        # in this fixture, so their bootstrap intervals collapse to a point.
        cfg, op, ex = _logs()
        jb = joint_composite_bootstrap(cfg, op, ex, n_bootstrap=40,
                                       rng=np.random.default_rng([20261122, 512, 21]))
        vio = jb["channel_intervals"]["viability_state"]["percentile_95"]
        self.assertEqual(vio[0], vio[1])
        lam = jb["channel_intervals"]["Lambda"]["percentile_95"]
        self.assertEqual(lam[0], lam[1])
        self.assertEqual(lam[0], 1.0)

    def test_variable_channels_have_nonzero_width(self):
        cfg, op, ex = _logs()
        jb = joint_composite_bootstrap(cfg, op, ex, n_bootstrap=60,
                                       rng=np.random.default_rng([20261122, 512, 21]))
        for key in ("a_exec", "a_epi", "a_ref"):
            lo, hi = jb["channel_intervals"][key]["percentile_95"]
            self.assertGreater(hi - lo, 0.0)

    def test_invalid_inputs_fail_closed(self):
        cfg, op, ex = _logs()
        with self.assertRaises(ValueError):
            joint_composite_bootstrap(cfg, op, ex, n_bootstrap=1,
                                      rng=np.random.default_rng(1))
        with self.assertRaises(ValueError):
            joint_composite_bootstrap(cfg, op[:1], ex, n_bootstrap=10,
                                      rng=np.random.default_rng(1))


if __name__ == "__main__":
    unittest.main()