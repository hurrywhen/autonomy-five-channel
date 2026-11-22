"""R21 certificate schema: conditioning disclosure (share-conditional composite
intervals + conditioning_scope + policy), separated coverage semantics, and
fail-closed governance.  R20 detection decisions and three-state sensitivity are
unchanged.  Software checks only; empirical phenomena are not pass conditions."""
import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim.r20_detection import basic_bootstrap_bias_corrected_interval  # noqa: E402
from autonomy_sim.r20_guards import produce_r20_certificate  # noqa: E402
from autonomy_sim.r21_guards import (  # noqa: E402
    COMPOSITE_INTERVAL_CONDITIONING, CONDITIONING_SCOPES, GRADE_INTERVAL_INDETERMINATE,
    GRADE_ZERO_FLOW, INTERVAL_KINDS, SHARE_CONDITIONAL_KIND, produce_r21_certificate,
    validate_r21_certificate, write_r21_certificate,
)

A_EXEC = 0.26550220320535944
A_REF = 0.5310044064107189
TOTAL_DI = 0.7305954885971118
W5 = [0.2] * 5


def point_partition(rni=1.0, nri=4.3846787364730815e-16, avg=0.5):
    return {"flows_bits_RNI": [nri * TOTAL_DI, rni * TOTAL_DI, 0.0],
            "flows_bits_NRI": [nri * TOTAL_DI, rni * TOTAL_DI, 0.0],
            "joint_di_bits": TOTAL_DI,
            "normative_share_RNI": rni, "normative_share_NRI": nri,
            "normative_share_order_average": avg}


def interval_partition(rni, nri, perc_rni, perc_nri, perc_avg):
    rep = point_partition(rni=rni, nri=nri, avg=0.5 * (rni + nri))
    residual = (1.0 - rni - nri) * TOTAL_DI
    rep["flows_bits_RNI"] = [nri * TOTAL_DI, rni * TOTAL_DI, residual]
    rep["flows_bits_NRI"] = [nri * TOTAL_DI, rni * TOTAL_DI, residual]
    rep["share_bootstrap_percentile_95"] = {
        "RNI": list(perc_rni), "NRI": list(perc_nri), "order_average": list(perc_avg)}
    return rep


def alternative_interval(s, perc):
    return {"flows_bits_RNI": [(1.0 - s) * TOTAL_DI, s * TOTAL_DI, 0.0],
            "flows_bits_NRI": [s * TOTAL_DI, (1.0 - s) * TOTAL_DI, 0.0],
            "joint_di_bits": TOTAL_DI,
            "normative_share_RNI": s, "normative_share_NRI": s,
            "normative_share_order_average": s,
            "share_bootstrap_percentile_95": {
                "RNI": list(perc), "NRI": list(perc), "order_average": list(perc)}}


def l2_profile(*, org_value=None, org_interval=None, org_kind=None):
    if org_interval is not None:
        org = {"value": None, "state": "INTERVAL", "interval": list(org_interval),
               "interval_kind": org_kind, "protocol_version": "RNI_R21"}
    else:
        org = {"value": 1.0 if org_value is None else org_value,
               "state": "DEFINED", "interval": None, "protocol_version": "RNI_R21"}
    return {
        "a_org": org,
        "a_goal": {"value": 0.5, "state": "DEFINED", "interval": None,
                   "protocol_version": "GOAL_R21", "structural_point": 0.5,
                   "irl_interval": [0.5, 1.0], "irl_interval_kind": "MODEL_SELECTION"},
        "a_exec": {"value": A_EXEC, "state": "DEFINED", "interval": None,
                   "protocol_version": "EXEC_R21", "horizon_actions": 2,
                   "uses_intermediate_observations": False},
        "a_epi": {"value": 0.9, "state": "DEFINED", "interval": [0.88, 0.92],
                  "interval_kind": "SAMPLING_NORMAL_APPROX", "protocol_version": "EPI_R21"},
        "a_ref": {"value": A_REF, "state": "DEFINED", "interval": None,
                  "protocol_version": "REF_R21", "fidelity": A_REF,
                  "endorsement_consistency": 1.0, "Lambda": 1.0,
                  "event_counts": {"normative_update_events": 24576,
                                   "endorsement_events": 24576, "surgery_contexts": 8192}},
    }


