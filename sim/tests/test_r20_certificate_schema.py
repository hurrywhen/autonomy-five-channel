"""R20 certificate schema: data-driven in-certificate detection, real
interval propagation with kinds, three-state sensitivity (never midpoint
agreement), and fail-closed governance.  Software checks only; empirical
phenomena are not pass conditions."""
import copy
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim.r19_guards import produce_r19_certificate  # noqa: E402
from autonomy_sim.r20_detection import (DETECTION_LIMIT,  # noqa: E402
                                        basic_bootstrap_bias_corrected_interval)
from autonomy_sim.r20_guards import (  # noqa: E402
    GRADE_INTERVAL, GRADE_INTERVAL_INDETERMINATE, GRADE_L0, GRADE_SENSITIVE,
    GRADE_ZERO_FLOW, INTERVAL_KINDS, produce_r20_certificate,
    validate_r20_certificate, write_r20_certificate,
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
        "RNI": list(perc_rni), "NRI": list(perc_nri),
        "order_average": list(perc_avg)}
    return rep


def alternative_interval(s, perc):
    # Alternative semantic partition (R reclassified as normative memory):
    # both order shares are ~s; flow layouts differ from the registered one.
    return {"flows_bits_RNI": [(1.0 - s) * TOTAL_DI, s * TOTAL_DI, 0.0],
            "flows_bits_NRI": [s * TOTAL_DI, (1.0 - s) * TOTAL_DI, 0.0],
            "joint_di_bits": TOTAL_DI,
            "normative_share_RNI": s, "normative_share_NRI": s,
            "normative_share_order_average": s,
            "share_bootstrap_percentile_95": {
                "RNI": list(perc), "NRI": list(perc), "order_average": list(perc)}}


def alternative_point():
    return {"flows_bits_RNI": [0.0, TOTAL_DI, 1.281370601525967e-15],
            "flows_bits_NRI": [TOTAL_DI, 0.0, 1.281370601525967e-15],
            "joint_di_bits": TOTAL_DI,
            "normative_share_RNI": 1.0, "normative_share_NRI": 1.0,
            "normative_share_order_average": 1.0}


def l2_profile(*, org_value=None, org_interval=None, org_kind=None):
    if org_interval is not None:
        org = {"value": None, "state": "INTERVAL", "interval": list(org_interval),
               "interval_kind": org_kind, "protocol_version": "RNI_R20"}
    else:
        org = {"value": 1.0 if org_value is None else org_value,
               "state": "DEFINED", "interval": None, "protocol_version": "RNI_R20"}
    return {
        "a_org": org,
        "a_goal": {"value": 0.5, "state": "DEFINED", "interval": None,
                   "protocol_version": "GOAL_R20", "structural_point": 0.5,
                   "irl_interval": [0.5, 1.0], "irl_interval_kind": "MODEL_SELECTION"},
        "a_exec": {"value": A_EXEC, "state": "DEFINED", "interval": None,
                   "protocol_version": "EXEC_R20", "horizon_actions": 2,
                   "uses_intermediate_observations": False},
        "a_epi": {"value": 0.9, "state": "DEFINED", "interval": [0.88, 0.92],
                  "interval_kind": "SAMPLING_NORMAL_APPROX",
                  "protocol_version": "EPI_R20"},
        "a_ref": {"value": A_REF, "state": "DEFINED", "interval": None,
                  "protocol_version": "REF_R20", "fidelity": A_REF,
                  "endorsement_consistency": 1.0, "Lambda": 1.0,
                  "event_counts": {"normative_update_events": 24576,
                                   "endorsement_events": 24576,
                                   "surgery_contexts": 8192}},
    }


