"""R19 layer-aware certificate schema: L0/L1/L2, four channel states,
point/interval modes, decomposed sensitivity, and fail-closed governance."""
import copy
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim.r19_guards import (  # noqa: E402
    GRADE_INTERVAL, GRADE_L0, GRADE_POINT, GRADE_SENSITIVE, GRADE_ZERO_FLOW,
    ORDER_SENSITIVITY_THRESHOLD, SEMANTIC_SENSITIVITY_THRESHOLD,
    THRESHOLD_PROVENANCE, produce_r19_certificate, validate_r19_certificate,
    write_r19_certificate,
)

A_EXEC = 0.26550220320535944
A_REF = 0.5310044064107189
TOTAL_DI = 0.7305954885971118
W5 = [0.2] * 5


def partition(rni=1.0, nri=4.3846787364730815e-16, avg=0.5):
    return {"flows_bits_RNI": [nri * TOTAL_DI, rni * TOTAL_DI, 0.0],
            "flows_bits_NRI": [nri * TOTAL_DI, rni * TOTAL_DI, 0.0],
            "joint_di_bits": TOTAL_DI,
            "normative_share_RNI": rni, "normative_share_NRI": nri,
            "normative_share_order_average": avg}


def alternative():
    return {"flows_bits_RNI": [0.0, TOTAL_DI, 1.281370601525967e-15],
            "flows_bits_NRI": [TOTAL_DI, 0.0, 1.281370601525967e-15],
            "joint_di_bits": TOTAL_DI,
            "normative_share_RNI": 1.0, "normative_share_NRI": 1.0,
            "normative_share_order_average": 1.0}


def with_intervals(report):
    report = copy.deepcopy(report)
    total = float(report["joint_di_bits"])
    report["share_intervals"] = {
        convention: (None if total <= 1e-9 else [report[key], report[key]])
        for convention, key in (("RNI", "normative_share_RNI"),
                                ("NRI", "normative_share_NRI"),
                                ("order_average", "normative_share_order_average"))}
    return report


def l2_profile(a_org=1.0):
    return {
        "a_org": {"value": a_org, "state": "DEFINED", "interval": None,
                  "protocol_version": "RNI_ORDERED_RESIDUAL_SHARE_R19"},
        "a_goal": {"value": 0.5, "state": "DEFINED", "interval": None,
                   "protocol_version": "STRUCTURAL_POINT_AND_IRL_INTERVAL_R19",
                   "structural_point": 0.5, "irl_interval": [0.5, 1.0]},
        "a_exec": {"value": A_EXEC, "state": "DEFINED", "interval": None,
                   "protocol_version": "PRECOMMITTED_OPEN_LOOP_CANONICAL_R19",
                   "horizon_actions": 2, "uses_intermediate_observations": False},
        "a_epi": {"value": 0.9, "state": "DEFINED", "interval": [0.88, 0.92],
                  "protocol_version": "LOGGED_BELIEF_ACCURACY_R19"},
        "a_ref": {"value": A_REF, "state": "DEFINED", "interval": None,
                  "protocol_version": "FIDELITY_CONSISTENCY_LAMBDA_R19",
                  "fidelity": A_REF, "endorsement_consistency": 1.0, "Lambda": 1.0,
                  "event_counts": {"normative_update_events": 24576,
                                   "endorsement_events": 24576,
                                   "surgery_contexts": 8192}},
    }


def attribution(reg=None, alts=None, *, interval_mode=False):
    reg = reg if reg is not None else partition()
    alts = alts if alts is not None else {"R_as_normative_memory": alternative()}
    if interval_mode:
        reg = with_intervals(reg)
        alts = {name: with_intervals(report) for name, report in alts.items()}
    return {"registered_partition": reg, "alternative_partitions": alts,
            "weights": list(W5), "sigma": 1.0}


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
    return produce_r19_certificate(
        channel_profile=profile if profile is not None else l2_profile(),
        attribution=attr if attr is not None else attribution(), **kwargs)


