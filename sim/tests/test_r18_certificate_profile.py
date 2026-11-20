"""R18 full-profile certificate guards.

Core regression: when the registered RNI share is near one and the NRI share
near zero, the certificate MUST carry the full channel profile, the
convention composites, enforced sensitivity flags, and a scalar-export
warning.  A single positive scalar without those fields fails closed.
"""
import copy
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim.r18_guards import (  # noqa: E402
    GRADE_POINT, GRADE_SENSITIVE, GRADE_UNDEFINED,
    MODEL_SENSITIVITY_THRESHOLD, ORDER_SENSITIVITY_THRESHOLD,
    R18_CHANNEL_SCHEMA_VERSION, make_r18_audit_certificate,
    produce_r18_certificate, validate_r18_certificate, write_r18_certificate,
)

A_EXEC = 0.26550220320535944
A_REF = 0.5310044064107189
TOTAL_DI = 0.7305954885971118
WEIGHTS = [0.2] * 5


def _registered_partition(rni=1.0, nri=4.3846787364730815e-16, avg=0.5):
    f_rand = nri * TOTAL_DI
    f_norm = rni * TOTAL_DI
    return {
        "flows_bits_RNI": [f_rand, f_norm, 0.0],
        "flows_bits_NRI": [f_rand, f_norm, 0.0],
        "joint_di_bits": TOTAL_DI,
        "normative_share_RNI": rni,
        "normative_share_NRI": nri,
        "normative_share_order_average": avg,
    }


def _alternative_partition():
    return {
        "flows_bits_RNI": [0.0, TOTAL_DI, 1.281370601525967e-15],
        "flows_bits_NRI": [TOTAL_DI, 0.0, 1.281370601525967e-15],
        "joint_di_bits": TOTAL_DI,
        "normative_share_RNI": 1.0,
        "normative_share_NRI": 1.0,
        "normative_share_order_average": 1.0,
    }


def _profile(a_org=1.0, a_ref=A_REF, lambda_value=1.0, consistency=1.0,
             event_counts=None):
    if event_counts is None:
        event_counts = {"normative_update_events": 3072,
                        "endorsement_events": 3072,
                        "surgery_contexts": 1024}
    return {
        "a_org": {"value": a_org, "state": "DEFINED", "interval": None,
                  "protocol_version": "RNI_ORDERED_RESIDUAL_SHARE_R18"},
        "a_goal": {"value": 0.5, "state": "DEFINED", "interval": None,
                   "protocol_version": "STRUCTURAL_POINT_AND_IRL_INTERVAL_R18",
                   "structural_point": 0.5, "irl_interval": [0.5, 1.0]},
        "a_exec": {"value": A_EXEC, "state": "DEFINED", "interval": None,
                   "protocol_version": "PRECOMMITTED_OPEN_LOOP_SEQUENCE_R18",
                   "horizon_actions": 2, "uses_intermediate_observations": False},
        "a_epi": {"value": 0.9, "state": "DEFINED", "interval": [0.88, 0.92],
                  "protocol_version": "LOGGED_BELIEF_ACCURACY_R18"},
        "a_ref": {"value": a_ref, "state": "DEFINED", "interval": None,
                  "protocol_version": "FIDELITY_CONSISTENCY_LAMBDA_R18",
                  "fidelity": A_REF, "endorsement_consistency": consistency,
                  "Lambda": lambda_value, "event_counts": dict(event_counts)},
    }


def _sensitivity(registered=None, alternatives=None, weights=None):
    return {
        "registered_partition": registered if registered is not None else _registered_partition(),
        "alternative_partitions": (alternatives if alternatives is not None
                                   else {"R_as_normative_memory": _alternative_partition()}),
        "weights": weights if weights is not None else list(WEIGHTS),
        "sigma": 1.0,
    }


def _produce(profile=None, sensitivity=None, channels=None, surgery=0,
             lambda_value=1.0):
    if channels is None:
        channels = (1.0, 0.5, A_EXEC, 0.9, A_REF)
    return produce_r18_certificate(
        layer="L2", channels=channels, weights=WEIGHTS,
        resource_ratios=[0.8], defense_margins=[0.7],
        surgery_history=surgery, lambda_value=lambda_value,
        lambda_status="DEFINED", source_registration="COMPLETE",
        mechanism_evidence="NONE", org_mode="L1_NORMATIVE_NR",
        goal_mode="STRUCTURAL_POINT", state_readiness_version="R15_SPLIT",
        model_hash="a" * 64, evidence_hash="b" * 64,
        lambda_time_origin="AUDIT_CURRENT_REMOVAL",
        lambda_counterfactual_scope="REMOVE_REGISTERED_SURGERIES_AT_AUDIT",
        channel_profile=profile if profile is not None else _profile(),
        attribution_sensitivity=(sensitivity if sensitivity is not None
                                 else _sensitivity()))


