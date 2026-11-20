"""R17-native small multi-step end-to-end benchmark (exact + seeded sampling).

This is an internal concept-validation benchmark, not external construct
validation.  The operating policy is reactive and closed-loop; the execution
channel is audited separately through precommitted open-loop sequence
interventions in the same environment.  All major current estimands are
computed on the same registered instance, with historical formation reported
as a co-primary profile rather than inferred from the channel scalar.
"""
from __future__ import annotations

from dataclasses import dataclass
import itertools
import math

import numpy as np

from .aggregate import composite_A
from .open_loop_execution import open_loop_execution_score
from .r15_guards import goal_from_distance, goal_interval_from_distances, state_defense_split
from .source_attribution import (joint_directed_information_nats,
                                 nats_to_bits, ordered_attribution_nats,
                                 shapley_order_average_nats)

R, N, I, A = 0, 1, 2, 3


@dataclass(frozen=True)
class NativeConfig:
    horizon: int = 3
    p_obs: float = 0.1
    q_self: float = 0.1
    resource_ratios: tuple[float, ...] = (1.0, 0.9, 0.8)
    defense_margins: tuple[float, ...] = (0.9, 0.7)
    surgery: int = 0
    action_effect: bool = True
    weights: tuple[float, ...] = (0.2, 0.2, 0.2, 0.2, 0.2)

    def validate(self) -> None:
        if self.horizon < 2:
            raise ValueError("native benchmark requires horizon>=2")
        for name, value in (("p_obs", self.p_obs), ("q_self", self.q_self)):
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0,1]")
        if self.surgery not in {0, 1}:
            raise ValueError("surgery must be binary")
        if len(self.resource_ratios) != self.horizon:
            raise ValueError("resource_ratios length must equal horizon")
        if not self.weights or any(w <= 0 for w in self.weights):
            raise ValueError("weights must be positive")
        if not math.isclose(sum(self.weights), 1.0, abs_tol=1e-12):
            raise ValueError("weights must sum to one")


def _binary_entropy(p: float) -> float:
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -p * math.log(p) - (1 - p) * math.log(1 - p)


def _operating_step(config: NativeConfig, x: int, r: tuple[int, ...],
                    i: tuple[int, ...], v: tuple[int, ...]):
    """Return R,N,I,A,E,O,B trajectories for one exogenous assignment."""
    horizon = config.horizon
    e = x
    n_prev = None
    ns, es, os_, bs, actions = [], [], [], [], []
    for t in range(horizon):
        o = e ^ v[t]
        b = o
        n = i[0] if t == 0 else (n_prev ^ actions[t - 1] ^ i[t])
        a = n ^ r[t] ^ b
        ns.append(n)
        es.append(e)
        os_.append(o)
        bs.append(b)
        actions.append(a)
        n_prev = n
        e = e ^ a if config.action_effect else e
    return tuple(r), tuple(ns), tuple(i), tuple(actions), tuple(es), tuple(os_), tuple(bs)


def exact_source_joints(config: NativeConfig):
    """Exact joint laws over (R^T,N^T,I^T,A^T) and an alternative partition."""
    config.validate()
    horizon = config.horizon
    joint = np.zeros((2,) * (4 * horizon))
    alt = np.zeros((2,) * (4 * horizon))
    v_values = tuple(itertools.product((0, 1), repeat=horizon))
    for x in (0, 1):
        for r in itertools.product((0, 1), repeat=horizon):
            for i in itertools.product((0, 1), repeat=horizon):
                for v in v_values:
                    prob = 0.5 ** (1 + 2 * horizon)
                    for bit in v:
                        prob *= config.p_obs if bit else (1 - config.p_obs)
                    rr, nn, ii, aa, _, _, _ = _operating_step(config, x, r, i, v)
                    index = rr + nn + ii + aa
                    joint[index] += prob
                    # Alternative semantic partition: the innovation register is
                    # reclassified as part of normative memory; R_alt is empty.
                    n_alt = tuple(nv ^ rv for nv, rv in zip(nn, rr))
                    alt_index = (0,) * horizon + n_alt + ii + aa
                    alt[alt_index] += prob
    return joint, alt