class R19LayerAwareCertificates(unittest.TestCase):
    def test_l2_point_reproduces_registered_convention_composites(self):
        cert = produce()
        self.assertEqual(cert["certificate_mode"], "POINT")
        self.assertEqual(validate_r19_certificate(cert), [])
        composites = cert["attribution_sensitivity"]["composite_by_convention"]["registered"]
        self.assertAlmostEqual(composites["RNI"], 0.4608565248033332, places=9)
        self.assertAlmostEqual(composites["NRI"], 0.0003907988672884718, places=9)
        self.assertAlmostEqual(composites["order_average"], 0.4011989072662361, places=9)
        self.assertAlmostEqual(cert["state_autonomy"], composites["RNI"], places=12)
        self.assertEqual(cert["sensitivity_flags"], ["ORDER_SENSITIVE", "MODEL_SENSITIVE"])
        self.assertEqual(cert["composite_scalar_grade"], GRADE_SENSITIVE)
        self.assertEqual(cert["threshold_provenance"], THRESHOLD_PROVENANCE)
        self.assertIn("POST_HOC_FROZEN", cert["threshold_provenance"])

    def test_l0_uses_internal_causal_report_not_rni_nri(self):
        profile = {
            "a_org": {"value": 0.75, "state": "DEFINED", "interval": None,
                      "protocol_version": "L0_INTERNAL_CAUSAL_R19"},
            "a_exec": {"value": A_EXEC, "state": "DEFINED", "interval": None,
                       "protocol_version": "PRECOMMITTED_OPEN_LOOP_CANONICAL_R19",
                       "horizon_actions": 2, "uses_intermediate_observations": False},
        }
        attr = {"attribution_report": {"mode": "L0_INTERNAL_CAUSAL",
                                       "f_int_bits": 0.6, "f_ext_bits": 0.2,
                                       "internal_causal_share": 0.75},
                "weights": [0.5, 0.5], "sigma": 1.0}
        cert = produce_r19_certificate(
            layer="L0", channel_profile=profile, attribution=attr,
            viability_state=0.8, defense_readiness=0.7, surgery_history=0,
            lambda_value=None, lambda_status="NOT_APPLICABLE",
            source_registration="COMPLETE", mechanism_evidence="NONE",
            goal_mode="STRUCTURAL_POINT", lambda_time_origin="NOT_APPLICABLE",
            lambda_counterfactual_scope="NOT_APPLICABLE")
        self.assertEqual(validate_r19_certificate(cert), [])
        self.assertEqual(cert["composite_scalar_grade"], GRADE_L0)
        self.assertEqual(cert["sensitivity_flags"], [])
        self.assertAlmostEqual(cert["state_autonomy"],
                               0.8 * math.sqrt(0.75 * A_EXEC), places=12)
        self.assertEqual(cert["attribution_report"]["mode"], "L0_INTERNAL_CAUSAL")
        self.assertNotIn("normative_share_RNI", cert["attribution_report"])
        # L0 must reject an imposed L1-style RNI/NRI structure.
        bad = copy.deepcopy(attr)
        bad["registered_partition"] = partition()
        with self.assertRaises(ValueError):
            produce_r19_certificate(
                layer="L0", channel_profile=profile, attribution=bad,
                viability_state=0.8, defense_readiness=0.7, surgery_history=0,
                lambda_value=None, lambda_status="NOT_APPLICABLE",
                source_registration="COMPLETE", mechanism_evidence="NONE",
                goal_mode="STRUCTURAL_POINT", lambda_time_origin="NOT_APPLICABLE",
                lambda_counterfactual_scope="NOT_APPLICABLE")
        # L0 share must equal f_int/(f_int+f_ext).
        bad2 = copy.deepcopy(attr)
        bad2["attribution_report"]["internal_causal_share"] = 0.5
        with self.assertRaises(ValueError):
            produce_r19_certificate(
                layer="L0", channel_profile=profile, attribution=bad2,
                viability_state=0.8, defense_readiness=0.7, surgery_history=0,
                lambda_value=None, lambda_status="NOT_APPLICABLE",
                source_registration="COMPLETE", mechanism_evidence="NONE",
                goal_mode="STRUCTURAL_POINT", lambda_time_origin="NOT_APPLICABLE",
                lambda_counterfactual_scope="NOT_APPLICABLE")

    def test_l1_point_certificate(self):
        profile = {k: v for k, v in l2_profile().items() if k != "a_ref"}
        attr = attribution()
        attr["weights"] = [0.25] * 4
        cert = produce_r19_certificate(
            layer="L1", channel_profile=profile, attribution=attr,
            viability_state=0.8, defense_readiness=0.7, surgery_history=0,
            lambda_value=None, lambda_status="NOT_APPLICABLE",
            source_registration="COMPLETE", mechanism_evidence="NONE",
            goal_mode="STRUCTURAL_POINT", lambda_time_origin="NOT_APPLICABLE",
            lambda_counterfactual_scope="NOT_APPLICABLE",
            model_hash="a" * 64, evidence_hash="b" * 64)
        self.assertEqual(validate_r19_certificate(cert), [])
        self.assertEqual(cert["certificate_mode"], "POINT")
        self.assertEqual(set(cert["channel_profile"]),
                         {"a_org", "a_goal", "a_exec", "a_epi"})
        self.assertEqual(cert["sensitivity_flags"], ["ORDER_SENSITIVE", "MODEL_SENSITIVE"])

    def test_l0_zero_total_flow_degrades_to_interval(self):
        profile = {
            "a_org": {"value": None, "state": "INTERVAL", "interval": [0.0, 1.0],
                      "protocol_version": "L0_INTERNAL_CAUSAL_R19"},
            "a_exec": {"value": A_EXEC, "state": "DEFINED", "interval": None,
                       "protocol_version": "PRECOMMITTED_OPEN_LOOP_CANONICAL_R19",
                       "horizon_actions": 2, "uses_intermediate_observations": False},
        }
        attr = {"attribution_report": {"mode": "L0_INTERNAL_CAUSAL",
                                       "f_int_bits": 0.0, "f_ext_bits": 0.0,
                                       "internal_causal_share": None},
                "weights": [0.5, 0.5], "sigma": 1.0}
        cert = produce_r19_certificate(
            layer="L0", channel_profile=profile, attribution=attr,
            viability_state=0.8, defense_readiness=0.7, surgery_history=0,
            lambda_value=None, lambda_status="NOT_APPLICABLE",
            source_registration="COMPLETE", mechanism_evidence="NONE",
            goal_mode="STRUCTURAL_POINT", lambda_time_origin="NOT_APPLICABLE",
            lambda_counterfactual_scope="NOT_APPLICABLE")
        self.assertEqual(cert["certificate_mode"], "INTERVAL")
        self.assertIsNone(cert["state_autonomy"])
        self.assertEqual(cert["composite_scalar_grade"], GRADE_ZERO_FLOW)
        self.assertAlmostEqual(cert["state_autonomy_interval"][1],
                               0.8 * math.sqrt(A_EXEC), places=12)


