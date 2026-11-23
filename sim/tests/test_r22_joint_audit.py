"""R22 joint-audit guards: unchanged formal certificate/controls, matched A/B/C
structure, exact R21-C reproduction, immutable-input binding, and withdrawal of
single-cause under-coverage attribution.  Frozen values are labeled snapshots."""
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim.r21_guards import validate_r21_certificate  # noqa: E402
from autonomy_sim.r22_interval_contrast import (CONTRAST_POLICY, METHOD_A,  # noqa: E402
                                                METHOD_B, METHOD_C, METHODS)
from analysis_r22_joint_audit import compute, validate_result  # noqa: E402


class R22JointAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = compute(n_samples=1024, seed=7, n_bootstrap=10,
                             n_joint_bootstrap=20)

    def test_small_audit_valid_and_certificate_unchanged_schema(self):
        validate_result(self.result)
        cert = self.result["baseline_certificate"]
        self.assertEqual(validate_r21_certificate(cert), [])
        self.assertEqual(cert["channel_schema_version"], "R21_CHANNEL_SCHEMA_V1")
        self.assertEqual(cert["certificate_mode"], "INTERVAL")
        self.assertIsNone(cert["state_autonomy"])
        self.assertNotIn("matched_interval_contrast", cert)
        self.assertNotIn("matched_interval_contrast", cert["attribution_sensitivity"])

    def test_matched_methods_and_policy_present_not_causal(self):
        matched = self.result["matched_interval_contrast"]
        self.assertEqual(matched["policy"], CONTRAST_POLICY)
        self.assertFalse(self.result["scope"]["causal_undercoverage_attribution"])
        self.assertFalse(self.result["scope"]["formal_bias_decomposition"])
        for conventions in matched["intervals"].values():
            for entry in conventions.values():
                self.assertEqual(set(entry), set(METHODS))
                self.assertIn("share_basic_interval", entry[METHOD_A])
                self.assertIn("bootstrap_mean", entry[METHOD_B])
                self.assertIn("bootstrap_mean", entry[METHOD_C])

    def test_c_reproduces_retained_r21_joint_diagnostic(self):
        matched = self.result["matched_interval_contrast"]
        for partition, conventions in matched["intervals"].items():
            for convention, entry in conventions.items():
                old = self.result["joint_bootstrap"]["composite_intervals"][partition][convention]
                self.assertEqual(entry[METHOD_C]["bounds"], old["percentile_95"])
                self.assertEqual(entry[METHOD_C]["bootstrap_mean"], old["bootstrap_mean"])
                self.assertEqual(entry[METHOD_C]["bootstrap_se"], old["bootstrap_se"])

    def test_formal_envelope_semantics_remain_separate(self):
        reports = self.result["baseline_certificate"]["attribution_sensitivity"]["convention_reports"]
        for partition in reports.values():
            for rep in partition.values():
                if rep["convention_status"] == "DATA_ABOVE_LIMIT":
                    self.assertEqual(rep["composite_interval"]["kind"],
                                     "SHARE_CONDITIONAL_SAMPLING_BASIC_BOOTSTRAP")
                else:
                    self.assertEqual(rep["composite_interval"]["kind"], "LOGICAL_ENVELOPE")
        semantics = self.result["r22_coverage_semantics"]
        self.assertTrue(semantics["no_combined_or_cross_kind_coverage_comparison"])
        self.assertTrue(semantics["no_single_cause_attribution_from_coverage_patterns"])
        self.assertIn("interval_construction_basic_vs_percentile",
                      semantics["potential_undercoverage_sources"])

    def test_evidence_binding_excludes_all_analysis_replicates(self):
        binding = self.result["evidence_binding"]
        self.assertIn("matched A/B/C bootstrap replicates", binding["excluded"])
        digest = binding["evidence_sha256"]
        mutated = json.loads(json.dumps(self.result))
        mutated["matched_interval_contrast"]["intervals"]["registered"]["RNI"][
            "B_percentile_share_conditional"]["bounds"] = [0.0, 1.0]
        self.assertEqual(mutated["evidence_binding"]["evidence_sha256"], digest)

    def test_negative_controls_and_exact_anchor_certificate_inherited(self):
        result = self.result
        self.assertEqual(result["surgery_arm_sampled"]["reflection"]["Lambda"], 0.0)
        for partition in result["surgery_certificate_sampled"][
                "attribution_sensitivity"]["convention_reports"].values():
            for rep in partition.values():
                self.assertEqual(rep["composite_interval"]["bounds"], [0.0, 0.0])
        self.assertLessEqual(result["action_decoupled_negative_control_sampled"][
            "channels"]["a_exec_open_loop"], 1e-3)
        exact = result["baseline_certificate_exact"]
        self.assertEqual(exact["certificate_mode"], "POINT")
        self.assertAlmostEqual(exact["attribution_sensitivity"]["convention_reports"][
            "registered"]["RNI"]["composite_interval"]["bounds"][0],
            0.4608565248033332, places=9)

    def test_policy_or_c_interval_tampering_fails_closed(self):
        broken = json.loads(json.dumps(self.result))
        broken["contrast_policy"]["not_formal_bias_decomposition"] = False
        with self.assertRaises(ValueError):
            validate_result(broken)
        broken2 = json.loads(json.dumps(self.result))
        broken2["matched_convention_table"]["registered"]["RNI"][
            "matched_interval_methods"][METHOD_C]["bounds"] = [0.0, 1.0]
        with self.assertRaises(ValueError):
            validate_result(broken2)
        broken3 = json.loads(json.dumps(self.result))
        broken3["matched_interval_contrast"]["intervals"]["registered"]["RNI"][
            METHOD_B]["bounds"] = [0.0, 1.0]
        with self.assertRaises(ValueError):
            validate_result(broken3)

    def test_saved_default_artifact_replays_and_preserves_r21(self):
        root = Path(__file__).resolve().parents[1]
        saved = json.loads((root / "analysis_r22_joint_audit.json").read_text(
            encoding="utf-8"))
        old = json.loads((root / "analysis_r21_joint_audit.json").read_text(
            encoding="utf-8"))
        validate_result(saved)
        self.assertEqual(saved["artifact_version"], "R22-native-joint-audit-v1")
        self.assertEqual(saved["baseline_certificate"], old["baseline_certificate"])
        self.assertEqual(saved["joint_bootstrap"], old["joint_bootstrap"])
        self.assertEqual(saved["status"], "INTERNAL_JOINT_LOG_CONCEPT_VALIDATION_NOT_EXTERNAL")
        self.assertIn("R21", saved["scope"]["supersedes"])
        self.assertFalse(saved["scope"]["external_construct_validation"])
        for partition in ("registered", "R_as_normative_memory"):
            for convention in ("RNI", "NRI", "order_average"):
                new_c = saved["matched_convention_table"][partition][convention][
                    "matched_interval_methods"][METHOD_C]
                old_c = old["joint_bootstrap"]["composite_intervals"][partition][convention]
                self.assertEqual(new_c["bounds"], old_c["percentile_95"])


if __name__ == "__main__":
    unittest.main()
