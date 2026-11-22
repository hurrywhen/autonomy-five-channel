"""R21 joint-log audit guards: share-conditional conditioning disclosure,
separated coverage semantics, joint-bootstrap diagnostic, evidence binding, and
sampled negative controls.  Software checks only; frozen-artifact values are
explicitly labeled snapshot regressions, not universal invariants."""
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
from autonomy_sim.r21_guards import (COMPOSITE_INTERVAL_CONDITIONING,  # noqa: E402
                                     SHARE_CONDITIONAL_KIND, validate_r21_certificate)
from analysis_r21_joint_audit import compute, validate_result  # noqa: E402

CONVENTIONS = ("RNI", "NRI", "order_average")


def small(**kw):
    params = dict(n_samples=1024, seed=7, n_bootstrap=10, n_joint_bootstrap=20)
    params.update(kw)
    return compute(**params)


class R21JointAuditFields(unittest.TestCase):
    def test_diagnostic_plugin_equals_five_channel_recomputation(self):
        result = small()
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

    def test_sampled_baseline_interval_with_conditioning_inside(self):
        result = small(seed=9)
        cert = result["baseline_certificate"]
        self.assertEqual(validate_r21_certificate(cert), [])
        self.assertEqual(cert["certificate_mode"], "INTERVAL")
        self.assertIsNone(cert["state_autonomy"])
        self.assertEqual(cert["composite_interval_conditioning"],
                         COMPOSITE_INTERVAL_CONDITIONING)
        reports = cert["attribution_sensitivity"]["convention_reports"]
        self.assertEqual(set(reports), {"registered", "R_as_normative_memory"})
        for partition in reports.values():
            self.assertEqual(set(partition), set(CONVENTIONS))
            for rep in partition.values():
                self.assertEqual(rep["detection_limit"], DETECTION_LIMIT)
                self.assertEqual(rep["detection_rule_version"], DETECTION_RULE_VERSION)
                perc = rep["share_bootstrap_percentile_95"]
                decision = basic_bootstrap_bias_corrected_interval(
                    rep["diagnostic_plugin_share"], perc[0], perc[1])
                self.assertEqual(decision, rep["share_interval"]["bounds"])
                self.assertEqual(classify_share_interval(decision), rep["convention_status"])
                self.assertEqual(rep["share_interval"]["kind"], "SAMPLING_BASIC_BOOTSTRAP")
                ci = rep["composite_interval"]
                self.assertEqual(ci["conditioning_scope"], "other_channels_fixed_at_plugin")
                if rep["convention_status"] == "DATA_ABOVE_LIMIT":
                    self.assertEqual(ci["kind"], SHARE_CONDITIONAL_KIND)
                else:
                    self.assertEqual(ci["kind"], "LOGICAL_ENVELOPE")
        self.assertNotIn("oracle_evaluation", json.dumps(reports))
        bounds = [rep["composite_interval"]["bounds"]
                  for partition in reports.values() for rep in partition.values()]
        hull = [min(b[0] for b in bounds), max(b[1] for b in bounds)]
        self.assertEqual(cert["state_autonomy_interval"], hull)

    def test_coverage_semantics_separated_in_table(self):
        result = small(seed=11)
        self.assertEqual(result["coverage_semantics"]
                         ["no_combined_or_cross_kind_coverage_comparison"], True)
        table = result["convention_composite_table"]["registered"]
        for convention, row in table.items():
            kind = row["reported_interval_kind"]
            if kind == "LOGICAL_ENVELOPE":
                self.assertIsNotNone(row["logical_envelope_anchor_containment"])
                self.assertIsNone(row["share_conditional_sampling_covers_exact"])
            elif kind == SHARE_CONDITIONAL_KIND:
                self.assertIsNotNone(row["share_conditional_sampling_covers_exact"])
                self.assertIsNone(row["logical_envelope_anchor_containment"])
            self.assertIsNotNone(row["joint_sampling_interval"])
            self.assertIsNotNone(row["joint_sampling_covers_exact"])

    def test_joint_bootstrap_is_supplementary_diagnostic(self):
        result = small(seed=13)
        jb = result["joint_bootstrap"]
        self.assertEqual(jb["n_bootstrap"], result["n_joint_bootstrap"])
        self.assertTrue(jb["scope"].startswith("SUPPLEMENTARY_JOINT_DIAGNOSTIC"))
        self.assertIn("DOES_NOT_REMOVE_PLUGIN_BIAS", jb["scope"])
        for partition, conventions in jb["composite_intervals"].items():
            for convention, iv in conventions.items():
                lo, hi = iv["percentile_95"]
                self.assertTrue(0.0 <= lo <= hi <= 1.0)
        # The joint diagnostic is NOT inside the formal certificate.
        self.assertNotIn("joint_bootstrap", result["baseline_certificate"])

    def test_evidence_binding_immutable_inputs_only(self):
        result = small(seed=15)
        binding = result["evidence_binding"]
        self.assertEqual(binding["policy"], "IMMUTABLE_RAW_INPUTS_ONLY_NOT_ANALYSIS_OUTPUTS")
        self.assertEqual(set(binding["payload"]),
                         {"log_hashes", "config", "seed", "n_samples_per_stream",
                          "n_bootstrap", "log_schema"})
        self.assertEqual(result["baseline_certificate"]["evidence_hash"],
                         binding["evidence_sha256"])
        mutated = json.loads(json.dumps(result))
        mutated["joint_bootstrap"]["composite_intervals"]["registered"]["RNI"]["percentile_95"] = [0.0, 1.0]
        mutated["sampled"]["channels"]["a_epi"] = 0.5
        self.assertEqual(mutated["evidence_binding"]["evidence_sha256"],
                         binding["evidence_sha256"])

    def test_exact_certificate_point_anchors_and_oracle_label(self):
        result = small(seed=17)
        cert = result["baseline_certificate_exact"]
        self.assertEqual(validate_r21_certificate(cert), [])
        self.assertEqual(cert["certificate_mode"], "POINT")
        reports = cert["attribution_sensitivity"]["convention_reports"]["registered"]
        self.assertAlmostEqual(reports["RNI"]["composite_interval"]["bounds"][0],
                               0.4608565248033332, places=9)
        self.assertAlmostEqual(reports["NRI"]["composite_interval"]["bounds"][0],
                               0.0003907988672884718, places=9)
        self.assertEqual(cert["sensitivity_flags"], ["ORDER_SENSITIVE", "MODEL_SENSITIVE"])
        self.assertEqual(reports["NRI"]["oracle_detection"]["label"],
                         "ORACLE_ASSISTED_VALIDATION_FIXTURE_ONLY_NOT_DEPLOYABLE")

    def test_sampled_surgery_and_decoupled_controls(self):
        result = small(seed=19)
        surgery = result["surgery_arm_sampled"]
        self.assertEqual(surgery["reflection"]["Lambda"], 0.0)
        scert = result["surgery_certificate_sampled"]
        self.assertEqual(validate_r21_certificate(scert), [])
        for partition in scert["attribution_sensitivity"]["convention_reports"].values():
            for rep in partition.values():
                self.assertEqual(rep["composite_interval"]["bounds"], [0.0, 0.0])
        decoupled = result["action_decoupled_negative_control_sampled"]
        self.assertLessEqual(decoupled["channels"]["a_exec_open_loop"], 1e-3)
        dcert = result["decoupled_certificate_sampled"]
        self.assertEqual(validate_r21_certificate(dcert), [])
        self.assertLessEqual(dcert["channel_profile"]["a_exec"]["value"], 1e-3)

    def test_audit_and_certificate_detection_agree_oracle_labeled(self):
        result = small(seed=21)
        cert_reports = result["baseline_certificate"]["attribution_sensitivity"]["convention_reports"]
        for partition, conventions in result["detection_reports"].items():
            for convention, rep in conventions.items():
                self.assertEqual(rep["convention_status"],
                                 cert_reports[partition][convention]["convention_status"])
                self.assertEqual(rep["composite_interval"]["conditioning_scope"],
                                 "other_channels_fixed_at_plugin")
                self.assertEqual(rep["oracle_evaluation"]["label"],
                                 "ORACLE_ASSISTED_VALIDATION_FIXTURE_ONLY_NOT_DEPLOYABLE")

    def test_full_default_run_passes_structural_validation(self):
        result = compute()  # default 8192 / seed 20261122 / 100 share / 200 joint
        validate_result(result)
        self.assertEqual(result["logs"]["operating_trajectories"], 8192)
        self.assertEqual(result["logs"]["execution_trajectories"], 4 * 8192)
        self.assertEqual(result["n_joint_bootstrap"], 200)

    def test_saved_artifact_replays_and_keeps_boundaries(self):
        root = Path(__file__).resolve().parents[1]
        saved = json.loads((root / "analysis_r21_joint_audit.json").read_text(encoding="utf-8"))
        validate_result(saved)
        self.assertEqual(saved["status"], "INTERNAL_JOINT_LOG_CONCEPT_VALIDATION_NOT_EXTERNAL")
        self.assertFalse(saved["scope"]["external_construct_validation"])
        self.assertIn("R20", saved["scope"]["supersedes"])
        self.assertEqual(saved["scope"]["composite_interval_conditioning"],
                         "SHARE_CONDITIONAL_OTHER_CHANNELS_FIXED_AT_PLUGIN")
        # SNAPSHOT of the frozen default-seed artifact (descriptive, not a universal
        # invariant): NRI is INDETERMINATE with a logical envelope; the share-conditional
        # RNI interval misses the anchor while the joint diagnostic covers it.
        table = saved["convention_composite_table"]["registered"]
        self.assertEqual(table["NRI"]["convention_status"], "INDETERMINATE_NEAR_ZERO")
        self.assertEqual(table["NRI"]["reported_interval_kind"], "LOGICAL_ENVELOPE")
        self.assertTrue(table["NRI"]["logical_envelope_anchor_containment"])
        self.assertEqual(table["RNI"]["reported_interval_kind"], SHARE_CONDITIONAL_KIND)
        self.assertFalse(table["RNI"]["share_conditional_sampling_covers_exact"])
        self.assertTrue(table["RNI"]["joint_sampling_covers_exact"])
        self.assertEqual(saved["baseline_certificate"]["certificate_mode"], "INTERVAL")


if __name__ == "__main__":
    unittest.main()