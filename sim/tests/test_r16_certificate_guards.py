"""R16 fail-closed certificate and T2 compatibility guards.

These are deterministic contract tests.  A syntactically valid artifact hash
binds a declared registered artifact; it is not evidence of external truth.
"""
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from autonomy_sim.logschema import validate_r15_certificate, write_r15_certificate  # noqa: E402
from autonomy_sim.r15_guards import (  # noqa: E402
    R16_CHANNEL_SCHEMA_VERSION,
    componentwise_compatible,
    goal_interval_compatible,
    make_audit_certificate,
    produce_r15_certificate,
)

MODEL_HASH = "a" * 64
EVIDENCE_HASH = "0123456789abcdef" * 4


def certificate_kwargs(layer="L1"):
    channel_count = {"L0": 2, "L1": 4, "L2": 5}[layer]
    lambda_status = "DEFINED" if layer == "L2" else "NOT_APPLICABLE"
    return {
        "layer": layer,
        "channels": tuple(0.8 + 0.02 * i for i in range(channel_count)),
        "weights": tuple(1.0 for _ in range(channel_count)),
        "resource_ratios": (1.0, 0.9),
        "defense_margins": (0.7,),
        "surgery_history": 0,
        "lambda_value": 0.8 if lambda_status == "DEFINED" else None,
        "lambda_status": lambda_status,
        "source_registration": "COMPLETE",
        "mechanism_evidence": "NONE",
        "channel_schema_version": R16_CHANNEL_SCHEMA_VERSION,
        "org_mode": "L0_INTERNAL" if layer == "L0" else "L1_NORMATIVE_NR",
        "goal_mode": "STRUCTURAL_POINT",
        "state_readiness_version": "R15_SPLIT",
        "model_hash": MODEL_HASH,
        "evidence_hash": EVIDENCE_HASH,
    }


def produce_certificate(layer="L1", **overrides):
    kwargs = certificate_kwargs(layer)
    kwargs.update(overrides)
    return produce_r15_certificate(**kwargs)


class R16ComponentwiseFiniteGuards(unittest.TestCase):
    def test_nan_and_infinities_raise_including_nan_to_nan(self):
        bad_values = (math.nan, math.inf, -math.inf)
        for bad in bad_values:
            for before, after in (((bad), 0.5), (0.5, bad), (bad, bad)):
                with self.subTest(bad=bad, before=before, after=after):
                    with self.assertRaises(ValueError):
                        componentwise_compatible({"x": before}, {"x": after})

    def test_all_values_are_validated_before_an_early_order_failure(self):
        # The first component already decreases.  A later NaN must still raise,
        # rather than letting an early False hide malformed numeric evidence.
        before = {"decreases": 0.9, "malformed": math.nan}
        after = {"decreases": 0.1, "malformed": math.nan}
        with self.assertRaises(ValueError):
            componentwise_compatible(before, after)
        before = {"na_status_changes": None, "malformed": math.inf}
        after = {"na_status_changes": 0.1, "malformed": math.inf}
        with self.assertRaises(ValueError):
            componentwise_compatible(before, after)

    def test_tolerance_must_be_finite_and_nonnegative(self):
        for tol in (-1e-12, math.nan, math.inf, -math.inf):
            with self.subTest(tol=tol):
                with self.assertRaises(ValueError):
                    componentwise_compatible({"x": 0.2}, {"x": 0.1}, tol=tol)
        self.assertTrue(componentwise_compatible({"x": 0.2}, {"x": 0.1}, tol=0.1))
        self.assertFalse(componentwise_compatible({"x": 0.2}, {"x": 0.1}, tol=0.0))

    def test_na_is_explicit_and_is_not_a_nan_sentinel(self):
        self.assertTrue(componentwise_compatible({"x": None}, {"x": None}))
        self.assertFalse(componentwise_compatible({"x": None}, {"x": 0.0}))
        self.assertFalse(componentwise_compatible({"x": 0.0}, {"x": None}))
        with self.assertRaises(ValueError):
            componentwise_compatible({"x": None}, {"x": math.nan})