def produce(profile=None, attr=None, **overrides):
    kwargs = dict(
        layer="L2", viability_state=0.8, defense_readiness=0.7,
        surgery_history=0, lambda_value=1.0, lambda_status="DEFINED",
        source_registration="COMPLETE", mechanism_evidence="NONE",
        goal_mode="STRUCTURAL_POINT",
        lambda_time_origin="AUDIT_CURRENT_REMOVAL",
        lambda_counterfactual_scope="REMOVE_REGISTERED_SURGERIES_AT_AUDIT",
        model_hash="a" * 64, evidence_hash="b" * 64)
    kwargs.update(overrides)
    if attr is None:
        attr = {"registered_partition": point_partition(),
                "alternative_partitions": {"R_as_normative_memory": alternative_point()},
                "weights": list(W5), "sigma": 1.0}
    return produce_r20_certificate(
        channel_profile=profile if profile is not None else l2_profile(),
        attribution=attr, **kwargs)


def interval_fixture(rni=0.9958235741244843, nri=0.0033464053205058595,
                     perc_rni=(0.9882402653377889, 0.9950900942070936),
                     perc_nri=(0.004763275099774422, 0.0107114682051783),
                     perc_avg=(0.4940, 0.5052), alt=None):
    reg = interval_partition(rni, nri, perc_rni, perc_nri, perc_avg)
    if alt is None:
        alt = alternative_interval(0.9667638674650484, (0.9559, 0.9776))
    org = basic_bootstrap_bias_corrected_interval(rni, *perc_rni)
    profile = l2_profile(org_interval=org, org_kind="SAMPLING_BASIC_BOOTSTRAP")
    attr = {"registered_partition": reg,
            "alternative_partitions": {"R_as_normative_memory": alt},
            "weights": list(W5), "sigma": 1.0}
    return profile, attr


class PointModeDetection(unittest.TestCase):
    def test_exact_point_certificate_reproduces_composites_with_oracle_label(self):
        cert = produce()
        self.assertEqual(cert["certificate_mode"], "POINT")
        self.assertEqual(validate_r20_certificate(cert), [])
        reports = cert["attribution_sensitivity"]["convention_reports"]["registered"]
        self.assertAlmostEqual(reports["RNI"]["composite_interval"]["bounds"][0],
                               0.4608565248033332, places=9)
        self.assertAlmostEqual(reports["NRI"]["composite_interval"]["bounds"][0],
                               0.0003907988672884718, places=9)
        self.assertAlmostEqual(reports["order_average"]["composite_interval"]["bounds"][0],
                               0.4011989072662361, places=9)
        self.assertEqual(reports["NRI"]["convention_status"], "POINT_EXACT")
        self.assertEqual(reports["NRI"]["share_interval"]["kind"], "POINT_EXACT")
        oracle = reports["NRI"]["oracle_detection"]
        self.assertTrue(oracle["oracle_below_limit"])
        self.assertEqual(oracle["label"],
                         "ORACLE_ASSISTED_VALIDATION_FIXTURE_ONLY_NOT_DEPLOYABLE")
        self.assertFalse(reports["RNI"]["oracle_detection"]["oracle_below_limit"])
        self.assertAlmostEqual(cert["state_autonomy"],
                               reports["RNI"]["composite_interval"]["bounds"][0],
                               places=12)

    def test_point_sensitivity_is_confirmed_by_point_separation(self):
        cert = produce()
        self.assertEqual(cert["sensitivity_flags"], ["ORDER_SENSITIVE", "MODEL_SENSITIVE"])
        order = cert["sensitivity_status"]["order"]
        self.assertEqual(order["status"], "CONFIRMED_SENSITIVE")
        self.assertAlmostEqual(order["min_possible_spread"], 0.4604657259, places=7)
        self.assertAlmostEqual(order["worst_case_spread"], 0.4604657259, places=7)
        self.assertAlmostEqual(order["midpoint_spread_descriptive"],
                               0.4604657259, places=7)
        self.assertEqual(cert["composite_scalar_grade"], GRADE_SENSITIVE)
        # Semantic decomposition: per-convention partition differences.
        sem = cert["sensitivity_status"]["semantic"]["per_convention"]
        self.assertAlmostEqual(sem["RNI"]["min_possible_spread"], 0.0, places=9)
        self.assertAlmostEqual(sem["NRI"]["min_possible_spread"], 0.4604657259, places=7)
        self.assertAlmostEqual(sem["order_average"]["min_possible_spread"],
                               0.0596576175, places=7)

    def test_point_conventions_within_threshold_no_confirmed_sensitivity(self):
        # All conventions share 0.5: point spread 0 -> NO_CONFIRMED_SENSITIVITY.
        rep = point_partition(rni=0.5, nri=0.5, avg=0.5)
        attr = {"registered_partition": rep,
                "alternative_partitions": {"same": copy.deepcopy(rep)},
                "weights": list(W5), "sigma": 1.0}
        cert = produce(profile=l2_profile(org_value=0.5), attr=attr)
        self.assertEqual(cert["sensitivity_flags"], [])
        self.assertEqual(cert["sensitivity_status"]["order"]["status"],
                         "NO_CONFIRMED_SENSITIVITY")
        self.assertEqual(cert["sensitivity_status"]["semantic"]["status"],
                         "NO_CONFIRMED_SENSITIVITY")