class R18CertificateProfile(unittest.TestCase):
    def test_full_profile_certificate_carries_every_required_field(self):
        cert = _produce()
        self.assertEqual(cert["channel_schema_version"], R18_CHANNEL_SCHEMA_VERSION)
        self.assertEqual(validate_r18_certificate(cert), [])
        self.assertEqual(set(cert["channel_profile"]),
                         {"a_org", "a_goal", "a_exec", "a_epi", "a_ref"})
        for entry in cert["channel_profile"].values():
            self.assertEqual(entry["state"], "DEFINED")
            self.assertTrue(entry["protocol_version"])
        self.assertEqual(cert["channel_profile"]["a_exec"]["horizon_actions"], 2)
        self.assertEqual(cert["channel_profile"]["a_goal"]["irl_interval"], [0.5, 1.0])
        self.assertEqual(cert["channel_profile"]["a_ref"]["event_counts"]["surgery_contexts"], 1024)
        sensitivity = cert["attribution_sensitivity"]
        for convention in ("RNI", "NRI", "order_average"):
            self.assertIn(convention, sensitivity["composite_by_convention"]["registered"])
        self.assertIn("R_as_normative_memory", sensitivity["composite_by_convention"])
        self.assertEqual(cert["current_structural_profile"]["full_channel_profile_field"],
                         "channel_profile")

    def test_rni_near_one_nri_near_zero_forces_flags_and_warning(self):
        # THE core R18 regression: no unflagged single positive scalar.
        cert = _produce()
        self.assertEqual(cert["sensitivity_flags"], ["ORDER_SENSITIVE", "MODEL_SENSITIVE"])
        self.assertEqual(cert["composite_scalar_grade"], GRADE_SENSITIVE)
        self.assertTrue(cert["scalar_export_warning"].strip())
        composites = cert["attribution_sensitivity"]["composite_by_convention"]["registered"]
        self.assertAlmostEqual(composites["RNI"], 0.4608565248033332, places=9)
        self.assertAlmostEqual(composites["NRI"], 0.0003907988672884718, places=9)
        self.assertAlmostEqual(composites["order_average"], 0.4011989072662361, places=9)
        self.assertAlmostEqual(cert["state_autonomy"], composites["RNI"], places=12)
        span = cert["attribution_sensitivity"]["composite_range"]
        self.assertAlmostEqual(span[0], composites["NRI"], places=12)
        self.assertAlmostEqual(span[1], composites["RNI"], places=12)
        self.assertGreater(cert["attribution_sensitivity"]["order_spread"],
                           ORDER_SENSITIVITY_THRESHOLD)
        self.assertGreater(cert["attribution_sensitivity"]["model_spread"],
                           MODEL_SENSITIVITY_THRESHOLD)

    def test_stripping_sensitivity_fields_fails_closed(self):
        cert = _produce()
        for field in ("channel_profile", "attribution_sensitivity", "sensitivity_flags",
                      "composite_scalar_grade", "scalar_export_warning"):
            stripped = copy.deepcopy(cert)
            del stripped[field]
            self.assertTrue(validate_r18_certificate(stripped), field)
        unflagged = copy.deepcopy(cert)
        unflagged["sensitivity_flags"] = []
        self.assertTrue(validate_r18_certificate(unflagged))
        unflagged_current = copy.deepcopy(cert)
        unflagged_current["current_structural_profile"]["sensitivity_flags"] = []
        self.assertTrue(validate_r18_certificate(unflagged_current))
        silent = copy.deepcopy(cert)
        silent["scalar_export_warning"] = ""
        self.assertTrue(validate_r18_certificate(silent))
        downgraded = copy.deepcopy(cert)
        downgraded["composite_scalar_grade"] = GRADE_POINT
        self.assertTrue(validate_r18_certificate(downgraded))

    def test_r17_style_scalar_only_profile_is_not_an_r18_certificate(self):
        cert = _produce()
        legacy = copy.deepcopy(cert)
        legacy["channel_schema_version"] = "R17_CHANNEL_SCHEMA_V1"
        for field in ("channel_profile", "attribution_sensitivity", "sensitivity_flags",
                      "composite_scalar_grade", "scalar_export_warning"):
            legacy.pop(field, None)
        self.assertTrue(validate_r18_certificate(legacy))

    def test_composite_and_weight_drift_fail_closed(self):
        cert = _produce()
        drifted = copy.deepcopy(cert)
        drifted["attribution_sensitivity"]["composite_by_convention"]["registered"]["NRI"] = 0.2
        self.assertTrue(validate_r18_certificate(drifted))
        range_drift = copy.deepcopy(cert)
        range_drift["attribution_sensitivity"]["composite_range"] = [0.1, 0.9]
        self.assertTrue(validate_r18_certificate(range_drift))
        scalar_drift = copy.deepcopy(cert)
        scalar_drift["state_autonomy"] = 0.9
        self.assertTrue(validate_r18_certificate(scalar_drift))
        with self.assertRaises(ValueError):
            _produce(sensitivity=_sensitivity(weights=[0.0, 0.25, 0.25, 0.25, 0.25]))
        with self.assertRaises(ValueError):
            _produce(sensitivity=_sensitivity(weights=[0.3] * 5))

    def test_channel_factor_and_event_count_guards(self):
        with self.assertRaises(ValueError):
            _produce(profile=_profile(a_ref=0.9))  # product mismatch
        with self.assertRaises(ValueError):
            _produce(profile=_profile(consistency=0.5))  # event ratio mismatch
        with self.assertRaises(ValueError):
            _produce(profile=_profile(event_counts={
                "normative_update_events": 10, "endorsement_events": 11,
                "surgery_contexts": 10}))
        with self.assertRaises(ValueError):
            _produce(profile=_profile(event_counts={
                "normative_update_events": 0, "endorsement_events": 0,
                "surgery_contexts": 0}))
        bad_exec = _profile()
        bad_exec["a_exec"]["uses_intermediate_observations"] = True
        with self.assertRaises(ValueError):
            _produce(profile=bad_exec)
        bad_interval = _profile()
        bad_interval["a_epi"]["interval"] = [0.95, 0.9]
        with self.assertRaises(ValueError):
            _produce(profile=bad_interval)
        nan_profile = _profile()
        nan_profile["a_org"]["value"] = float("nan")
        with self.assertRaises(ValueError):
            _produce(profile=nan_profile)

    def test_zero_reflection_annihilates_all_conventions_without_flags(self):
        profile = _profile(a_ref=0.0, lambda_value=0.0)
        cert = _produce(profile=profile, channels=(1.0, 0.5, A_EXEC, 0.9, 0.0),
                        surgery=1, lambda_value=0.0)
        self.assertEqual(validate_r18_certificate(cert), [])
        self.assertEqual(cert["state_autonomy"], 0.0)
        self.assertEqual(cert["sensitivity_flags"], [])
        self.assertEqual(cert["composite_scalar_grade"], GRADE_POINT)
        for partition in cert["attribution_sensitivity"]["composite_by_convention"].values():
            for value in partition.values():
                self.assertEqual(value, 0.0)
        self.assertEqual(cert["historical_formation_profile"]["formation_status"],
                         "REGISTERED_SURGERY")

    def test_zero_total_flow_is_undefined_not_a_silent_positive(self):
        zero_partition = {
            "flows_bits_RNI": [0.0, 0.0, 0.0],
            "flows_bits_NRI": [0.0, 0.0, 0.0],
            "joint_di_bits": 0.0,
            "normative_share_RNI": None,
            "normative_share_NRI": None,
            "normative_share_order_average": None,
        }
        profile = _profile(a_org=0.0)
        cert = _produce(profile=profile,
                        sensitivity=_sensitivity(registered=zero_partition, alternatives={}),
                        channels=(0.0, 0.5, A_EXEC, 0.9, A_REF))
        self.assertEqual(validate_r18_certificate(cert), [])
        self.assertEqual(cert["composite_scalar_grade"], GRADE_UNDEFINED)
        self.assertIsNone(cert["attribution_sensitivity"]["composite_range"])
        self.assertEqual(cert["state_autonomy"], 0.0)
        positive = copy.deepcopy(cert)
        positive["state_autonomy"] = 0.4
        self.assertTrue(validate_r18_certificate(positive))

    def test_flow_share_consistency_is_checked(self):
        bad = _registered_partition()
        bad["normative_share_RNI"] = 0.5  # disagrees with its flow term
        with self.assertRaises(ValueError):
            _produce(sensitivity=_sensitivity(registered=bad))
        bad_avg = _registered_partition()
        bad_avg["normative_share_order_average"] = 0.9
        with self.assertRaises(ValueError):
            _produce(sensitivity=_sensitivity(registered=bad_avg))

    def test_writer_enforces_the_same_contract(self):
        import tempfile
        cert = _produce()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as handle:
            path = handle.name
        try:
            write_r18_certificate(path, cert)
            broken = copy.deepcopy(cert)
            broken["sensitivity_flags"] = []
            with self.assertRaises(ValueError):
                write_r18_certificate(path, broken)
        finally:
            os.unlink(path)

    def test_upgrade_requires_valid_r17_base(self):
        cert = _produce()
        r17 = copy.deepcopy(cert)
        r17["channel_schema_version"] = "R17_CHANNEL_SCHEMA_V1"
        for field in ("channel_profile", "attribution_sensitivity", "sensitivity_flags",
                      "composite_scalar_grade", "scalar_export_warning"):
            r17.pop(field, None)
        current = r17["current_structural_profile"]
        for field in ("composite_range_across_conventions", "sensitivity_flags",
                      "composite_scalar_grade", "full_channel_profile_field"):
            current.pop(field, None)
        upgraded = make_r18_audit_certificate(
            r17_certificate=r17, channel_profile=_profile(),
            attribution_sensitivity=_sensitivity())
        self.assertEqual(validate_r18_certificate(upgraded), [])
        r17["lambda_time_origin"] = "ORIGINAL_IMPLANT_PREVENTION"
        with self.assertRaises(ValueError):
            make_r18_audit_certificate(r17_certificate=r17, channel_profile=_profile(),
                                       attribution_sensitivity=_sensitivity())


if __name__ == "__main__":
    unittest.main()