class R19DegradedStates(unittest.TestCase):
    def test_irl_interval_mode_forbids_forced_structural_point(self):
        profile = l2_profile()
        profile["a_goal"] = {"value": None, "state": "INTERVAL",
                             "interval": [0.5, 1.0],
                             "protocol_version": "GOAL_IRL_R19",
                             "structural_point": None, "irl_interval": [0.5, 1.0]}
        cert = produce(profile=profile, attr=attribution(interval_mode=True),
                       goal_mode="IRL_INTERVAL")
        self.assertEqual(cert["certificate_mode"], "INTERVAL")
        self.assertIsNone(cert["state_autonomy"])
        self.assertEqual(cert["state_autonomy_interval"][0], 0.0003907988672884718)
        self.assertTrue(cert["scalar_export_warning"].strip())
        # Forcing a structural point in IRL mode fails closed.
        forced = copy.deepcopy(profile)
        forced["a_goal"]["structural_point"] = 0.5
        with self.assertRaises(ValueError):
            produce(profile=forced, attr=attribution(interval_mode=True),
                    goal_mode="IRL_INTERVAL")

    def test_thin_log_reflection_interval_and_ceiling(self):
        profile = l2_profile()
        profile["a_ref"] = {"value": None, "state": "INTERVAL",
                            "interval": [0.0, A_REF],
                            "protocol_version": "REF_R19",
                            "degradation_reason": "THIN_LOG",
                            "fidelity": A_REF, "endorsement_consistency": None,
                            "Lambda": 1.0,
                            "event_counts": {"normative_update_events": 3,
                                             "endorsement_events": 3,
                                             "surgery_contexts": 8192}}
        cert = produce(profile=profile, attr=attribution(interval_mode=True))
        self.assertEqual(cert["certificate_mode"], "INTERVAL")
        self.assertEqual(cert["evidence_ceiling"], "LIMITED")
        self.assertEqual(cert["degradation_reasons"], ["THIN_LOG"])
        self.assertAlmostEqual(cert["state_autonomy_interval"][1],
                               0.4608565248033332, places=9)
        self.assertEqual(cert["state_autonomy_interval"][0], 0.0)
        # A numeric consistency without logged events fails closed.
        bad = copy.deepcopy(profile)
        bad["a_ref"]["endorsement_consistency"] = 1.0
        bad["a_ref"]["interval"] = [0.0, A_REF]
        with self.assertRaises(ValueError):
            produce(profile=bad, attr=attribution(interval_mode=True))

    def test_zero_entropy_ensemble_interval(self):
        profile = l2_profile()
        profile["a_ref"] = {"value": None, "state": "INTERVAL",
                            "interval": [0.0, 1.0],
                            "protocol_version": "REF_R19",
                            "degradation_reason": "ZERO_ENTROPY_ENSEMBLE",
                            "fidelity": None, "endorsement_consistency": 1.0,
                            "Lambda": 1.0,
                            "event_counts": {"normative_update_events": 24576,
                                             "endorsement_events": 24576,
                                             "surgery_contexts": 8192}}
        cert = produce(profile=profile, attr=attribution(interval_mode=True))
        expected_upper = 0.8 * (1.0 * 0.5 * A_EXEC * 0.9 * 1.0) ** 0.2
        self.assertAlmostEqual(cert["state_autonomy_interval"][1], expected_upper, places=9)
        self.assertEqual(cert["degradation_reasons"], ["ZERO_ENTROPY_ENSEMBLE"])
        # Wrong interval upper bound fails closed.
        bad = copy.deepcopy(profile)
        bad["a_ref"]["interval"] = [0.0, 0.5]
        with self.assertRaises(ValueError):
            produce(profile=bad, attr=attribution(interval_mode=True))

    def test_zero_total_flow_share_unidentifiable_interval(self):
        zero = {"flows_bits_RNI": [0.0, 0.0, 0.0], "flows_bits_NRI": [0.0, 0.0, 0.0],
                "joint_di_bits": 0.0,
                "normative_share_RNI": None, "normative_share_NRI": None,
                "normative_share_order_average": None,
                "share_intervals": {"RNI": None, "NRI": None, "order_average": None}}
        profile = l2_profile()
        profile["a_org"] = {"value": None, "state": "INTERVAL", "interval": [0.0, 1.0],
                            "protocol_version": "RNI_R19"}
        attr = {"registered_partition": zero, "alternative_partitions": {},
                "weights": list(W5), "sigma": 1.0}
        cert = produce(profile=profile, attr=attr)
        self.assertEqual(cert["composite_scalar_grade"], GRADE_ZERO_FLOW)
        self.assertIsNone(cert["state_autonomy"])
        self.assertEqual(cert["sensitivity_flags"], [])  # conventions agree
        upper = 0.8 * (1.0 * 0.5 * A_EXEC * 0.9 * A_REF) ** 0.2
        self.assertAlmostEqual(cert["state_autonomy_interval"][1], upper, places=9)
        # A positive point export on zero flow fails closed.
        broken = copy.deepcopy(cert)
        broken["state_autonomy"] = 0.3
        self.assertTrue(validate_r19_certificate(broken))

    def test_unknown_channel_caps_ceiling_and_propagates_unit_interval(self):
        profile = l2_profile()
        profile["a_epi"] = {"value": None, "state": "UNKNOWN", "interval": None,
                            "protocol_version": "EPI_R19",
                            "reason": "NO_GROUND_TRUTH_ACCESS"}
        cert = produce(profile=profile, attr=attribution(interval_mode=True))
        self.assertEqual(cert["evidence_ceiling"], "LIMITED")
        self.assertEqual(cert["unknown_channels"], ["a_epi"])
        self.assertEqual(cert["state_autonomy_interval"][0], 0.0)
        suppressed = copy.deepcopy(cert)
        suppressed["unknown_channels"] = []
        self.assertTrue(validate_r19_certificate(suppressed))
        upgraded = copy.deepcopy(cert)
        upgraded["evidence_ceiling"] = "REGISTERED_COMPLETE"
        self.assertTrue(validate_r19_certificate(upgraded))

    def test_not_applicable_reflection_rejected_at_l2(self):
        profile = l2_profile()
        profile["a_ref"] = {"value": None, "state": "NOT_APPLICABLE", "interval": None,
                            "protocol_version": "REF_R19", "reason": "NO_ENDORSEMENT_SCM"}
        with self.assertRaises(ValueError):
            produce(profile=profile, attr=attribution(interval_mode=True))