def _share_report(joint, horizon: int) -> dict:
    rni = ordered_attribution_nats(joint, horizon=horizon, order=(R, N, I), action=A)
    nri = ordered_attribution_nats(joint, horizon=horizon, order=(N, R, I), action=A)
    total = joint_directed_information_nats(joint, horizon=horizon,
                                            sources=(R, N, I), action=A)
    average = shapley_order_average_nats(joint, horizon=horizon,
                                         sources=(R, N), action=A)
    total_bits = nats_to_bits(total)
    return {
        "flows_bits_RNI": [nats_to_bits(v) for v in rni],
        "flows_bits_NRI": [nats_to_bits(v) for v in nri],
        "joint_di_bits": total_bits,
        "normative_share_RNI": nats_to_bits(rni[1]) / total_bits if total_bits > 0 else None,
        "normative_share_NRI": nats_to_bits(nri[0]) / total_bits if total_bits > 0 else None,
        "normative_share_order_average": (
            nats_to_bits(average[N]) / total_bits if total_bits > 0 else None),
    }


def source_report(config: NativeConfig) -> dict:
    joint, alt = exact_source_joints(config)
    return {
        "registered_partition": _share_report(joint, config.horizon),
        "alternative_partition_R_as_normative_memory": _share_report(alt, config.horizon),
        "semantic_note": "Alternative partition is preregistered sensitivity, not a selected score.",
    }


def open_loop_execution_report(config: NativeConfig) -> dict:
    """Open-loop n=2 execution audit from t=1 in the same environment."""
    config.validate()
    n = 2
    kernels = []
    for a1, a2 in itertools.product((0, 1), repeat=2):
        parity = a1 ^ a2 if config.action_effect else 0
        # O_3 = E_1 xor parity xor V_3; take registered E_1=0 state.
        p_one = config.p_obs if parity == 0 else (1 - config.p_obs)
        kernels.append([1 - p_one, p_one])
    kernels = np.asarray(kernels, dtype=float)
    state_zero = open_loop_execution_score(kernels, n_actions=n, action_alphabet_size=2)
    # E_1 is fair and only flips the output label, so the state average is identical.
    return {
        "protocol": "PRECOMMITTED_OPEN_LOOP_SEQUENCE_IN_SAME_ENVIRONMENT",
        "horizon_actions": n,
        "registered_state": {"E_1": 0, "N_1": 0, "B_1": 0},
        "sequence_kernels": kernels.tolist(),
        "state_conditional": state_zero,
        "state_averaged_a_exec": state_zero["a_exec"],
        "analytic_capacity_nats": (math.log(2.0) - _binary_entropy(config.p_obs)
                                   if config.action_effect else 0.0),
        "uses_intermediate_observations": False,
    }


def goal_report() -> dict:
    structural = goal_from_distance(0.5, 1.0)
    interval = goal_interval_from_distances((0.0, 0.5), 1.0)
    return {
        "structural_point": structural,
        "U_eff": 1.5,
        "Fix": [0.0, 1.0],
        "d_c": 1.0,
        "behavior_IRL_identified_interval": list(interval),
        "note": "Caller-registered admissible reward distances; not a generic MaxEnt-IRL solver.",
    }


def reflection_report(config: NativeConfig) -> dict:
    fidelity = 1.0 - _binary_entropy(config.q_self) / math.log(2.0)
    # Explicit XOR endorsement SCM: Y=U xor J, no-surgery Y0=U.
    lambda_value = 1.0 if config.surgery == 0 else 0.0
    consistency = 1.0  # every registered normative update is logged as endorsed.
    return {
        "fidelity": fidelity,
        "endorsement_consistency": consistency,
        "Lambda": lambda_value,
        "lambda_time_origin": "AUDIT_CURRENT_REMOVAL",
        "lambda_counterfactual_scope": "REMOVE_REGISTERED_SURGERIES_AT_AUDIT",
        "A_ref": fidelity * consistency * lambda_value,
        "surgery_history": config.surgery,
        "event_log_policy": "all normative updates carry endorsement events",
    }