class R16GoalIntervalGuards(unittest.TestCase):
    def test_endpoint_order_and_tolerance(self):
        self.assertTrue(goal_interval_compatible((0.2, 0.6), (0.2, 0.6)))
        self.assertTrue(goal_interval_compatible((0.2, 0.6), (0.3, 0.7)))
        self.assertFalse(goal_interval_compatible((0.2, 0.6), (0.19, 0.7)))
        self.assertFalse(goal_interval_compatible((0.2, 0.6), (0.3, 0.59)))
        self.assertTrue(goal_interval_compatible(
            (0.2, 0.6), (0.199, 0.599), tol=0.001))

    def test_crossing_interval_is_not_lower_bound_only_improvement(self):
        # The lower endpoint increases while the upper endpoint decreases.
        # Endpoint order says nothing about pairing individual worlds either.
        self.assertFalse(goal_interval_compatible((0.2, 0.8), (0.3, 0.7)))
        self.assertFalse(goal_interval_compatible((0.2, 0.6), (0.1, 0.9)))

    def test_interval_shape_finiteness_bounds_order_and_tol_are_checked(self):
        invalid_intervals = (
            (0.1,), (0.1, 0.2, 0.3), (0.3, 0.2), (-0.1, 0.2),
            (0.1, 1.1), (math.nan, math.nan), (math.inf, math.inf),
            (0.1, -math.inf),
        )
        for interval in invalid_intervals:
            for position in ("before", "after"):
                before = interval if position == "before" else (0.1, 0.2)
                after = interval if position == "after" else (0.1, 0.2)
                with self.subTest(interval=interval, position=position):
                    with self.assertRaises(ValueError):
                        goal_interval_compatible(before, after)
        for tol in (-1.0, math.nan, math.inf, -math.inf):
            with self.assertRaises(ValueError):
                goal_interval_compatible((0.1, 0.2), (0.1, 0.2), tol=tol)


class R16CertificateEvidenceGuards(unittest.TestCase):
    def assert_writer_rejects(self, cert):
        self.assertTrue(validate_r15_certificate(cert))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "certificate.json"
            with self.assertRaises(ValueError):
                write_r15_certificate(str(path), cert)
            self.assertFalse(path.exists())

    def test_complete_registration_without_scm_is_not_scm_audited(self):
        cert = produce_certificate(mechanism_evidence="NONE")
        self.assertEqual(cert["registration_completeness"], "COMPLETE")
        self.assertEqual(cert["mechanism_evidence"], "NONE")
        self.assertEqual(cert["evidence_ceiling"], "REGISTERED_COMPLETE")
        self.assertNotEqual(cert["evidence_ceiling"], "SCM_AUDITED")
        self.assertEqual(validate_r15_certificate(cert), [])
        forged = dict(cert, evidence_ceiling="SCM_AUDITED")
        self.assert_writer_rejects(forged)

    def test_explicit_audited_scm_evidence_can_reach_scm_ceiling(self):
        cert = produce_certificate(layer="L2", mechanism_evidence="SCM_AUDITED")
        self.assertEqual(cert["mechanism_evidence"], "SCM_AUDITED")
        self.assertEqual(cert["evidence_ceiling"], "SCM_AUDITED")
        self.assertFalse(cert["external_construct_validation"])
        self.assertFalse(cert["integrity_certificate"])
        self.assertEqual(validate_r15_certificate(cert), [])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "certificate.json"
            write_r15_certificate(str(path), cert)
            self.assertEqual(validate_r15_certificate(json.loads(path.read_text())), [])

    def test_state_cannot_exceed_viability_or_claim_audited_ceiling(self):
        kwargs = certificate_kwargs("L2")
        with self.assertRaises(ValueError):
            make_audit_certificate(
                layer="L2", state_autonomy=1.0, viability_state=0.0,
                defense_readiness=0.7, surgery_history=0, lambda_value=0.8,
                lambda_status="DEFINED", source_registration="COMPLETE",
                registration_completeness="COMPLETE", mechanism_evidence="SCM_AUDITED",
                channel_schema_version=kwargs["channel_schema_version"],
                org_mode=kwargs["org_mode"], goal_mode=kwargs["goal_mode"],
                state_readiness_version=kwargs["state_readiness_version"],
                model_hash=kwargs["model_hash"], evidence_hash=kwargs["evidence_hash"])
        forged = dict(produce_certificate(layer="L2", mechanism_evidence="SCM_AUDITED"),
                      state_autonomy=1.0, viability_state=0.0)
        self.assert_writer_rejects(forged)
        zero = produce_certificate(layer="L2", mechanism_evidence="SCM_AUDITED",
                                   resource_ratios=(0.0,))
        self.assertEqual(zero["state_autonomy"], 0.0)
        self.assertEqual(zero["viability_state"], 0.0)
        self.assertEqual(validate_r15_certificate(zero), [])

    def test_unknown_or_incomplete_fields_cap_even_explicit_scm_evidence(self):
        variants = (
            {"surgery_history": None},
            {"source_registration": "UNKNOWN"},
            {"source_registration": "INCOMPLETE"},
            {"source_registration": "UNKNOWN", "registration_completeness": "UNKNOWN"},
            {"lambda_status": "UNKNOWN", "lambda_value": None},
        )
        for overrides in variants:
            with self.subTest(overrides=overrides):
                cert = produce_certificate(mechanism_evidence="SCM_AUDITED", **overrides)
                self.assertEqual(cert["evidence_ceiling"], "LIMITED")
                self.assertEqual(validate_r15_certificate(cert), [])

    def test_lambda_na_at_l0_l1_is_not_unknown_but_unknown_is_limited(self):
        for layer in ("L0", "L1"):
            with self.subTest(layer=layer, status="NOT_APPLICABLE"):
                cert = produce_certificate(layer=layer)
                self.assertEqual(cert["lambda_status"], "NOT_APPLICABLE")
                self.assertEqual(cert["evidence_ceiling"], "REGISTERED_COMPLETE")
            with self.subTest(layer=layer, status="UNKNOWN"):
                cert = produce_certificate(
                    layer=layer, lambda_status="UNKNOWN", lambda_value=None)
                self.assertEqual(cert["evidence_ceiling"], "LIMITED")
        with self.assertRaises(ValueError):
            produce_certificate(layer="L2", lambda_status="NOT_APPLICABLE", lambda_value=None)

    def test_registration_and_source_aliases_must_agree(self):
        cert = produce_certificate(
            source_registration=None, registration_completeness="COMPLETE")
        self.assertEqual(cert["source_registration"], "COMPLETE")
        self.assertEqual(cert["registration_completeness"], "COMPLETE")
        with self.assertRaises(ValueError):
            produce_certificate(registration_completeness="UNKNOWN")
        tampered = dict(cert, registration_completeness="UNKNOWN")
        self.assert_writer_rejects(tampered)


