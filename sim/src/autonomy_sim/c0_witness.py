"""Nondegenerate same-environment R14 C0-CF-v2 witness.

Both arms share environment, observation channel, policy, dynamics, horizon and
registered coarse-graining. Only the belief-update law differs. Unlike the
invalid first fixture, this version has active policy rows, positive execution
empowerment, and a nondegenerate goal space. Composite values are computed from
those channel functionals, not assigned illustratively.
"""
from __future__ import annotations

import numpy as np

from .aggregate import composite_A
from .components import truth_A_epi_real, truth_A_goal
from .counterfactual import observation_equivalent_xor_witness
from .di import truth_A_org
from .empowerment import a_exec as normalize_a_exec
from .empowerment import empowerment_support, step_channels_from_esz
from .graph import Alphabet, CausalModel, Kernels
from .propagate import truth_marginals, truth_step_joints


def build_same_environment_c0_models():
    al = Alphabet(n_E=2, n_O=2, n_A=2, n_G=2, n_B=2, n_M=1, n_R=1, n_Z=1)
    obs = np.zeros((2, 2, 2))
    env = np.zeros((2, 2, 1, 2))
    for e in range(2):
        obs[e, :, e] = 1.0
        for a in range(2):
            # Next environment state is action-driven but independent of the
            # current environment, so belief updating cannot alter empowerment.
            env[e, a, 0, a] = 1.0
    faithful = np.zeros((2, 2, 2))
    pinned = np.zeros((2, 2, 2))
    for b in range(2):
        for o in range(2):
            faithful[b, o, o] = 1.0
            pinned[b, o, 1] = 1.0
    policy = np.array([[0.8, 0.2], [0.8, 0.2], [0.2, 0.8], [0.2, 0.8]])

    def build(belief, params):
        model = CausalModel(
            alphabet=al,
            kernels=Kernels(
                obs=obs.copy(), belief=belief.copy(), internal=np.eye(al.n_GMR),
                policy=policy.copy(), env=env.copy(), resource=np.ones((1, 1)),
                init_E=np.array([0.5, 0.5]), init_S=np.full(al.n_S, 1.0 / al.n_S),
                init_Z=np.array([1.0]), init_A=np.array([0.5, 0.5])),
            params=params)
        model.validate()
        return model

    z1 = build(faithful, {"fixture": "r14_c0cf_v2", "surgery_history": 1})
    z2 = build(pinned, {"fixture": "r14_c0cf_v2", "surgery_history": 1,
                        "beta_B": {"kind": "pin_independent_of_environment", "target_b": 1}})
    return z1, z2


def trajectory_joint_eoa(model, T: int) -> dict:
    """Exact full-horizon joint law over (E^T,O^T,A^T), with hidden states summed."""
    al, k = model.alphabet, model.kernels
    # Prefix key: (E-history, O-history, A-history, current S, current Z, previous A).
    states = {}
    for e in range(al.n_E):
        for s in range(al.n_S):
            for z in range(al.n_Z):
                for ap in range(al.n_A):
                    p = k.init_E[e] * k.init_S[s] * k.init_Z[z] * k.init_A[ap]
                    if p:
                        states[((e,), (), (), s, z, ap)] = p
    for _ in range(T):
        nxt = {}
        for (eh, oh, ah, s, z, ap), p0 in states.items():
            e = eh[-1]
            g, b, m, r = al.split_S(s)
            gmr = (g * al.n_M + m) * al.n_R + r
            for o in range(al.n_O):
                p_obs = k.obs[e, ap, o]
                if not p_obs:
                    continue
                for b_new in range(al.n_B):
                    p_bel = k.belief[b, o, b_new]
                    if not p_bel:
                        continue
                    for gmr_new in range(al.n_GMR):
                        p_int = k.internal[gmr, gmr_new]
                        if not p_int:
                            continue
                        g_new, rem = divmod(gmr_new, al.n_M * al.n_R)
                        m_new, r_new = divmod(rem, al.n_R)
                        s_new = al.join_S(g_new, b_new, m_new, r_new)
                        for a in range(al.n_A):
                            p_pol = k.policy[s_new, a]
                            if not p_pol:
                                continue
                            for z_new in range(al.n_Z):
                                p_res = k.resource[z, z_new]
                                if not p_res:
                                    continue
                                for e_new in range(al.n_E):
                                    p_env = k.env[e, a, z_new, e_new]
                                    if not p_env:
                                        continue
                                    key = (eh + (e_new,), oh + (o,), ah + (a,),
                                           s_new, z_new, a)
                                    nxt[key] = nxt.get(key, 0.0) + p0 * p_obs * p_bel * p_int * p_pol * p_res * p_env
        states = nxt
    out = {}
    for (eh, oh, ah, _s, _z, _ap), p in states.items():
        key = (eh, oh, ah)
        out[key] = out.get(key, 0.0) + p
    if abs(sum(out.values()) - 1.0) > 1e-10:
        raise AssertionError("trajectory joint law is not normalized")
    return out


