"""R20 joint-log audit guards: in-certificate data-driven detection, real
interval propagation, diagnostic plug-in separation, evidence binding, and
sampled negative controls.  Software checks only (R20 review item 4): no
expected empirical outcome is a pass condition; frozen-artifact values are
snapshot regressions."""
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim.aggregate import composite_A  # noqa: E402
from autonomy_sim.r20_detection import (DETECTION_LIMIT,  # noqa: E402
                                        DETECTION_RULE_VERSION,
                                        basic_bootstrap_bias_corrected_interval,
                                        classify_share_interval)
from autonomy_sim.r20_guards import validate_r20_certificate  # noqa: E402
from analysis_r20_joint_audit import compute, validate_result  # noqa: E402

CONVENTIONS = ("RNI", "NRI", "order_average")


class R20JointAuditFields(unittest.TestCase):
    def test_diagnostic_plugin_equals_five_channel_recomputation_not_gate(self):
        result = compute(n_samples=1024, seed=7, n_bootstrap=10)
        sampled = result["sampled"]
        channels = sampled["channels"]
        independent = float(composite_A(
            sampled["viability_state"],
            (channels["a_org_RNI"], channels["a_goal_structural"],
             channels["a_exec_open_loop"], channels["a_epi"], channels["a_ref"]),
            result["config"]["weights"], sigma=1.0))
        self.assertAlmostEqual(result["diagnostic_state_autonomy_RNI_plugin"],
                               independent, places=12)
        self.assertNotAlmostEqual(result["diagnostic_state_autonomy_RNI_plugin"],
                                  sampled["viability_state"], places=6)
        cert_rep = (result["baseline_certificate"]["attribution_sensitivity"]
                    ["convention_reports"]["registered"]["RNI"])
        self.assertAlmostEqual(cert_rep["diagnostic_plugin_composite"],
                               independent, places=12)

    def test_sampled_baseline_is_interval_with_detection_inside(self):
        result = compute(n_samples=1024, seed=9, n_bootstrap=10)
        cert = result["baseline_certificate"]
        self.assertEqual(validate_r20_certificate(cert), [])
        self.assertEqual(cert["certificate_mode"], "INTERVAL")
        self.assertIsNone(cert["state_autonomy"])
        reports = cert["attribution_sensitivity"]["convention_reports"]
        self.assertEqual(set(reports), {"registered", "R_as_normative_memory"})
        for partition in reports.values():
            self.assertEqual(set(partition), set(CONVENTIONS))
            for rep in partition.values():
                self.assertIn(rep["convention_status"],
                              {"DATA_BELOW_LIMIT", "DATA_ABOVE_LIMIT",
                               "INDETERMINATE_NEAR_ZERO"})
                self.assertEqual(rep["detection_limit"], DETECTION_LIMIT)
                self.assertEqual(rep["detection_rule_version"], DETECTION_RULE_VERSION)
                # Formula consistency with the declared rule (independent).
                perc = rep["share_bootstrap_percentile_95"]
                decision = basic_bootstrap_bias_corrected_interval(
                    rep["diagnostic_plugin_share"], perc[0], perc[1])
                self.assertEqual(decision, rep["share_interval"]["bounds"])
                self.assertEqual(classify_share_interval(decision),
                                 rep["convention_status"])
                # Real (non-degenerate) share intervals.
                self.assertLess(rep["share_interval"]["bounds"][0],
                                rep["share_interval"]["bounds"][1])
        self.assertNotIn("oracle_evaluation", json.dumps(reports))
        self.assertFalse(cert["detection_policy"]["deployable_decision_uses_exact_truth"])
        # Overall range equals the reported-interval hull.
        bounds = [rep["composite_interval"]["bounds"]
                  for partition in reports.values() for rep in partition.values()]
        hull = [min(b[0] for b in bounds), max(b[1] for b in bounds)]
        self.assertEqual(cert["state_autonomy_interval"], hull)
        self.assertEqual(cert["attribution_sensitivity"]["overall_composite_range"], hull)

    def test_evidence_binding_is_immutable_inputs_only(self):
        result = compute(n_samples=1024, seed=11, n_bootstrap=10)
        binding = result["evidence_binding"]
        self.assertEqual(binding["policy"], "IMMUTABLE_RAW_INPUTS_ONLY_NOT_ANALYSIS_OUTPUTS")
        self.assertEqual(set(binding["payload"]),
                         {"log_hashes", "config", "seed", "n_samples_per_stream",
                          "n_bootstrap", "log_schema"})
        self.assertEqual(result["baseline_certificate"]["evidence_hash"],
                         binding["evidence_sha256"])
        mutated = json.loads(json.dumps(result))
        mutated["sampled"]["channels"]["a_epi"] = 0.5
        mutated["detection_reports"]["registered"]["NRI"]["convention_status"] = "DATA_BELOW_LIMIT"
        self.assertEqual(mutated["evidence_binding"]["evidence_sha256"],
                         binding["evidence_sha256"])

    def test_exact_certificate_point_anchors_and_oracle_label(self):
        result = compute(n_samples=1024, seed=13, n_bootstrap=10)
        cert = result["baseline_certificate_exact"]
        self.assertEqual(validate_r20_certificate(cert), [])
        self.assertEqual(cert["certificate_mode"], "POINT")
        reports = cert["attribution_sensitivity"]["convention_reports"]["registered"]
        self.assertAlmostEqual(reports["RNI"]["composite_interval"]["bounds"][0],
                               0.4608565248033332, places=9)
        self.assertAlmostEqual(reports["NRI"]["composite_interval"]["bounds"][0],
                               0.0003907988672884718, places=9)
        self.assertAlmostEqual(reports["order_average"]["composite_interval"]["bounds"][0],
                               0.4011989072662361, places=9)
        self.assertEqual(cert["sensitivity_flags"], ["ORDER_SENSITIVE", "MODEL_SENSITIVE"])
        self.assertEqual(cert["sensitivity_status"]["order"]["status"], "CONFIRMED_SENSITIVE")
        oracle = reports["NRI"]["oracle_detection"]
        self.assertTrue(oracle["oracle_below_limit"])
        self.assertEqual(oracle["label"],
                         "ORACLE_ASSISTED_VALIDATION_FIXTURE_ONLY_NOT_DEPLOYABLE")

    def test_sampled_surgery_annihilates_all_convention_intervals(self):
        result = compute(n_samples=1024, seed=15, n_bootstrap=10)
        surgery = result["surgery_arm_sampled"]
        self.assertEqual(surgery["reflection"]["Lambda"], 0.0)
        cert = result["surgery_certificate_sampled"]
        self.assertEqual(validate_r20_certificate(cert), [])
        for partition in cert["attribution_sensitivity"]["convention_reports"].values():
            for rep in partition.values():
                self.assertEqual(rep["composite_interval"]["bounds"], [0.0, 0.0])
        self.assertEqual(cert["state_autonomy_interval"], [0.0, 0.0])
        self.assertEqual(cert["historical_formation_profile"]["formation_status"],
                         "REGISTERED_SURGERY")
        self.assertEqual(result["surgery_certificate_exact"]["state_autonomy"], 0.0)

    def test_sampled_decoupled_zero_within_sampling_precision(self):
        result = compute(n_samples=1024, seed=17, n_bootstrap=10)
        decoupled = result["action_decoupled_negative_control_sampled"]
        self.assertLessEqual(decoupled["channels"]["a_exec_open_loop"], 1e-3)
        self.assertEqual(decoupled["execution_open_loop"]["score"]
                         ["input_distribution_over_allowed"], [0.25] * 4)
        cert = result["decoupled_certificate_sampled"]
        self.assertEqual(validate_r20_certificate(cert), [])
        self.assertLessEqual(cert["channel_profile"]["a_exec"]["value"], 1e-3)
        self.assertEqual(result["action_decoupled_negative_control_exact"]
                         ["execution_open_loop"]["state_averaged_a_exec"], 0.0)

    def test_audit_and_certificate_detection_agree_oracle_labeled(self):
        result = compute(n_samples=1024, seed=19, n_bootstrap=10)
        cert_reports = (result["baseline_certificate"]["attribution_sensitivity"]
                        ["convention_reports"])
        for partition, conventions in result["detection_reports"].items():
            for convention, rep in conventions.items():
                self.assertEqual(rep["convention_status"],
                                 cert_reports[partition][convention]["convention_status"])
                self.assertEqual(rep["oracle_evaluation"]["label"],
                                 "ORACLE_ASSISTED_VALIDATION_FIXTURE_ONLY_NOT_DEPLOYABLE")
                self.assertIn(rep["oracle_evaluation"]["classification_vs_oracle"],
                              {"TRUE_BELOW", "FALSE_ABOVE", "INDETERMINATE_TRUE_BELOW",
                               "TRUE_ABOVE", "FALSE_BELOW", "INDETERMINATE_TRUE_ABOVE"})

    def test_full_default_run_passes_structural_validation(self):
        result = compute()  # default 8192 / seed 20261122 / 100 bootstrap
        validate_result(result)
        self.assertEqual(result["logs"]["operating_trajectories"], 8192)
        self.assertEqual(result["logs"]["execution_trajectories"], 4 * 8192)

    def test_saved_artifact_replays_and_keeps_boundaries(self):
        root = Path(__file__).resolve().parents[1]
        saved = json.loads((root / "analysis_r20_joint_audit.json").read_text(
            encoding="utf-8"))
        validate_result(saved)
        self.assertEqual(saved["status"],
                         "INTERNAL_JOINT_LOG_CONCEPT_VALIDATION_NOT_EXTERNAL")
        self.assertFalse(saved["scope"]["external_construct_validation"])
        self.assertIn("R19", saved["scope"]["supersedes"])
        self.assertEqual(saved["scope"]["detection_decision_inputs"],
                         "ESTIMABLE_ONLY_NO_EXACT_TRUTH")
        self.assertTrue(saved["detection_rule_declaration"]["declared_before_r20_study_outcomes"])
        # SNAPSHOT of the frozen default-seed artifact (descriptive, not a
        # universal invariant): the data rule returns INDETERMINATE for NRI.
        nri = (saved["baseline_certificate"]["attribution_sensitivity"]
               ["convention_reports"]["registered"]["NRI"])
        self.assertEqual(nri["convention_status"], "INDETERMINATE_NEAR_ZERO")
        self.assertEqual(nri["composite_interval"]["kind"], "LOGICAL_ENVELOPE")
        self.assertEqual(saved["baseline_certificate"]["certificate_mode"], "INTERVAL")


if __name__ == "__main__":
    unittest.main()