class R16CertificateMetadataGuards(unittest.TestCase):
    def assert_writer_rejects(self, cert):
        self.assertTrue(validate_r15_certificate(cert))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "certificate.json"
            with self.assertRaises(ValueError):
                write_r15_certificate(str(path), cert)
            self.assertFalse(path.exists())

    def test_legacy_bundle_like_values_without_metadata_are_rejected(self):
        legacy = certificate_kwargs("L1")
        for field in ("channel_schema_version", "org_mode", "goal_mode",
                      "state_readiness_version", "model_hash", "evidence_hash",
                      "mechanism_evidence"):
            legacy.pop(field, None)
        # These channel numbers are otherwise entirely plausible L1 values.
        with self.assertRaises(ValueError):
            produce_r15_certificate(**legacy)

        # Supplying only the old source-registration label is not enough.
        legacy["mechanism_evidence"] = "NONE"
        with self.assertRaises(ValueError):
            produce_r15_certificate(**legacy)

    def test_every_new_metadata_field_is_mandatory_at_production(self):
        for field in ("channel_schema_version", "org_mode", "goal_mode",
                      "state_readiness_version", "model_hash", "evidence_hash"):
            kwargs = certificate_kwargs("L1")
            kwargs.pop(field)
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    produce_r15_certificate(**kwargs)

    def test_legacy_or_fake_schema_and_readiness_tags_fail_closed(self):
        for field, bad_values in (
            ("channel_schema_version", ("R15", "R15_CHANNEL_SCHEMA", "R17_CHANNEL_SCHEMA_V1")),
            ("state_readiness_version", ("R15", "R14_COMBINED", "r15_split")),
            ("goal_mode", ("LEGACY_POINT", "POINT", None)),
        ):
            for bad in bad_values:
                with self.subTest(field=field, bad=bad):
                    with self.assertRaises(ValueError):
                        produce_certificate(**{field: bad})
                    tampered = dict(produce_certificate(), **{field: bad})
                    self.assert_writer_rejects(tampered)

    def test_org_mode_is_layer_checked_not_merely_self_declared(self):
        for layer in ("L1", "L2"):
            with self.subTest(layer=layer):
                with self.assertRaises(ValueError):
                    produce_certificate(layer=layer, org_mode="L0_INTERNAL")
        with self.assertRaises(ValueError):
            produce_certificate(layer="L0", org_mode="L1_NORMATIVE_NR")
        cert = produce_certificate(layer="L0", model_hash=None, evidence_hash=None)
        self.assertEqual(cert["org_mode"], "L0_INTERNAL")
        self.assertEqual(validate_r15_certificate(cert), [])

    def test_l1_l2_require_strict_lowercase_64_hex_artifact_hashes(self):
        invalid_hashes = (None, "", "a" * 63, "a" * 65, "A" * 64,
                          "g" * 64, 123, MODEL_HASH + "\n")
        for layer in ("L1", "L2"):
            for field in ("model_hash", "evidence_hash"):
                for bad in invalid_hashes:
                    with self.subTest(layer=layer, field=field, bad=bad):
                        with self.assertRaises(ValueError):
                            produce_certificate(layer=layer, **{field: bad})
                        tampered = dict(produce_certificate(layer=layer), **{field: bad})
                        self.assertTrue(validate_r15_certificate(tampered))

    def test_scm_ceiling_requires_artifact_bindings_even_at_l0(self):
        for field in ("model_hash", "evidence_hash"):
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    produce_certificate(
                        layer="L0", mechanism_evidence="SCM_AUDITED", **{field: None})

    def test_legacy_sidecar_and_faked_org_metadata_are_unwritable(self):
        valid = produce_certificate()
        legacy = dict(valid)
        for field in ("channel_schema_version", "org_mode", "goal_mode",
                      "state_readiness_version", "model_hash", "evidence_hash",
                      "registration_completeness", "mechanism_evidence"):
            legacy.pop(field)
        legacy["evidence_ceiling"] = "SCM_AUDITED"
        self.assert_writer_rejects(legacy)

        faked = dict(valid, org_mode="L0_INTERNAL")
        self.assert_writer_rejects(faked)
        wrong_schema = dict(valid, channel_schema_version="R15_CHANNEL_SCHEMA")
        self.assert_writer_rejects(wrong_schema)

    def test_goal_interval_mode_is_explicit_and_valid(self):
        cert = produce_certificate(goal_mode="IRL_INTERVAL")
        self.assertEqual(cert["goal_mode"], "IRL_INTERVAL")
        self.assertEqual(validate_r15_certificate(cert), [])

    def test_direct_certificate_builder_uses_the_same_fail_closed_contract(self):
        kwargs = certificate_kwargs("L1")
        direct = make_audit_certificate(
            layer="L1", state_autonomy=0.8, viability_state=0.9,
            defense_readiness=0.7, surgery_history=0, lambda_value=None,
            lambda_status="NOT_APPLICABLE", source_registration="COMPLETE",
            registration_completeness="COMPLETE", mechanism_evidence="NONE",
            channel_schema_version=kwargs["channel_schema_version"],
            org_mode=kwargs["org_mode"], goal_mode=kwargs["goal_mode"],
            state_readiness_version=kwargs["state_readiness_version"],
            model_hash=kwargs["model_hash"], evidence_hash=kwargs["evidence_hash"])
        self.assertEqual(direct["evidence_ceiling"], "REGISTERED_COMPLETE")
        self.assertEqual(validate_r15_certificate(direct), [])
        with self.assertRaises(ValueError):
            make_audit_certificate(
                layer="L1", state_autonomy=0.8, viability_state=0.9,
                defense_readiness=0.7, surgery_history=0, lambda_value=None,
                lambda_status="NOT_APPLICABLE", source_registration="COMPLETE")

    def test_writer_rejects_nonfinite_numbers_and_true_validation_flags(self):
        for value in (math.nan, math.inf, -math.inf):
            cert = dict(produce_certificate(), state_autonomy=value)
            self.assert_writer_rejects(cert)
        self.assert_writer_rejects(dict(produce_certificate(),
                                        external_construct_validation=True))
        self.assert_writer_rejects(dict(produce_certificate(), integrity_certificate=True))


if __name__ == "__main__":
    unittest.main()