def _execution(model, T: int) -> float:
    joints = truth_step_joints(model, T)
    channels, mask = step_channels_from_esz(model, joints[-1]["ESZ"])
    p_s = joints[-1]["S"]
    e_pi = 0.0
    for s, w_s in enumerate(channels):
        if not mask[s] or p_s[s] <= 0:
            continue
        support = tuple(a for a in range(model.alphabet.n_A)
                        if model.kernels.policy[s, a] > 1e-9)
        e_pi += float(p_s[s]) * empowerment_support(w_s, support)
    return normalize_a_exec(e_pi, n=1, n_A=model.alphabet.n_A)


def evaluate_same_environment_c0(T: int = 3, w_epi: float = 0.2) -> dict:
    if T < 1 or not 0.0 < w_epi < 1.0:
        raise ValueError("T>=1 and 0<w_epi<1 are required")
    z1, z2 = build_same_environment_c0_models()
    per_time_equal = all(np.array_equal(m1, m2) for m1, m2 in
                         zip(truth_marginals(z1, T), truth_marginals(z2, T)))
    joint1, joint2 = trajectory_joint_eoa(z1, T), trajectory_joint_eoa(z2, T)
    trajectory_equal = (joint1.keys() == joint2.keys() and
                        all(abs(joint1[k] - joint2[k]) <= 1e-12 for k in joint1))
    epi1 = float(truth_A_epi_real(z1, T, np.arange(2)).a_epi_real)
    epi2 = float(truth_A_epi_real(z2, T, np.arange(2)).a_epi_real)
    a_org1, a_org2 = float(truth_A_org(z1, T)), float(truth_A_org(z2, T))
    joints = truth_step_joints(z1, T)
    g_marg = joints[-1]["S"].reshape(2, 2, 1, 1).sum(axis=(1, 2, 3))
    u_eff = float(np.dot(g_marg, np.arange(2)))
    goal = truth_A_goal(u_eff, lambda _u: 0.0, [0.0, 1.0])
    if goal.degenerate:
        raise AssertionError("C0-CF-v2 requires a nondegenerate goal channel")
    a_goal = float(goal.point)
    a_exec1, a_exec2 = float(_execution(z1, T)), float(_execution(z2, T))
    a_via = 1.0
    weights = ((1.0 - w_epi) / 3.0, (1.0 - w_epi) / 3.0,
               (1.0 - w_epi) / 3.0, w_epi)
    a1 = float(composite_A(a_via, (a_org1, a_goal, a_exec1, epi1), weights, 1.0))
    a2 = float(composite_A(a_via, (a_org2, a_goal, a_exec2, epi2), weights, 1.0))
    xor = observation_equivalent_xor_witness((0, 1, 0, 1))
    observation_equivalent = (xor["identity_p_y1"] == xor["xor_p_y1"] == 0.5
                              and np.array_equal(xor["identity_passive_action"],
                                                 xor["xor_passive_action"]))
    baseline_positive = all(v > 0.0 for v in (a_via, a_org1, a_goal, a_exec1, epi1))
    criteria = {
        "C1_same_environment_per_time_and_full_trajectory_law": bool(per_time_equal and trajectory_equal),
        "C2_nondegenerate_baseline_and_epistemic_values": bool(
            baseline_positive and abs(epi1 - 1.0) <= 1e-12 and abs(epi2 - 0.5) <= 1e-12),
        "C3_positive_composite_separation": bool(0.0 < a2 < a1),
        "C4_observationally_equivalent_xor_lambda": bool(
            observation_equivalent and xor["identity"].lam == 1.0 and xor["xor"].lam == 0.0
            and xor["identity"].surgery_history == xor["xor"].surgery_history == 1),
    }
    return {
        "T": T, "w_epi": w_epi,
        "behavior_equal_per_time_EOA": bool(per_time_equal),
        "behavior_equal_full_trajectory_EOA": bool(trajectory_equal),
        "n_trajectories": len(joint1),
        "a_via": a_via, "a_org_z1": a_org1, "a_org_z2": a_org2,
        "a_goal": a_goal, "u_eff": u_eff,
        "a_exec_z1": a_exec1, "a_exec_z2": a_exec2,
        "a_epi_z1": epi1, "a_epi_z2": epi2,
        "composite_z1": a1, "composite_z2": a2,
        "xor_identity_lambda": xor["identity"].lam,
        "xor_implanted_lambda": xor["xor"].lam,
        "factual_p_y1_identity": xor["identity_p_y1"],
        "factual_p_y1_xor": xor["xor_p_y1"],
        "criteria": criteria,
        "overall_verdict": "CONFIRMED" if all(criteria.values()) else "REFUTED",
        "evidence_type": "nondegenerate same-environment constructive implementation check; no external validation",
        "lambda_layer": "L1 composite plus auxiliary nondegenerate endorsement SCM; composite-silent at L1",
    }