class IntervalModeDetection(unittest.TestCase):
    def test_sampled_certificate_carries_detection_inside(self):
        profile, attr = interval_fixture()
        cert = produce(profile=profile, attr=attr)
        self.assertEqual(cert["certificate_mode"], "INTERVAL")
        self.assertIsNone(cert["state_autonomy"])
        self.assertEqual(validate_r20_certificate(cert), [])
        reports = cert["attribution_sensitivity"]["convention_reports"]["registered"]
        nri = reports["NRI"]
        self.assertEqual(nri["convention_status"], "INDETERMINATE_NEAR_ZERO")
        self.assertEqual(nri["share_interval"]["kind"], "SAMPLING_BASIC_BOOTSTRAP")
        self.assertEqual(nri["composite_interval"]["kind"], "LOGICAL_ENVELOPE")
        self.assertEqual(nri["composite_interval"]["bounds"][0], 0.0)
        self.assertEqual(nri["detection_limit"], DETECTION_LIMIT)
        self.assertIn("detection_provenance", nri)
        self.assertIn("diagnostic_plugin_composite", nri)
        # Diagnostic plug-in is separated from the reported semantics and may
        # lie outside the reported envelope.
        self.assertGreater(nri["diagnostic_plugin_composite"],
                           nri["composite_interval"]["bounds"][1])
        rni = reports["RNI"]
        self.assertEqual(rni["convention_status"], "DATA_ABOVE_LIMIT")
        self.assertEqual(rni["composite_interval"]["kind"], "SAMPLING_BASIC_BOOTSTRAP")
        # No oracle evaluation inside the formal certificate.
        self.assertNotIn("oracle_evaluation",
                         cert["attribution_sensitivity"]["convention_reports"]["registered"]["NRI"])
        self.assertFalse(cert["detection_policy"]["deployable_decision_uses_exact_truth"])

    def test_real_intervals_propagated_not_degenerate_points(self):
        profile, attr = interval_fixture()
        cert = produce(profile=profile, attr=attr)
        reports = cert["attribution_sensitivity"]["convention_reports"]["registered"]
        for convention, rep in reports.items():
            lo, hi = rep["share_interval"]["bounds"]
            self.assertLess(lo, hi, msg=f"{convention} share interval must be non-degenerate")
        # a_org carries the actual RNI share interval with matching kind.
        org = cert["channel_profile"]["a_org"]
        self.assertEqual(org["state"], "INTERVAL")
        self.assertEqual(org["interval"], reports["RNI"]["share_interval"]["bounds"])
        self.assertEqual(org["interval_kind"], "SAMPLING_BASIC_BOOTSTRAP")

    def test_overall_range_is_hull_of_reported_intervals(self):
        profile, attr = interval_fixture()
        cert = produce(profile=profile, attr=attr)
        reports = cert["attribution_sensitivity"]["convention_reports"]
        bounds = [rep["composite_interval"]["bounds"]
                  for partition in reports.values() for rep in partition.values()]
        hull = [min(b[0] for b in bounds), max(b[1] for b in bounds)]
        self.assertEqual(cert["attribution_sensitivity"]["overall_composite_range"], hull)
        self.assertEqual(cert["state_autonomy_interval"], hull)
        self.assertEqual(cert["current_structural_profile"]
                         ["composite_range_across_conventions"], hull)

    def test_interval_sensitivity_confirmed_by_disjoint_intervals(self):
        # RNI ~0.9 vs NRI ~0.1 with tight intervals: composite intervals are
        # disjoint with separation > threshold -> CONFIRMED_SENSITIVE.
        reg = interval_partition(0.9, 0.1, (0.89, 0.91), (0.09, 0.11), (0.49, 0.51))
        org = basic_bootstrap_bias_corrected_interval(0.9, 0.89, 0.91)
        profile = l2_profile(org_interval=org, org_kind="SAMPLING_BASIC_BOOTSTRAP")
        attr = {"registered_partition": reg, "alternative_partitions": {},
                "weights": list(W5), "sigma": 1.0}
        cert = produce(profile=profile, attr=attr)
        order = cert["sensitivity_status"]["order"]
        self.assertEqual(order["status"], "CONFIRMED_SENSITIVE")
        self.assertGreater(order["min_possible_spread"], 0.05)
        self.assertIn("ORDER_SENSITIVE", cert["sensitivity_flags"])

    def test_overlapping_wide_intervals_are_indeterminate_not_agreement(self):
        # Midpoint spread exceeds the threshold but intervals overlap:
        # INDETERMINATE, never "conventions agree", no flag.
        reg = interval_partition(0.6, 0.4, (0.2, 0.9), (0.1, 0.8), (0.2, 0.8))
        org = basic_bootstrap_bias_corrected_interval(0.6, 0.2, 0.9)
        profile = l2_profile(org_interval=org, org_kind="SAMPLING_BASIC_BOOTSTRAP")
        attr = {"registered_partition": reg,
                "alternative_partitions": {"same": copy.deepcopy(reg)},
                "weights": list(W5), "sigma": 1.0}
        cert = produce(profile=profile, attr=attr)
        order = cert["sensitivity_status"]["order"]
        self.assertEqual(order["status"], "INDETERMINATE")
        self.assertGreater(order["midpoint_spread_descriptive"], 0.05)
        self.assertEqual(order["min_possible_spread"], 0.0)
        self.assertEqual(cert["sensitivity_flags"], [])
        self.assertEqual(cert["composite_scalar_grade"], GRADE_INTERVAL_INDETERMINATE)
        self.assertIn("not evidence of convention agreement",
                      cert["scalar_export_warning"])

    def test_identical_wide_intervals_never_mean_agreement(self):
        # Both conventions [0.1,0.9]-wide: identical intervals only mean both
        # could take any value in the range; sensitivity is INDETERMINATE.
        reg = interval_partition(0.5, 0.5, (0.1, 0.9), (0.1, 0.9), (0.1, 0.9))
        org = basic_bootstrap_bias_corrected_interval(0.5, 0.1, 0.9)
        profile = l2_profile(org_interval=org, org_kind="SAMPLING_BASIC_BOOTSTRAP")
        attr = {"registered_partition": reg,
                "alternative_partitions": {"same": copy.deepcopy(reg)},
                "weights": list(W5), "sigma": 1.0}
        cert = produce(profile=profile, attr=attr)
        self.assertEqual(cert["sensitivity_status"]["order"]["status"], "INDETERMINATE")
        self.assertEqual(cert["sensitivity_flags"], [])
        self.assertIn("not evidence of convention agreement",
                      cert["scalar_export_warning"])

    def test_tight_identical_intervals_no_confirmed_sensitivity(self):
        reg = interval_partition(0.5, 0.5, (0.49, 0.51), (0.49, 0.51), (0.49, 0.51))
        org = basic_bootstrap_bias_corrected_interval(0.5, 0.49, 0.51)
        profile = l2_profile(org_interval=org, org_kind="SAMPLING_BASIC_BOOTSTRAP")
        attr = {"registered_partition": reg,
                "alternative_partitions": {"same": copy.deepcopy(reg)},
                "weights": list(W5), "sigma": 1.0}
        cert = produce(profile=profile, attr=attr)
        self.assertEqual(cert["sensitivity_status"]["order"]["status"],
                         "NO_CONFIRMED_SENSITIVITY")
        self.assertEqual(cert["sensitivity_flags"], [])
        self.assertEqual(cert["composite_scalar_grade"], GRADE_INTERVAL)
        self.assertIn("no confirmed", cert["scalar_export_warning"])