class R19DecomposedSensitivity(unittest.TestCase):
    def test_order_only_sensitivity_when_partitions_agree(self):
        cert = produce(attr=attribution(alts={"same": partition()}))
        self.assertEqual(cert["sensitivity_flags"], ["ORDER_SENSITIVE"])
        sensitivity = cert["attribution_sensitivity"]
        self.assertGreater(sensitivity["order_spread"], ORDER_SENSITIVITY_THRESHOLD)
        self.assertAlmostEqual(sensitivity["semantic_partition_spread"], 0.0, places=12)

    def test_semantic_only_sensitivity_when_orders_agree(self):
        reg = partition(rni=0.5, nri=0.5, avg=0.5)
        cert = produce(profile=l2_profile(a_org=0.5), attr=attribution(reg=reg))
        self.assertEqual(cert["sensitivity_flags"], ["MODEL_SENSITIVE"])
        sensitivity = cert["attribution_sensitivity"]
        self.assertAlmostEqual(sensitivity["order_spread"], 0.0, places=12)
        self.assertGreater(sensitivity["semantic_partition_spread"],
                           SEMANTIC_SENSITIVITY_THRESHOLD)

    def test_native_instance_decomposition_values(self):
        cert = produce()
        sensitivity = cert["attribution_sensitivity"]
        self.assertAlmostEqual(sensitivity["order_spread"], 0.4604657259, places=7)
        self.assertAlmostEqual(sensitivity["semantic_partition_spread"],
                               0.4604657259, places=7)
        composites = sensitivity["composite_by_convention"]
        rni_diff = abs(composites["registered"]["RNI"]
                       - composites["R_as_normative_memory"]["RNI"])
        nri_diff = abs(composites["registered"]["NRI"]
                       - composites["R_as_normative_memory"]["NRI"])
        avg_diff = abs(composites["registered"]["order_average"]
                       - composites["R_as_normative_memory"]["order_average"])
        self.assertAlmostEqual(rni_diff, 0.0, places=9)
        self.assertAlmostEqual(nri_diff, 0.4604657259, places=7)
        self.assertAlmostEqual(avg_diff, 0.0596576175, places=7)
        # Overall range is an overview, not the model-sensitivity definition.
        self.assertEqual(sensitivity["overall_composite_range"],
                         [composites["registered"]["NRI"],
                          composites["registered"]["RNI"]])

    def test_flags_cannot_be_suppressed_and_threshold_provenance_enforced(self):
        cert = produce()
        stripped = copy.deepcopy(cert)
        stripped["sensitivity_flags"] = []
        self.assertTrue(validate_r19_certificate(stripped))
        wrong_provenance = copy.deepcopy(cert)
        wrong_provenance["threshold_provenance"] = "PREREGISTERED_BEFORE_OUTCOMES"
        self.assertTrue(validate_r19_certificate(wrong_provenance))
        silent = copy.deepcopy(cert)
        silent["scalar_export_warning"] = ""
        self.assertTrue(validate_r19_certificate(silent))

    def test_interval_mode_spreads_use_midpoints_not_uncertainty_width(self):
        # Identical convention intervals (zero flow) must not fire flags even
        # though the uncertainty hull is wide.
        zero = {"flows_bits_RNI": [0.0, 0.0, 0.0], "flows_bits_NRI": [0.0, 0.0, 0.0],
                "joint_di_bits": 0.0,
                "normative_share_RNI": None, "normative_share_NRI": None,
                "normative_share_order_average": None,
                "share_intervals": {"RNI": None, "NRI": None, "order_average": None}}
        profile = l2_profile()
        profile["a_org"] = {"value": None, "state": "INTERVAL", "interval": [0.0, 1.0],
                            "protocol_version": "RNI_R19"}
        attr = {"registered_partition": zero, "alternative_partitions": {},
                "weights": list(W5), "sigma": 1.0}
        cert = produce(profile=profile, attr=attr)
        self.assertEqual(cert["sensitivity_flags"], [])
        self.assertGreater(cert["state_autonomy_interval"][1], 0.4)