def exact_bundle(config: NativeConfig) -> dict:
    config.validate()
    source = source_report(config)
    execution = open_loop_execution_report(config)
    goal = goal_report()
    reflection = reflection_report(config)
    a_org = source["registered_partition"]["normative_share_RNI"]
    a_exec = execution["state_averaged_a_exec"]
    a_epi = 1.0 - config.p_obs
    channels = (a_org, goal["structural_point"], a_exec, a_epi, reflection["A_ref"])
    split = state_defense_split(1.0, resource_ratios=config.resource_ratios,
                                defense_margins=config.defense_margins)
    composite = composite_A(split["viability_state"], channels, config.weights, sigma=1.0)
    return {
        "config": {
            "horizon": config.horizon, "p_obs": config.p_obs,
            "q_self": config.q_self, "surgery": config.surgery,
            "action_effect": config.action_effect,
            "resource_ratios": list(config.resource_ratios),
            "defense_margins": list(config.defense_margins),
            "weights": list(config.weights),
        },
        "source": source,
        "execution_open_loop": execution,
        "goal": goal,
        "epistemic": {"A_epi": a_epi, "belief": "B_t=O_t", "ground_truth": "E_t"},
        "reflection": reflection,
        "channels": {
            "a_org_RNI": a_org, "a_goal_structural": goal["structural_point"],
            "a_exec_open_loop": a_exec, "a_epi": a_epi, "a_ref": reflection["A_ref"],
        },
        "viability_state": split["viability_state"],
        "defense_readiness": split["defense_readiness"],
        "state_autonomy": composite,
        "resilience_autonomy": split["defense_readiness"] * composite,
        "historical_formation_status": ("REGISTERED_SURGERY" if config.surgery
                                        else "NO_REGISTERED_SURGERY"),
        "evidence_grade": "INTERNAL_EXACT_AND_SEEDED_SAMPLING_CONCEPT_VALIDATION",
        "external_construct_validation": False,
    }


def _sample_source_joint(config: NativeConfig, n_samples: int, rng) -> np.ndarray:
    horizon = config.horizon
    counts = np.zeros((2,) * (4 * horizon))
    for _ in range(n_samples):
        x = int(rng.integers(0, 2))
        r = tuple(int(v) for v in rng.integers(0, 2, size=horizon))
        i = tuple(int(v) for v in rng.integers(0, 2, size=horizon))
        v = tuple(int(bit) for bit in (rng.random(horizon) < config.p_obs))
        rr, nn, ii, aa, _, _, _ = _operating_step(config, x, r, i, v)
        counts[rr + nn + ii + aa] += 1.0
    return counts / counts.sum()