class DegradedAndLayerStates(unittest.TestCase):
    def test_zero_total_flow_not_evaluable(self):
        zero = {"flows_bits_RNI": [0.0, 0.0, 0.0], "flows_bits_NRI": [0.0, 0.0, 0.0],
                "joint_di_bits": 0.0,
                "normative_share_RNI": None, "normative_share_NRI": None,
                "normative_share_order_average": None,
                "share_bootstrap_percentile_95": {"RNI": None, "NRI": None,
                                                  "order_average": None}}
        profile = l2_profile(org_interval=[0.0, 1.0], org_kind="LOGICAL_ENVELOPE")
        attr = {"registered_partition": zero, "alternative_partitions": {},
                "weights": list(W5), "sigma": 1.0}
        cert = produce(profile=profile, attr=attr)
        self.assertEqual(cert["sensitivity_status"]["order"]["status"], "NOT_EVALUABLE")
        self.assertEqual(cert["sensitivity_status"]["semantic"]["status"], "NOT_EVALUABLE")
        self.assertEqual(cert["composite_scalar_grade"], GRADE_ZERO_FLOW)
        self.assertEqual(cert["sensitivity_flags"], [])
        self.assertIn("NOT EVALUABLE", cert["scalar_export_warning"])
        reports = cert["attribution_sensitivity"]["convention_reports"]["registered"]
        for rep in reports.values():
            self.assertEqual(rep["convention_status"], "NOT_EVALUABLE")
            self.assertIsNone(rep["share_interval"])
            self.assertEqual(rep["composite_interval"]["kind"], "LOGICAL_ENVELOPE")
        upper = 0.8 * (1.0 * 0.5 * A_EXEC * 0.9 * A_REF) ** 0.2
        self.assertAlmostEqual(cert["state_autonomy_interval"][1], upper, places=9)

    def test_unknown_channel_not_evaluable_and_limited(self):
        profile, attr = interval_fixture()
        profile["a_epi"] = {"value": None, "state": "UNKNOWN", "interval": None,
                            "protocol_version": "EPI_R20", "reason": "NO_GROUND_TRUTH"}
        cert = produce(profile=profile, attr=attr)
        self.assertEqual(cert["unknown_channels"], ["a_epi"])
        self.assertEqual(cert["evidence_ceiling"], "LIMITED")
        self.assertEqual(cert["sensitivity_status"]["order"]["status"], "NOT_EVALUABLE")
        self.assertEqual(cert["state_autonomy_interval"][0], 0.0)

    def test_l0_internal_causal_point_and_zero_flow(self):
        profile = {
            "a_org": {"value": 0.75, "state": "DEFINED", "interval": None,
                      "protocol_version": "L0_R20"},
            "a_exec": {"value": A_EXEC, "state": "DEFINED", "interval": None,
                       "protocol_version": "EXEC_R20", "horizon_actions": 2,
                       "uses_intermediate_observations": False},
        }
        attr = {"attribution_report": {"mode": "L0_INTERNAL_CAUSAL",
                                       "f_int_bits": 0.6, "f_ext_bits": 0.2,
                                       "internal_causal_share": 0.75},
                "weights": [0.5, 0.5], "sigma": 1.0}
        kwargs = dict(layer="L0", viability_state=0.8, defense_readiness=0.7,
                      surgery_history=0, lambda_value=None,
                      lambda_status="NOT_APPLICABLE",
                      source_registration="COMPLETE", mechanism_evidence="NONE",
                      goal_mode="STRUCTURAL_POINT",
                      lambda_time_origin="NOT_APPLICABLE",
                      lambda_counterfactual_scope="NOT_APPLICABLE")
        cert = produce_r20_certificate(channel_profile=profile, attribution=attr,
                                       **kwargs)
        self.assertEqual(cert["composite_scalar_grade"], GRADE_L0)
        self.assertAlmostEqual(cert["state_autonomy"],
                               0.8 * math.sqrt(0.75 * A_EXEC), places=12)
        self.assertEqual(cert["sensitivity_status"]["order"]["status"], "NOT_APPLICABLE")
        # L0 must reject imposed RNI/NRI structure.
        bad = copy.deepcopy(attr)
        bad["registered_partition"] = point_partition()
        with self.assertRaises(ValueError):
            produce_r20_certificate(channel_profile=profile, attribution=bad, **kwargs)
        # L0 zero flow degrades to interval.
        profile0 = copy.deepcopy(profile)
        profile0["a_org"] = {"value": None, "state": "INTERVAL",
                             "interval": [0.0, 1.0], "interval_kind": "LOGICAL_ENVELOPE",
                             "protocol_version": "L0_R20"}
        attr0 = {"attribution_report": {"mode": "L0_INTERNAL_CAUSAL",
                                        "f_int_bits": 0.0, "f_ext_bits": 0.0,
                                        "internal_causal_share": None},
                 "weights": [0.5, 0.5], "sigma": 1.0}
        cert0 = produce_r20_certificate(channel_profile=profile0, attribution=attr0,
                                        **kwargs)
        self.assertEqual(cert0["certificate_mode"], "INTERVAL")
        self.assertEqual(cert0["composite_scalar_grade"], GRADE_ZERO_FLOW)

    def test_l1_point_certificate(self):
        profile = {k: v for k, v in l2_profile().items() if k != "a_ref"}
        attr = {"registered_partition": point_partition(),
                "alternative_partitions": {"R_as_normative_memory": alternative_point()},
                "weights": [0.25] * 4, "sigma": 1.0}
        cert = produce_r20_certificate(
            layer="L1", channel_profile=profile, attribution=attr,
            viability_state=0.8, defense_readiness=0.7, surgery_history=0,
            lambda_value=None, lambda_status="NOT_APPLICABLE",
            source_registration="COMPLETE", mechanism_evidence="NONE",
            goal_mode="STRUCTURAL_POINT", lambda_time_origin="NOT_APPLICABLE",
            lambda_counterfactual_scope="NOT_APPLICABLE",
            model_hash="a" * 64, evidence_hash="b" * 64)
        self.assertEqual(validate_r20_certificate(cert), [])
        self.assertEqual(set(cert["channel_profile"]),
                         {"a_org", "a_goal", "a_exec", "a_epi"})

    def test_irl_interval_mode(self):
        profile, attr = interval_fixture()
        profile["a_goal"] = {"value": None, "state": "INTERVAL",
                             "interval": [0.5, 1.0], "interval_kind": "MODEL_SELECTION",
                             "protocol_version": "GOAL_IRL_R20",
                             "structural_point": None, "irl_interval": [0.5, 1.0],
                             "irl_interval_kind": "MODEL_SELECTION"}
        cert = produce(profile=profile, attr=attr, goal_mode="IRL_INTERVAL")
        self.assertEqual(cert["certificate_mode"], "INTERVAL")
        self.assertIsNone(cert["state_autonomy"])
        forced = copy.deepcopy(profile)
        forced["a_goal"]["structural_point"] = 0.5
        with self.assertRaises(ValueError):
            produce(profile=forced, attr=attr, goal_mode="IRL_INTERVAL")

    def test_thin_log_and_zero_entropy_reflection_intervals(self):
        profile, attr = interval_fixture()
        profile["a_ref"] = {"value": None, "state": "INTERVAL",
                            "interval": [0.0, A_REF], "interval_kind": "LOGICAL_ENVELOPE",
                            "protocol_version": "REF_R20",
                            "degradation_reason": "THIN_LOG", "fidelity": A_REF,
                            "endorsement_consistency": None, "Lambda": 1.0,
                            "event_counts": {"normative_update_events": 3,
                                             "endorsement_events": 3,
                                             "surgery_contexts": 8192}}
        cert = produce(profile=profile, attr=attr)
        self.assertEqual(cert["evidence_ceiling"], "LIMITED")
        self.assertEqual(cert["degradation_reasons"], ["THIN_LOG"])
        self.assertEqual(cert["state_autonomy_interval"][0], 0.0)
        profile2, attr2 = interval_fixture()
        profile2["a_ref"] = {"value": None, "state": "INTERVAL",
                             "interval": [0.0, 1.0], "interval_kind": "LOGICAL_ENVELOPE",
                             "protocol_version": "REF_R20",
                             "degradation_reason": "ZERO_ENTROPY_ENSEMBLE",
                             "fidelity": None, "endorsement_consistency": 1.0,
                             "Lambda": 1.0,
                             "event_counts": {"normative_update_events": 24576,
                                              "endorsement_events": 24576,
                                              "surgery_contexts": 8192}}
        cert2 = produce(profile=profile2, attr=attr2)
        expected_upper = 0.8 * (1.0 * 0.5 * A_EXEC * 0.9 * 1.0) ** 0.2
        self.assertAlmostEqual(cert2["state_autonomy_interval"][1],
                               expected_upper, places=9)


