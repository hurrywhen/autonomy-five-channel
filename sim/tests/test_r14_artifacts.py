"""R14 generated-evidence, replay, and historical-write-protection checks."""
import hashlib
import json
from pathlib import Path
import unittest

from autonomy_sim.c0_witness import evaluate_same_environment_c0
from run_x5c_r14_stratified import compute


ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class R14Artifacts(unittest.TestCase):
    def test_T_R14_X5C_stratified_protocol_and_sensitivity_consequence(self):
        rows, cross, estimates, differences, d_noise, status, witness, criteria, verdict = compute()
        self.assertEqual(len(rows), 24)  # 2 noises * 4 arms * 3 times
        self.assertTrue(all(r["n_contexts"] == 20000 for r in rows))
        self.assertEqual({r["t"] for r in rows}, {1, 2, 3})
        self.assertEqual(len(cross), 2)
        self.assertTrue(all(criteria.values()))
        self.assertEqual(verdict, "CONFIRMED")
        self.assertGreater(d_noise, 0.01)
        self.assertEqual(status, "MODEL_SENSITIVE")
        self.assertEqual(witness["identity_p_y1"], witness["xor_p_y1"])
        self.assertNotEqual(witness["identity"].lam, witness["xor"].lam)
        manifest = json.loads((RUNS / "20261116_r14/x5c_stratified/manifest.json").read_text())
        for key in ("estimand_version", "audit_observation", "T", "n_contexts_per_t_arm_noise",
                    "git_dirty", "source_sha256", "preregistration_sha256", "surgery_map"):
            self.assertIn(key, manifest)
        self.assertEqual(manifest["n_contexts_total"], 480000)
        self.assertTrue(manifest["git_dirty"])
        self.assertFalse(manifest["old_env0_upgraded"])

    def test_T_R14_C0_same_environment_witness_and_failed_attempt_retained(self):
        result = evaluate_same_environment_c0()
        self.assertTrue(result["behavior_equal_full_trajectory_EOA"])
        self.assertEqual(result["a_epi_z1"], 1.0)
        self.assertEqual(result["a_epi_z2"], 0.5)
        self.assertGreater(result["a_org_z1"], 0.0)
        self.assertGreater(result["a_goal"], 0.0)
        self.assertGreater(result["a_exec_z1"], 0.0)
        self.assertGreater(result["a_exec_z2"], 0.0)
        self.assertTrue(0.0 < result["composite_z2"] < result["composite_z1"])
        self.assertEqual(result["overall_verdict"], "CONFIRMED")
        self.assertEqual(result["xor_identity_lambda"], 1.0)
        self.assertEqual(result["xor_implanted_lambda"], 0.0)
        self.assertTrue((RUNS / "20261116_r14/c0cf_failed_initial/FAILURE.md").exists())

    def test_T_R14_historical_evidence_not_rewritten(self):
        expected = {
            "manifest.json": "6c17724800b2befa11e61af25988a18accec73a770b34f53ba29e6a4d905e481",
            "results.csv": "5371704d9b662a00ebe2c15e5435b9daebf039fa398f1a0310a9b6e5a571e6fd",
            "verdict_table.csv": "137ae820ee48cb16171acd5cd2326ce3c9d1111a74fee0c997c07e319f24faf2",
        }
        base = RUNS / "20261102_r11/del1"
        for name, digest in expected.items():
            self.assertEqual(sha(base / name), digest)
        old_x5 = json.loads((ROOT / "analysis_sensitivity_arms.json").read_text(encoding="utf-8"))
        self.assertEqual(old_x5["meta"]["x_c_status"], "registered, not run (deferred per reviewer R8-1)")
        new_analysis = json.loads((RUNS / "20261116_r14/x5c_stratified/analysis.json").read_text())
        self.assertFalse(new_analysis["historical_archives_modified"])
        self.assertFalse(new_analysis["old_env0_upgraded"])
        self.assertFalse(new_analysis["external_construct_validation"])


if __name__ == "__main__":
    unittest.main()