def produce(profile=None, attr=None, **overrides):
    kwargs = dict(layer="L2", viability_state=0.8, defense_readiness=0.7,
                  surgery_history=0, lambda_value=1.0, lambda_status="DEFINED",
                  source_registration="COMPLETE", mechanism_evidence="NONE",
                  goal_mode="STRUCTURAL_POINT",
                  lambda_time_origin="AUDIT_CURRENT_REMOVAL",
                  lambda_counterfactual_scope="REMOVE_REGISTERED_SURGERIES_AT_AUDIT",
                  model_hash="a" * 64, evidence_hash="b" * 64)
    kwargs.update(overrides)
    if attr is None:
        attr = {"registered_partition": point_partition(),
                "alternative_partitions": {"R_as_normative_memory": alternative_interval(
                    1.0, (0.99, 1.0))},
                "weights": list(W5), "sigma": 1.0}
    return produce_r21_certificate(
        channel_profile=profile if profile is not None else l2_profile(),
        attribution=attr, **kwargs)


def interval_fixture(rni=0.9958235741244843, nri=0.0033464053205058595,
                     perc_rni=(0.9882402653377889, 0.9950900942070936),
                     perc_nri=(0.004763275099774422, 0.0107114682051783),
                     perc_avg=(0.4940, 0.5052)):
    reg = interval_partition(rni, nri, perc_rni, perc_nri, perc_avg)
    alt = alternative_interval(0.9667638674650484, (0.9559, 0.9776))
    org = basic_bootstrap_bias_corrected_interval(rni, *perc_rni)
    profile = l2_profile(org_interval=org, org_kind="SAMPLING_BASIC_BOOTSTRAP")
    attr = {"registered_partition": reg,
            "alternative_partitions": {"R_as_normative_memory": alt},
            "weights": list(W5), "sigma": 1.0}
    return profile, attr


class ConditioningDisclosure(unittest.TestCase):
    def test_above_limit_composite_is_share_conditional_with_scope(self):
        profile, attr = interval_fixture()
        cert = produce(profile=profile, attr=attr)
        self.assertEqual(validate_r21_certificate(cert), [])
        reports = cert["attribution_sensitivity"]["convention_reports"]["registered"]
        rni = reports["RNI"]
        self.assertEqual(rni["convention_status"], "DATA_ABOVE_LIMIT")
        self.assertEqual(rni["composite_interval"]["kind"], SHARE_CONDITIONAL_KIND)
        self.assertEqual(rni["composite_interval"]["conditioning_scope"],
                         "other_channels_fixed_at_plugin")
        self.assertEqual(rni["composite_interval_sampling"]["kind"], SHARE_CONDITIONAL_KIND)
        self.assertEqual(rni["composite_interval_sampling"]["conditioning_scope"],
                         "other_channels_fixed_at_plugin")
        # The share interval itself is unconditional sampling.
        self.assertEqual(rni["share_interval"]["kind"], "SAMPLING_BASIC_BOOTSTRAP")
        self.assertNotIn("conditioning_scope", rni["share_interval"])

    def test_certificate_declares_conditioning_policy(self):
        profile, attr = interval_fixture()
        cert = produce(profile=profile, attr=attr)
        self.assertEqual(cert["composite_interval_conditioning"],
                         COMPOSITE_INTERVAL_CONDITIONING)
        self.assertEqual(cert["composite_interval_conditioning"]["design"], "SHARE_CONDITIONAL")
        self.assertTrue(cert["composite_interval_conditioning"]
                        ["not_a_full_joint_uncertainty_interval"])
        self.assertIn("directed_information_plugin_bias",
                      cert["composite_interval_conditioning"]["undercoverage_causes"])
        self.assertIn("share_conditional_design_other_channels_fixed",
                      cert["composite_interval_conditioning"]["undercoverage_causes"])
        self.assertIn("SHARE-CONDITIONAL", cert["scalar_export_warning"])

    def test_envelope_also_discloses_scope_and_is_not_coverage(self):
        profile, attr = interval_fixture()
        cert = produce(profile=profile, attr=attr)
        nri = cert["attribution_sensitivity"]["convention_reports"]["registered"]["NRI"]
        self.assertEqual(nri["convention_status"], "INDETERMINATE_NEAR_ZERO")
        self.assertEqual(nri["composite_interval"]["kind"], "LOGICAL_ENVELOPE")
        self.assertEqual(nri["composite_interval"]["conditioning_scope"],
                         "other_channels_fixed_at_plugin")
        self.assertIn("LOGICAL_ENVELOPE", cert["scalar_export_warning"])
        self.assertIn("not statistical coverage", cert["scalar_export_warning"])

    def test_composite_bounds_unchanged_from_r20_only_kind_renamed(self):
        # R21 renames the kind and adds scope; the propagated bounds are identical
        # to R20 (same share interval, same fixed other channels).
        profile, attr = interval_fixture()
        r21 = produce(profile=profile, attr=attr)
        r20 = produce_r20_certificate(
            channel_profile=profile, attribution=attr, layer="L2",
            viability_state=0.8, defense_readiness=0.7, surgery_history=0,
            lambda_value=1.0, lambda_status="DEFINED", source_registration="COMPLETE",
            mechanism_evidence="NONE", goal_mode="STRUCTURAL_POINT",
            lambda_time_origin="AUDIT_CURRENT_REMOVAL",
            lambda_counterfactual_scope="REMOVE_REGISTERED_SURGERIES_AT_AUDIT",
            model_hash="a" * 64, evidence_hash="b" * 64)
        for partition in ("registered", "R_as_normative_memory"):
            for convention in ("RNI", "NRI", "order_average"):
                b21 = r21["attribution_sensitivity"]["convention_reports"][partition][convention]["composite_interval"]["bounds"]
                b20 = r20["attribution_sensitivity"]["convention_reports"][partition][convention]["composite_interval"]["bounds"]
                self.assertEqual(b21, b20)
        self.assertEqual(r21["state_autonomy_interval"], r20["state_autonomy_interval"])

    def test_unknown_channel_scope_is_declared_bounds(self):
        profile, attr = interval_fixture()
        profile["a_epi"] = {"value": None, "state": "UNKNOWN", "interval": None,
                            "protocol_version": "EPI_R21", "reason": "NO_GROUND_TRUTH"}
        cert = produce(profile=profile, attr=attr)
        rep = cert["attribution_sensitivity"]["convention_reports"]["registered"]["RNI"]
        self.assertEqual(rep["composite_interval"]["conditioning_scope"],
                         "other_channels_at_declared_bounds")
        self.assertEqual(cert["sensitivity_status"]["order"]["status"], "NOT_EVALUABLE")