class R19FailClosed(unittest.TestCase):
    def test_point_mode_rejects_interval_channels(self):
        profile = l2_profile()
        profile["a_epi"] = {"value": None, "state": "INTERVAL", "interval": [0.8, 0.9],
                            "protocol_version": "EPI_R19"}
        with self.assertRaises(ValueError):
            produce(profile=profile)  # POINT inference fails on INTERVAL entry

    def test_reflection_factor_product_and_event_ratio_guards(self):
        profile = l2_profile()
        profile["a_ref"]["value"] = 0.9
        with self.assertRaises(ValueError):
            produce(profile=profile)
        profile2 = l2_profile()
        profile2["a_ref"]["endorsement_consistency"] = 0.5
        with self.assertRaises(ValueError):
            produce(profile=profile2)
        profile3 = l2_profile()
        profile3["a_ref"]["event_counts"] = {"normative_update_events": 0,
                                             "endorsement_events": 0,
                                             "surgery_contexts": 0}
        with self.assertRaises(ValueError):
            produce(profile=profile3)

    def test_weight_and_composite_drift_fail_closed(self):
        cert = produce()
        drifted = copy.deepcopy(cert)
        drifted["attribution_sensitivity"]["composite_by_convention"]["registered"]["NRI"] = 0.2
        self.assertTrue(validate_r19_certificate(drifted))
        range_drift = copy.deepcopy(cert)
        range_drift["attribution_sensitivity"]["overall_composite_range"] = [0.1, 0.9]
        self.assertTrue(validate_r19_certificate(range_drift))
        with self.assertRaises(ValueError):
            produce(attr=attribution() | {"weights": [0.0, 0.25, 0.25, 0.25, 0.25]})

    def test_writer_enforces_contract(self):
        import tempfile
        cert = produce()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as handle:
            path = handle.name
        try:
            write_r19_certificate(path, cert)
            broken = copy.deepcopy(cert)
            broken["sensitivity_flags"] = []
            with self.assertRaises(ValueError):
                write_r19_certificate(path, broken)
        finally:
            os.unlink(path)

    def test_exec_intermediate_observation_mark_required(self):
        profile = l2_profile()
        profile["a_exec"]["uses_intermediate_observations"] = True
        with self.assertRaises(ValueError):
            produce(profile=profile)


if __name__ == "__main__":
    unittest.main()