def sample_errors(config: NativeConfig, *, n_samples: int = 4096, seed: int = 20261119) -> dict:
    """Seeded plug-in sampling errors against exact truth; not a power claim."""
    config.validate()
    rng = np.random.default_rng(seed)
    exact = exact_bundle(config)
    empirical_joint = _sample_source_joint(config, n_samples, rng)
    sampled_source = _share_report(empirical_joint, config.horizon)
    exact_source = exact["source"]["registered_partition"]

    # Epistemic accuracy: independent trajectory-level Bernoulli outcomes.
    hits = rng.random(n_samples) >= config.p_obs
    epi_mean = float(hits.mean())
    epi_se = float(hits.std(ddof=1) / math.sqrt(n_samples))

    # Reflection fidelity from sampled (theta,M) pairs.
    theta = rng.integers(0, 2, size=n_samples)
    m = theta ^ (rng.random(n_samples) < config.q_self).astype(int)
    joint_tm = np.zeros((2, 2))
    for tval, mval in zip(theta, m):
        joint_tm[tval, mval] += 1.0
    joint_tm /= joint_tm.sum()
    pt = joint_tm.sum(axis=1)
    pm = joint_tm.sum(axis=0)
    mi = 0.0
    for tval in range(2):
        for mval in range(2):
            p = joint_tm[tval, mval]
            if p > 0:
                mi += p * math.log(p / (pt[tval] * pm[mval]))
    h_theta = -float(np.sum(pt[pt > 0] * np.log(pt[pt > 0])))
    fidelity_sample = mi / h_theta if h_theta > 0 else 0.0

    # Lambda contexts from the explicit XOR SCM.
    u = rng.integers(0, 2, size=n_samples)
    y = u ^ config.surgery
    tv = float(np.mean(y != u))
    lambda_sample = 1.0 - tv

    # Open-loop sequence kernels sampled under interventions.
    kernels = np.zeros((4, 2))
    for seq_index, (a1, a2) in enumerate(itertools.product((0, 1), repeat=2)):
        parity = a1 ^ a2 if config.action_effect else 0
        v3 = (rng.random(n_samples) < config.p_obs).astype(int)
        o3 = parity ^ v3
        kernels[seq_index, 1] = float(o3.mean())
        kernels[seq_index, 0] = 1.0 - kernels[seq_index, 1]
    exec_sample = open_loop_execution_score(kernels, n_actions=2, action_alphabet_size=2)

    def diff(key):
        return float(abs(sampled_source[key] - exact_source[key]))

    # Descriptive atom-level bootstrap for the plug-in source shares.  This is
    # not an independent-instance confidence interval and does not establish
    # asymptotic consistency.
    bootstrap = {key: [] for key in ("normative_share_RNI", "normative_share_NRI",
                                     "normative_share_order_average", "joint_di_bits")}
    flat = empirical_joint.ravel()
    for _ in range(100):
        resampled = rng.multinomial(n_samples, flat).reshape(empirical_joint.shape) / n_samples
        report = _share_report(resampled, config.horizon)
        for key in bootstrap:
            bootstrap[key].append(report[key])
    source_intervals = {}
    for key, values in bootstrap.items():
        arr = np.asarray(values, dtype=float)
        source_intervals[key] = {
            "bootstrap_se": float(arr.std(ddof=1)),
            "percentile_95": [float(np.percentile(arr, 2.5)),
                              float(np.percentile(arr, 97.5))],
        }

    fidelity_boot = []
    for _ in range(100):
        idx = rng.integers(0, n_samples, size=n_samples)
        jt = np.zeros((2, 2))
        for tval, mval in zip(theta[idx], m[idx]):
            jt[tval, mval] += 1.0
        jt /= jt.sum()
        pt_b = jt.sum(axis=1)
        pm_b = jt.sum(axis=0)
        mi_b = 0.0
        for tval in range(2):
            for mval in range(2):
                p = jt[tval, mval]
                if p > 0:
                    mi_b += p * math.log(p / (pt_b[tval] * pm_b[mval]))
        h_b = -float(np.sum(pt_b[pt_b > 0] * np.log(pt_b[pt_b > 0])))
        fidelity_boot.append(mi_b / h_b if h_b > 0 else 0.0)
    fidelity_arr = np.asarray(fidelity_boot)

    kernel_intervals = []
    z = 1.96
    for seq_index in range(4):
        p_hat = float(kernels[seq_index, 1])
        denom = 1 + z * z / n_samples
        center = (p_hat + z * z / (2 * n_samples)) / denom
        half = z * math.sqrt(p_hat * (1 - p_hat) / n_samples
                             + z * z / (4 * n_samples * n_samples)) / denom
        kernel_intervals.append([max(0.0, center - half), min(1.0, center + half)])

    return {
        "seed": seed,
        "n_samples_per_object": n_samples,
        "source_share_abs_errors": {
            "RNI": diff("normative_share_RNI"),
            "NRI": diff("normative_share_NRI"),
            "order_average": diff("normative_share_order_average"),
            "joint_di_bits": abs(sampled_source["joint_di_bits"] - exact_source["joint_di_bits"]),
        },
        "source_bootstrap_intervals": source_intervals,
        "epistemic": {"sample_mean": epi_mean, "se": epi_se,
                      "abs_error": abs(epi_mean - exact["epistemic"]["A_epi"])},
        "reflection_fidelity": {"sample": float(fidelity_sample),
                                "abs_error": float(abs(fidelity_sample - exact["reflection"]["fidelity"])),
                                "bootstrap_se": float(fidelity_arr.std(ddof=1)),
                                "percentile_95": [float(np.percentile(fidelity_arr, 2.5)),
                                                  float(np.percentile(fidelity_arr, 97.5))]},
        "Lambda": {"sample": float(lambda_sample),
                   "abs_error": float(abs(lambda_sample - exact["reflection"]["Lambda"]))},
        "execution_open_loop": {"sample_a_exec": float(exec_sample["a_exec"]),
                                "abs_error": float(abs(exec_sample["a_exec"]
                                                       - exact["execution_open_loop"]["state_averaged_a_exec"])),
                                "kernel_wilson_95": kernel_intervals},
        "interpretation": "Finite-sample implementation agreement on this registered instance, not statistical consistency or external validation.",
    }


def run_benchmark(*, n_samples: int = 4096, seed: int = 20261119) -> dict:
    baseline = exact_bundle(NativeConfig(surgery=0))
    surgery = exact_bundle(NativeConfig(surgery=1))
    decoupled = exact_bundle(NativeConfig(action_effect=False))
    return {
        "artifact_version": "R17-native-benchmark-v1",
        "status": "INTERNAL_CONCEPT_VALIDATION_NOT_EXTERNAL",
        "baseline": baseline,
        "surgery_arm": surgery,
        "action_decoupled_negative_control": decoupled,
        "sampling": sample_errors(NativeConfig(surgery=0), n_samples=n_samples, seed=seed),
        "scope": {
            "operating_policy": "reactive closed-loop A_t=N_t xor R_t xor B_t",
            "execution_audit": "precommitted open-loop sequence interventions, n=2",
            "historical_formation": "co-primary profile, not inferred from current scalar",
            "generic_MaxEnt_IRL_solver": False,
            "external_construct_validation": False,
        },
    }