class PointAndSensitivityUnchanged(unittest.TestCase):
    def test_point_exact_reproduces_anchors_and_oracle_label(self):
        cert = produce()
        self.assertEqual(cert["certificate_mode"], "POINT")
        reports = cert["attribution_sensitivity"]["convention_reports"]["registered"]
        self.assertAlmostEqual(reports["RNI"]["composite_interval"]["bounds"][0],
                               0.4608565248033332, places=9)
        self.assertAlmostEqual(reports["NRI"]["composite_interval"]["bounds"][0],
                               0.0003907988672884718, places=9)
        self.assertEqual(reports["NRI"]["composite_interval"]["kind"], "POINT_EXACT")
        self.assertNotIn("conditioning_scope", reports["NRI"]["composite_interval"])
        self.assertEqual(reports["NRI"]["oracle_detection"]["label"],
                         "ORACLE_ASSISTED_VALIDATION_FIXTURE_ONLY_NOT_DEPLOYABLE")
        self.assertEqual(cert["sensitivity_flags"], ["ORDER_SENSITIVE", "MODEL_SENSITIVE"])

    def test_three_state_sensitivity_inherited(self):
        # Disjoint tight intervals -> CONFIRMED.
        reg = interval_partition(0.9, 0.1, (0.89, 0.91), (0.09, 0.11), (0.49, 0.51))
        org = basic_bootstrap_bias_corrected_interval(0.9, 0.89, 0.91)
        profile = l2_profile(org_interval=org, org_kind="SAMPLING_BASIC_BOOTSTRAP")
        attr = {"registered_partition": reg, "alternative_partitions": {},
                "weights": list(W5), "sigma": 1.0}
        cert = produce(profile=profile, attr=attr)
        self.assertEqual(cert["sensitivity_status"]["order"]["status"], "CONFIRMED_SENSITIVE")
        # Overlapping wide intervals -> INDETERMINATE, never agreement.
        reg2 = interval_partition(0.5, 0.5, (0.1, 0.9), (0.1, 0.9), (0.1, 0.9))
        org2 = basic_bootstrap_bias_corrected_interval(0.5, 0.1, 0.9)
        profile2 = l2_profile(org_interval=org2, org_kind="SAMPLING_BASIC_BOOTSTRAP")
        attr2 = {"registered_partition": reg2,
                 "alternative_partitions": {"same": copy.deepcopy(reg2)},
                 "weights": list(W5), "sigma": 1.0}
        cert2 = produce(profile=profile2, attr=attr2)
        self.assertEqual(cert2["sensitivity_status"]["order"]["status"], "INDETERMINATE")
        self.assertEqual(cert2["sensitivity_flags"], [])
        self.assertEqual(cert2["composite_scalar_grade"], GRADE_INTERVAL_INDETERMINATE)
        # Zero flow -> NOT_EVALUABLE.
        zero = {"flows_bits_RNI": [0, 0, 0], "flows_bits_NRI": [0, 0, 0],
                "joint_di_bits": 0.0, "normative_share_RNI": None,
                "normative_share_NRI": None, "normative_share_order_average": None,
                "share_bootstrap_percentile_95": {"RNI": None, "NRI": None,
                                                  "order_average": None}}
        profile3 = l2_profile(org_interval=[0.0, 1.0], org_kind="LOGICAL_ENVELOPE")
        attr3 = {"registered_partition": zero, "alternative_partitions": {},
                 "weights": list(W5), "sigma": 1.0}
        cert3 = produce(profile=profile3, attr=attr3)
        self.assertEqual(cert3["sensitivity_status"]["order"]["status"], "NOT_EVALUABLE")
        self.assertEqual(cert3["composite_scalar_grade"], GRADE_ZERO_FLOW)
        self.assertEqual(cert3["attribution_sensitivity"]["convention_reports"]
                         ["registered"]["RNI"]["composite_interval"]["conditioning_scope"],
                         "other_channels_fixed_at_plugin")