class IntervalKindsAndFailClosed(unittest.TestCase):
    def test_interval_kind_vocabulary_enforced(self):
        profile, attr = interval_fixture()
        profile["a_org"]["interval_kind"] = "CONFIDENCE_95"
        with self.assertRaises(ValueError):
            produce(profile=profile, attr=attr)
        profile2, attr2 = interval_fixture()
        del profile2["a_org"]["interval_kind"]
        with self.assertRaises(ValueError):
            produce(profile=profile2, attr=attr2)
        self.assertIn("LOGICAL_ENVELOPE", INTERVAL_KINDS)
        self.assertIn("SAMPLING_BASIC_BOOTSTRAP", INTERVAL_KINDS)
        self.assertIn("MODEL_SELECTION", INTERVAL_KINDS)

    def test_degraded_reflection_kind_must_be_logical_envelope(self):
        profile, attr = interval_fixture()
        profile["a_ref"] = {"value": None, "state": "INTERVAL",
                            "interval": [0.0, A_REF],
                            "interval_kind": "SAMPLING_PERCENTILE",
                            "protocol_version": "REF_R20",
                            "degradation_reason": "THIN_LOG", "fidelity": A_REF,
                            "endorsement_consistency": None, "Lambda": 1.0,
                            "event_counts": {"normative_update_events": 3,
                                             "endorsement_events": 3,
                                             "surgery_contexts": 8192}}
        with self.assertRaises(ValueError):
            produce(profile=profile, attr=attr)

    def test_suppression_and_forgery_fail_closed(self):
        profile, attr = interval_fixture()
        cert = produce(profile=profile, attr=attr)
        bad = copy.deepcopy(cert)
        bad["sensitivity_flags"] = []
        self.assertTrue(validate_r20_certificate(bad))
        bad2 = copy.deepcopy(cert)
        bad2["attribution_sensitivity"]["convention_reports"]["registered"]["NRI"]["convention_status"] = "DATA_BELOW_LIMIT"
        self.assertTrue(validate_r20_certificate(bad2))
        bad3 = copy.deepcopy(cert)
        bad3["attribution_sensitivity"]["overall_composite_range"] = [0.0, 0.9]
        self.assertTrue(validate_r20_certificate(bad3))
        bad4 = copy.deepcopy(cert)
        bad4["state_autonomy"] = 0.1478374  # diagnostic plugin as point export
        self.assertTrue(validate_r20_certificate(bad4))
        bad5 = copy.deepcopy(cert)
        bad5["detection_policy"]["deployable_decision_uses_exact_truth"] = True
        self.assertTrue(validate_r20_certificate(bad5))
        bad6 = copy.deepcopy(cert)
        bad6["sensitivity_status"]["order"]["status"] = "NO_CONFIRMED_SENSITIVITY"
        self.assertTrue(validate_r20_certificate(bad6))
        bad7 = copy.deepcopy(cert)
        del bad7["attribution_sensitivity"]["convention_reports"]["registered"]["NRI"]["detection_limit"]
        self.assertTrue(validate_r20_certificate(bad7))

    def test_r19_certificate_not_valid_under_r20(self):
        # Build the R19 point certificate (compatibility layer) and check the
        # R20 validator rejects the older schema version.
        r19_profile = {
            "a_org": {"value": 1.0, "state": "DEFINED", "interval": None,
                      "protocol_version": "RNI_R19"},
            "a_goal": {"value": 0.5, "state": "DEFINED", "interval": None,
                       "protocol_version": "GOAL_R19", "structural_point": 0.5,
                       "irl_interval": [0.5, 1.0]},
            "a_exec": {"value": A_EXEC, "state": "DEFINED", "interval": None,
                       "protocol_version": "EXEC_R19", "horizon_actions": 2,
                       "uses_intermediate_observations": False},
            "a_epi": {"value": 0.9, "state": "DEFINED", "interval": None,
                      "protocol_version": "EPI_R19"},
            "a_ref": {"value": A_REF, "state": "DEFINED", "interval": None,
                      "protocol_version": "REF_R19", "fidelity": A_REF,
                      "endorsement_consistency": 1.0, "Lambda": 1.0,
                      "event_counts": {"normative_update_events": 24576,
                                       "endorsement_events": 24576,
                                       "surgery_contexts": 8192}},
        }
        r19_attr = {"registered_partition": point_partition(),
                    "alternative_partitions": {"R_as_normative_memory": alternative_point()},
                    "weights": list(W5), "sigma": 1.0}
        r19_cert = produce_r19_certificate(
            layer="L2", channel_profile=r19_profile, attribution=r19_attr,
            viability_state=0.8, defense_readiness=0.7, surgery_history=0,
            lambda_value=1.0, lambda_status="DEFINED",
            source_registration="COMPLETE", mechanism_evidence="NONE",
            goal_mode="STRUCTURAL_POINT",
            lambda_time_origin="AUDIT_CURRENT_REMOVAL",
            lambda_counterfactual_scope="REMOVE_REGISTERED_SURGERIES_AT_AUDIT",
            model_hash="a" * 64, evidence_hash="b" * 64)
        self.assertTrue(validate_r20_certificate(r19_cert))

    def test_writer_enforces_contract(self):
        import tempfile
        profile, attr = interval_fixture()
        cert = produce(profile=profile, attr=attr)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as handle:
            path = handle.name
        try:
            write_r20_certificate(path, cert)
            broken = copy.deepcopy(cert)
            broken["sensitivity_flags"] = []
            with self.assertRaises(ValueError):
                write_r20_certificate(path, broken)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()