"""Explicit structural-counterfactual endorsement audit (R14 / X5-c).

This module is deliberately separate from ENV-0.  ENV-0's legacy
``law_level_lambda`` is a scenario marker, not this estimand.  Here the
structural equations, factual observations, surgery history, exogenous noise,
and shared-noise downstream decision rule are all explicit, so the three
counterfactual steps can be executed and audited:

1. abduction: recover U from the observed continuous score Z;
2. action: remove the registered surgery J;
3. prediction: evaluate actual/no-surgery endorsement laws with the same
   abducted U and shared downstream noise V.

Lambda measures output-law deviation, not the existence of a surgery history.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from .rng import make_rng


@dataclass(frozen=True)
class AuditEstimate:
    lam: float
    mean_tv: float
    tv_se: float
    n_contexts: int
    surgery_history: int

    @property
    def normal_95_halfwidth(self) -> float:
        return 1.96 * self.tv_se


class ThresholdEndorsementSCM:
    """Z=aX+bJ+U and Y=1{Z+V>=0}, with Gaussian or logistic U,V."""

    def __init__(self, noise: str, *, a: float = 0.35, b: float = 1.0):
        if noise not in {"gaussian", "logistic"}:
            raise ValueError("noise must be 'gaussian' or 'logistic'")
        if not (math.isfinite(a) and math.isfinite(b)):
            raise ValueError("a and b must be finite")
        self.noise = noise
        self.a = float(a)
        self.b = float(b)

    def _cdf(self, z):
        z = np.asarray(z, dtype=float)
        if self.noise == "gaussian":
            # numpy has no erf in some minimal installations; math.erf is
            # vectorized explicitly to keep the dependency surface unchanged.
            flat = np.fromiter((0.5 * (1.0 + math.erf(float(v) / math.sqrt(2.0)))
                                for v in z.ravel()), dtype=float, count=z.size)
            return flat.reshape(z.shape)
        # Stable standard-logistic CDF.
        out = np.empty_like(z)
        positive = z >= 0
        out[positive] = 1.0 / (1.0 + np.exp(-z[positive]))
        ez = np.exp(z[~positive])
        out[~positive] = ez / (1.0 + ez)
        return out

    def sample_score_noise(self, rng, size: int) -> np.ndarray:
        if self.noise == "gaussian":
            return rng.standard_normal(size)
        # Inverse-CDF logistic draw through the registered Generator only.
        u = rng.random(size)
        eps = np.finfo(float).eps
        u = np.clip(u, eps, 1.0 - eps)
        return np.log(u) - np.log1p(-u)

    def abduct(self, x, z, j):
        """U = Z-aX-bJ, exactly point-identified from the factual score."""
        x, z, j = np.broadcast_arrays(np.asarray(x, float), np.asarray(z, float),
                                     np.asarray(j, float))
        if (np.any(~np.isfinite(x)) or np.any(~np.isfinite(z))
                or np.any(~np.isfinite(j))):
            raise ValueError("X,Z,J must be finite")
        if np.any((x != 0.0) & (x != 1.0)) or np.any((j != 0.0) & (j != 1.0)):
            raise ValueError("X and J must be binary")
        return z - self.a * x - self.b * j

    def action_remove_surgery(self, x, u):
        """Structural prediction of the no-surgery score Z^0=aX+U."""
        return self.a * np.asarray(x, float) + np.asarray(u, float)

    def prediction_probabilities(self, x, z, j):
        """Actual/no-surgery Bernoulli laws after abduction-action-prediction."""
        x, z, j = np.broadcast_arrays(np.asarray(x, float), np.asarray(z, float),
                                     np.asarray(j, float))
        u = self.abduct(x, z, j)
        z0 = self.action_remove_surgery(x, u)
        # Symmetric noise: P(Z+V>=0 | Z=z)=F_V(z).
        return self._cdf(z), self._cdf(z0)

    def tv_per_context(self, x, z, j) -> np.ndarray:
        p, p0 = self.prediction_probabilities(x, z, j)
        return np.abs(p - p0)

    def evaluate(self, x, z, j) -> AuditEstimate:
        x, z, j = np.broadcast_arrays(np.asarray(x, float), np.asarray(z, float),
                                     np.asarray(j, float))
        if x.size == 0:
            raise ValueError("at least one audit context is required")
        # Validate factual observations before computing any output.
        self.abduct(x, z, j)
        tv = self.tv_per_context(x, z, j)
        mean_tv = float(tv.mean())
        se = float(tv.std(ddof=1) / math.sqrt(tv.size)) if tv.size > 1 else 0.0
        return AuditEstimate(lam=1.0 - mean_tv, mean_tv=mean_tv, tv_se=se,
                             n_contexts=tv.size, surgery_history=int(np.any(j != 0.0)))

    def simulate_contexts(self, *, n_contexts: int, surgery: int, seed: int):
        if n_contexts < 1 or surgery not in {0, 1}:
            raise ValueError("n_contexts>=1 and surgery must be binary")
        rng = make_rng(seed)
        x = rng.integers(0, 2, size=n_contexts).astype(float)
        j = np.full(n_contexts, float(surgery))
        u = self.sample_score_noise(rng, n_contexts)
        z = self.a * x + self.b * j + u
        return x, z, j

    def shared_noise_disagreement(self, x, z, j, *, seed: int) -> AuditEstimate:
        """Independent finite-V Monte-Carlo cross-check of the CDF-integrated TV."""
        x, z, j = np.broadcast_arrays(np.asarray(x, float), np.asarray(z, float),
                                     np.asarray(j, float))
        rng = make_rng(seed)
        v = self.sample_score_noise(rng, x.size)
        u = self.abduct(x, z, j)
        z0 = self.action_remove_surgery(x, u)
        factual_y = (z + v >= 0.0).astype(float)
        cf_y = (z0 + v >= 0.0).astype(float)
        disagreement = np.abs(factual_y - cf_y)
        mean = float(disagreement.mean())
        se = float(disagreement.std(ddof=1) / math.sqrt(disagreement.size)) \
            if disagreement.size > 1 else 0.0
        return AuditEstimate(lam=1.0 - mean, mean_tv=mean, tv_se=se,
                             n_contexts=disagreement.size,
                             surgery_history=int(np.any(j != 0.0)))


def xor_abduct(y, j):
    """Recover U=Y xor J from factual binary endorsement observations."""
    y, j = np.broadcast_arrays(np.asarray(y, dtype=int), np.asarray(j, dtype=int))
    if y.size == 0:
        raise ValueError("at least one XOR observation is required")
    if np.any((y != 0) & (y != 1)) or np.any((j != 0) & (j != 1)):
        raise ValueError("Y and J must be binary")
    return np.bitwise_xor(y, j)


def xor_endorsement_audit(u, j) -> AuditEstimate:
    """Nondegenerate-across-contexts XOR witness with per-context TV in {0,1}."""
    u, j = np.broadcast_arrays(np.asarray(u, dtype=int), np.asarray(j, dtype=int))
    if u.size == 0:
        raise ValueError("at least one XOR context is required")
    if np.any((u != 0) & (u != 1)) or np.any((j != 0) & (j != 1)):
        raise ValueError("U and J must be binary")
    factual = np.bitwise_xor(u, j)
    counterfactual = u  # action J=0, same abducted U
    tv = (factual != counterfactual).astype(float)
    mean = float(tv.mean())
    se = float(tv.std(ddof=1) / math.sqrt(tv.size)) if tv.size > 1 else 0.0
    return AuditEstimate(lam=1.0 - mean, mean_tv=mean, tv_se=se, n_contexts=tv.size,
                         surgery_history=int(np.any(j != 0)))


def xor_endorsement_audit_from_observations(y, j) -> AuditEstimate:
    """Full abduction-action-prediction path from factual (Y,J), not given U."""
    u = xor_abduct(y, j)
    return xor_endorsement_audit(u, j)


def identity_endorsement_audit(y, j) -> AuditEstimate:
    """Execute abduction-action-prediction for identity endorsement Y=U.

    Abduction recovers U=Y.  Surgery history is present, but its action map has
    no edge into Y, so removing J leaves U and hence Y unchanged.  The two
    conditional output laws are identical by computation, not by convention.
    """
    y, j = np.broadcast_arrays(np.asarray(y, dtype=int), np.asarray(j, dtype=int))
    if y.size == 0:
        raise ValueError("at least one identity-endorsement observation is required")
    if np.any((y != 0) & (y != 1)) or np.any((j != 0) & (j != 1)):
        raise ValueError("Y and J must be binary")
    u = y.copy()  # abduction for the identity structural equation Y=U
    counterfactual = u.copy()  # action J=0: no structural effect on endorsement
    tv = (y != counterfactual).astype(float)
    mean = float(tv.mean())
    se = float(tv.std(ddof=1) / math.sqrt(tv.size)) if tv.size > 1 else 0.0
    return AuditEstimate(lam=1.0 - mean, mean_tv=mean, tv_se=se, n_contexts=tv.size,
                         surgery_history=int(np.any(j != 0)))


def observation_equivalent_xor_witness(u=(0, 1)) -> dict:
    """Same factual fair-Y law and passive behavior, different counterfactual Lambda.

    Both models carry surgery history J=1.  Identity endorsement Y=U has no
    output effect (Lambda=1); XOR endorsement Y=U xor 1 flips every abducted
    point mass (Lambda=0).  Factual Y is fair in both, and the auxiliary
    behavior A is fixed at zero in both by construction.
    """
    u = np.asarray(u, dtype=int)
    if u.size == 0 or np.any((u != 0) & (u != 1)):
        raise ValueError("U must be a nonempty binary vector")
    j = np.ones(u.size, dtype=int)
    identity_factual = u.copy()
    xor_factual = np.bitwise_xor(u, j)
    identity = identity_endorsement_audit(identity_factual, j)
    flipped = xor_endorsement_audit_from_observations(xor_factual, j)
    return {
        "identity": identity,
        "xor": flipped,
        "identity_factual_y": identity_factual,
        "xor_factual_y": xor_factual,
        "identity_p_y1": float(identity_factual.mean()),
        "xor_p_y1": float(xor_factual.mean()),
        "identity_passive_action": np.zeros(u.size, dtype=int),
        "xor_passive_action": np.zeros(u.size, dtype=int),
    }