class FailClosed(unittest.TestCase):
    def test_missing_conditioning_scope_rejected(self):
        profile, attr = interval_fixture()
        cert = produce(profile=profile, attr=attr)
        bad = copy.deepcopy(cert)
        del bad["attribution_sensitivity"]["convention_reports"]["registered"]["RNI"]["composite_interval"]["conditioning_scope"]
        self.assertTrue(validate_r21_certificate(bad))

    def test_wrong_kind_rejected(self):
        profile, attr = interval_fixture()
        cert = produce(profile=profile, attr=attr)
        bad = copy.deepcopy(cert)
        bad["attribution_sensitivity"]["convention_reports"]["registered"]["RNI"]["composite_interval"]["kind"] = "SAMPLING_BASIC_BOOTSTRAP"
        self.assertTrue(validate_r21_certificate(bad))

    def test_invalid_scope_rejected(self):
        profile, attr = interval_fixture()
        cert = produce(profile=profile, attr=attr)
        bad = copy.deepcopy(cert)
        bad["attribution_sensitivity"]["convention_reports"]["registered"]["RNI"]["composite_interval"]["conditioning_scope"] = "FULL_JOINT"
        self.assertTrue(validate_r21_certificate(bad))

    def test_conditioning_policy_forgery_rejected(self):
        profile, attr = interval_fixture()
        cert = produce(profile=profile, attr=attr)
        bad = copy.deepcopy(cert)
        bad["composite_interval_conditioning"]["design"] = "FULL_JOINT"
        self.assertTrue(validate_r21_certificate(bad))
        bad2 = copy.deepcopy(cert)
        del bad2["composite_interval_conditioning"]
        self.assertTrue(validate_r21_certificate(bad2))

    def test_flag_suppression_and_range_forgery_rejected(self):
        profile, attr = interval_fixture()
        cert = produce(profile=profile, attr=attr)
        bad = copy.deepcopy(cert)
        bad["sensitivity_flags"] = []
        self.assertTrue(validate_r21_certificate(bad))
        bad2 = copy.deepcopy(cert)
        bad2["attribution_sensitivity"]["overall_composite_range"] = [0.0, 0.9]
        self.assertTrue(validate_r21_certificate(bad2))
        bad3 = copy.deepcopy(cert)
        bad3["state_autonomy"] = 0.1478374
        self.assertTrue(validate_r21_certificate(bad3))

    def test_r20_certificate_rejected_by_r21(self):
        profile, attr = interval_fixture()
        r20 = produce_r20_certificate(
            channel_profile=profile, attribution=attr, layer="L2",
            viability_state=0.8, defense_readiness=0.7, surgery_history=0,
            lambda_value=1.0, lambda_status="DEFINED", source_registration="COMPLETE",
            mechanism_evidence="NONE", goal_mode="STRUCTURAL_POINT",
            lambda_time_origin="AUDIT_CURRENT_REMOVAL",
            lambda_counterfactual_scope="REMOVE_REGISTERED_SURGERIES_AT_AUDIT",
            model_hash="a" * 64, evidence_hash="b" * 64)
        self.assertTrue(validate_r21_certificate(r20))

    def test_kind_vocabulary_and_writer(self):
        self.assertIn(SHARE_CONDITIONAL_KIND, INTERVAL_KINDS)
        self.assertIn("SAMPLING_BASIC_BOOTSTRAP", INTERVAL_KINDS)
        self.assertTrue(CONDITIONING_SCOPES <= {
            "other_channels_fixed_at_plugin", "other_channels_at_declared_bounds"})
        import tempfile
        profile, attr = interval_fixture()
        cert = produce(profile=profile, attr=attr)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as handle:
            path = handle.name
        try:
            write_r21_certificate(path, cert)
            broken = copy.deepcopy(cert)
            broken["sensitivity_flags"] = []
            with self.assertRaises(ValueError):
                write_r21_certificate(path, broken)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()