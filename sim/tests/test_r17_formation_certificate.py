"""R17 co-primary current/history certificates and fixed-point implant witness."""
import math
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim.formation_audit import fixed_point_replacement_witness, formation_status
from autonomy_sim.r15_guards import R16_CHANNEL_SCHEMA_VERSION, produce_r15_certificate
from autonomy_sim.r17_guards import (R17_CHANNEL_SCHEMA_VERSION, make_r17_audit_certificate,
                                     produce_r17_certificate, validate_r17_certificate,
                                     write_r17_certificate)

MODEL_HASH = "a" * 64
EVIDENCE_HASH = "0123456789abcdef" * 4


def kwargs(layer="L2", **overrides):
    count = {"L0": 2, "L1": 4, "L2": 5}[layer]
    lambda_status = "DEFINED" if layer == "L2" else "NOT_APPLICABLE"
    base = {
        "layer": layer,
        "channels": tuple(0.8 + 0.02 * i for i in range(count)),
        "weights": tuple(1.0 for _ in range(count)),
        "resource_ratios": (1.0, 0.9),
        "defense_margins": (0.7,),
        "surgery_history": 0,
        "lambda_value": 0.8 if lambda_status == "DEFINED" else None,
        "lambda_status": lambda_status,
        "source_registration": "COMPLETE",
        "mechanism_evidence": "NONE",
        "org_mode": "L0_INTERNAL" if layer == "L0" else "L1_NORMATIVE_NR",
        "goal_mode": "STRUCTURAL_POINT",
        "state_readiness_version": "R15_SPLIT",
        "model_hash": MODEL_HASH,
        "evidence_hash": EVIDENCE_HASH,
        "lambda_time_origin": "AUDIT_CURRENT_REMOVAL" if lambda_status == "DEFINED" else "NOT_APPLICABLE",
        "lambda_counterfactual_scope": ("REMOVE_REGISTERED_SURGERIES_AT_AUDIT"
                                        if lambda_status == "DEFINED" else "NOT_APPLICABLE"),
    }
    base.update(overrides)
    return base


class R17FormationCertificate(unittest.TestCase):
    def test_valid_certificate_has_two_co_primary_profiles(self):
        cert = produce_r17_certificate(**kwargs())
        self.assertEqual(validate_r17_certificate(cert), [])
        self.assertEqual(cert["channel_schema_version"], R17_CHANNEL_SCHEMA_VERSION)
        self.assertEqual(cert["current_structural_profile"]["scope"],
                         "PRESENT_STRUCTURAL_AUTONOMY")
        self.assertEqual(cert["historical_formation_profile"]["scope"],
                         "HISTORICAL_FORMATION_AUTONOMY")
        self.assertTrue(cert["historical_formation_profile"]["evidence_only_not_scalar"])
        self.assertFalse(cert["external_construct_validation"])

    def test_fixed_point_implant_keeps_current_goal_one_but_history_changes(self):
        witness = fixed_point_replacement_witness()
        self.assertEqual(witness["A_goal_before"], 1.0)
        self.assertEqual(witness["A_goal_after"], 1.0)
        self.assertTrue(witness["current_channel_profile_identical"])
        self.assertEqual(witness["residual_external_bypass_flow"], 0.0)
        self.assertEqual(witness["historical_formation_status"], "REGISTERED_SURGERY")
        self.assertNotEqual(witness["lambda_audit_current_removal"],
                            witness["lambda_original_implant_prevention"])
        cert = produce_r17_certificate(**kwargs(surgery_history=1, lambda_value=1.0))
        self.assertEqual(cert["historical_formation_profile"]["formation_status"],
                         "REGISTERED_SURGERY")
        self.assertEqual(cert["current_structural_profile"]["state_autonomy"],
                         cert["state_autonomy"])

    def test_lambda_time_origin_and_scope_must_match_and_fit_status(self):
        with self.assertRaises(ValueError):
            produce_r17_certificate(**kwargs(lambda_time_origin="ORIGINAL_IMPLANT_PREVENTION",
                                             lambda_counterfactual_scope="REMOVE_REGISTERED_SURGERIES_AT_AUDIT"))
        with self.assertRaises(ValueError):
            produce_r17_certificate(**kwargs(lambda_status="UNKNOWN", lambda_value=None,
                                             lambda_time_origin="AUDIT_CURRENT_REMOVAL",
                                             lambda_counterfactual_scope="REMOVE_REGISTERED_SURGERIES_AT_AUDIT"))
        cert = produce_r17_certificate(**kwargs(lambda_time_origin="ORIGINAL_IMPLANT_PREVENTION",
                                                lambda_counterfactual_scope="PREVENT_ORIGINAL_SURGERY_AND_RECOMPUTE_DESCENDANTS"))
        self.assertEqual(validate_r17_certificate(cert), [])

    def test_profile_drift_and_legacy_schema_fail_closed(self):
        cert = produce_r17_certificate(**kwargs())
        forged = dict(cert)
        forged["current_structural_profile"] = dict(cert["current_structural_profile"],
                                                    state_autonomy=1.0)
        self.assertTrue(validate_r17_certificate(forged))
        legacy = produce_r15_certificate(channel_schema_version=R16_CHANNEL_SCHEMA_VERSION,
                                         **{k: v for k, v in kwargs().items()
                                            if k not in {"lambda_time_origin", "lambda_counterfactual_scope"}})
        self.assertTrue(validate_r17_certificate(legacy))
        with self.assertRaises(ValueError):
            make_r17_audit_certificate(r16_certificate=cert,
                                       lambda_time_origin="AUDIT_CURRENT_REMOVAL",
                                       lambda_counterfactual_scope="REMOVE_REGISTERED_SURGERIES_AT_AUDIT")

    def test_writer_rejects_invalid_and_accepts_valid(self):
        cert = produce_r17_certificate(**kwargs())
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "cert.json")
            write_r17_certificate(path, cert)
            bad = dict(cert)
            bad["historical_formation_profile"] = dict(cert["historical_formation_profile"],
                                                       formation_status="UNKNOWN")
            with self.assertRaises(ValueError):
                write_r17_certificate(path, bad)

    def test_formation_status_mapping(self):
        self.assertEqual(formation_status(0), "NO_REGISTERED_SURGERY")
        self.assertEqual(formation_status(1), "REGISTERED_SURGERY")
        self.assertEqual(formation_status(None), "UNKNOWN")
        with self.assertRaises(ValueError):
            formation_status(2)


if __name__ == "__main__":
    unittest.main()
