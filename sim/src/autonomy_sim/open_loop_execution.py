"""R17 precommitted open-loop execution-channel guards (nats).

The repaired multi-step execution estimand optimizes over action-sequence
distributions chosen before the horizon, conditional only on S_t and certified
pre-horizon randomness.  Intermediate observations never choose later actions
inside this audit object.  The environment may still have state and feedback;
all intermediate dynamics are marginalized into the supplied sequence kernel.

This module is an exact finite-channel guard, not a closed-loop directed-
information estimator and not external validation.
"""
from __future__ import annotations

import math

import numpy as np

from .empowerment import channel_capacity


def _positive_int(value: int, label: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError(f"{label} must be a positive integer")
    value = int(value)
    if value < 1:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _kernel_matrix(kernels) -> np.ndarray:
    array = np.asarray(kernels, dtype=float)
    if array.ndim != 2 or array.shape[0] < 1 or array.shape[1] < 1:
        raise ValueError("kernels must be a nonempty 2-D row-stochastic matrix")
    if not np.all(np.isfinite(array)) or np.any(array < 0.0):
        raise ValueError("kernels must be finite and nonnegative")
    if not np.allclose(array.sum(axis=1), 1.0, rtol=0.0, atol=1e-12):
        raise ValueError("kernels must be row-normalized")
    return array


def _distribution(probabilities, size: int, label: str) -> np.ndarray:
    array = np.asarray(probabilities, dtype=float)
    if array.shape != (size,):
        raise ValueError(f"{label} shape must be ({size},)")
    if not np.all(np.isfinite(array)) or np.any(array < 0.0):
        raise ValueError(f"{label} must be finite and nonnegative")
    if not math.isclose(float(array.sum()), 1.0, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError(f"{label} must sum to one")
    return array


def sequence_channel_mi_nats(input_dist, kernels) -> float:
    """I(A^n; O_final) for a fixed precommitted open-loop input distribution."""
    kernel = _kernel_matrix(kernels)
    q = _distribution(input_dist, kernel.shape[0], "input_dist")
    output = q @ kernel
    total = 0.0
    for row_index, probability in enumerate(q):
        if probability == 0.0:
            continue
        row = kernel[row_index]
        mask = row > 0.0
        total += float(probability * np.sum(row[mask] * np.log(row[mask] / output[mask])))
    return max(0.0, float(total))


def open_loop_execution_score(kernels, *, n_actions: int, action_alphabet_size: int,
                              allowed_sequences=None, input_dist=None) -> dict:
    """Exact open-loop sequence MI/capacity and normalized execution score.

    ``kernels[i]`` is P(O_final | S_t fixed, do(A^n = sequence_i)), already
    marginalized over intermediate environment/observation dynamics.  If
    ``input_dist`` is supplied it must be a precommitted distribution over the
    candidate sequences; otherwise the finite allowed sequence channel is
    optimized by the existing Blahut--Arimoto/KKT implementation.
    """
    kernel = _kernel_matrix(kernels)
    n_actions = _positive_int(n_actions, "n_actions")
    action_alphabet_size = _positive_int(action_alphabet_size, "action_alphabet_size")
    if action_alphabet_size < 2:
        raise ValueError("action_alphabet_size must be at least two")
    if kernel.shape[0] > action_alphabet_size ** n_actions:
        raise ValueError("more sequence kernels than the declared action alphabet allows")
    if allowed_sequences is None:
        allowed = tuple(range(kernel.shape[0]))
    else:
        allowed = tuple(sorted({int(index) for index in allowed_sequences}))
        if not allowed or allowed[0] < 0 or allowed[-1] >= kernel.shape[0]:
            raise ValueError("allowed_sequences must be a nonempty valid index set")
    subkernel = kernel[list(allowed), :]
    normalizer = n_actions * math.log(action_alphabet_size)
    if input_dist is None:
        if len(allowed) == 1:
            empowerment = 0.0
            q = np.array([1.0])
        else:
            empowerment, q = channel_capacity(subkernel)
        mode = "CAPACITY_OVER_ALLOWED_OPEN_LOOP_SEQUENCES"
    else:
        full_q = _distribution(input_dist, kernel.shape[0], "input_dist")
        if np.any(full_q[np.setdiff1d(np.arange(kernel.shape[0]), allowed)] > 0.0):
            raise ValueError("input_dist puts mass outside allowed_sequences")
        q = full_q[list(allowed)]
        q = q / q.sum()
        empowerment = sequence_channel_mi_nats(q, subkernel)
        mode = "FIXED_PRECOMMITTED_OPEN_LOOP_DISTRIBUTION"
    score = empowerment / normalizer
    if score > 1.0 + 1e-12:
        raise ValueError("open-loop score exceeds its declared normalizer")
    return {
        "protocol": "PRECOMMITTED_OPEN_LOOP_SEQUENCE",
        "mode": mode,
        "n_actions": n_actions,
        "action_alphabet_size": action_alphabet_size,
        "empowerment_nats": float(empowerment),
        "normalizer_nats": float(normalizer),
        "a_exec": min(1.0, float(score)),
        "input_distribution_over_allowed": [float(value) for value in q],
        "allowed_sequences": list(allowed),
        "uses_intermediate_observations": False,
    }


def open_loop_zero_iff_rows_identical(kernels, *, allowed_sequences=None,
                                      tol: float = 1e-12) -> bool:
    """Zero *capacity* over a finite sequence set iff all allowed rows coincide.

    R18 quantifier convention: the capacity mode optimizes over every
    precommitted distribution on the allowed set, so every allowed pure
    sequence can receive positive probability under some admissible Q (its
    point mass).  Zero capacity therefore holds exactly when all sequences
    that can be assigned positive probability by some admissible Q induce the
    same conditional terminal-observation kernel.  For a *fixed* precommitted
    Q the correct statement is support-relative; see
    :func:`open_loop_zero_iff_positive_support_rows_identical`.  A point-mass
    Q has zero MI even when the allowed rows differ.
    """
    kernel = _kernel_matrix(kernels)
    if not math.isfinite(tol) or tol < 0.0:
        raise ValueError("tol must be finite and nonnegative")
    allowed = range(kernel.shape[0]) if allowed_sequences is None else allowed_sequences
    rows = kernel[list(allowed), :]
    return bool(np.all(np.max(np.abs(rows - rows[0]), axis=0) <= tol))


def open_loop_zero_iff_positive_support_rows_identical(kernels, input_dist, *,
                                                       allowed_sequences=None,
                                                       tol: float = 1e-12) -> bool:
    """Fixed-Q zero MI iff all positive-probability sequence rows coincide.

    R18 quantifier convention for the fixed-precommitted-distribution mode:
    sequences outside the support of Q are irrelevant to I_Q(A^n; O_final).
    In particular a point-mass Q always gives zero MI, regardless of how
    different the unused sequence kernels are.
    """
    kernel = _kernel_matrix(kernels)
    if not math.isfinite(tol) or tol < 0.0:
        raise ValueError("tol must be finite and nonnegative")
    q = _distribution(input_dist, kernel.shape[0], "input_dist")
    if allowed_sequences is not None:
        allowed = tuple(sorted({int(index) for index in allowed_sequences}))
        if not allowed or allowed[0] < 0 or allowed[-1] >= kernel.shape[0]:
            raise ValueError("allowed_sequences must be a nonempty valid index set")
        if np.any(q[np.setdiff1d(np.arange(kernel.shape[0]), allowed)] > 0.0):
            raise ValueError("input_dist puts mass outside allowed_sequences")
    support = np.flatnonzero(q > 0.0)
    if support.size == 0:
        raise ValueError("input_dist must have nonempty support")
    rows = kernel[support, :]
    return bool(np.all(np.max(np.abs(rows - rows[0]), axis=0) <= tol))


def memoryless_observation_sequence_kernels(step_channel, *, n_actions: int) -> np.ndarray:
    """Kronecker channel from action tuples to *whole observation sequences*.

    R18 naming convention: this object maps A^n to (O_{t+1},...,O_{t+n}) and
    is the **observation-sequence** channel, not the paper's execution
    estimand, which reads only the terminal observation O_{t+n}.  For a
    two-step BSC with error p the normalized observation-sequence capacity is
    1 - H_b(p)/ln 2, while the terminal-observation capacity is
    (ln 2 - H_b(p))/(2 ln 2); the two objects must not be conflated.  Use
    :func:`memoryless_terminal_observation_kernels` for the latter.
    """
    step = _kernel_matrix(step_channel)
    n_actions = _positive_int(n_actions, "n_actions")
    result = step
    for _ in range(n_actions - 1):
        result = np.kron(result, step)
    return result


# Backward-compatible R17 name; the object is the observation-sequence channel.
memoryless_sequence_kernels = memoryless_observation_sequence_kernels


def memoryless_terminal_observation_kernels(step_channel, *, n_actions: int) -> np.ndarray:
    """Terminal-observation kernels for a memoryless per-step environment.

    R18 convention matching the paper's estimand: when each observation
    O_{t+k} depends only on the concurrent action A_{t+k} through the same
    step channel (no environment state carries action effects forward), the
    marginalized terminal kernel K(o | a^n) = step(o | a_n) depends only on
    the last action.  Stateful environments (e.g. the native benchmark's
    parity SCM) must instead supply their marginalized sequence kernels
    directly; this helper is only the memoryless special case.
    """
    step = _kernel_matrix(step_channel)
    n_actions = _positive_int(n_actions, "n_actions")
    if step.shape[0] != step.shape[1]:
        raise ValueError("memoryless terminal helper requires a square step channel")
    alphabet = step.shape[0]
    rows = []
    for sequence in range(alphabet ** n_actions):
        last_action = sequence % alphabet
        rows.append(step[last_action])
    return np.asarray(rows, dtype=float)


def feedback_copy_counterexample() -> dict:
    """The R17 counterexample to the former ordinary-MI multi-step definition.

    X is a fair exogenous bit, the environment ignores every action,
    O_{t+1}=O_{t+2}=X, A_t=0 after conditioning on S_t, and the reactive second
    action copies the intermediate observation: A_{t+1}=X.  The old ordinary
    conditional MI is ln 2 although no action has any causal effect.
    """
    joint = np.zeros((2, 2, 2, 2))  # axes X, A_t, A_{t+1}, O_{t+2}
    for x in (0, 1):
        joint[x, 0, x, x] = 0.5
    # H(O)=ln2 and H(O|A_t,A_{t+1})=0 because A_{t+1}=O=X.
    old_mi = math.log(2.0)
    kernels = np.full((4, 2), 0.5)  # sequences 00,01,10,11 all give fair O=X
    repaired = open_loop_execution_score(kernels, n_actions=2, action_alphabet_size=2)
    return {
        "joint_axes": ["X", "A_t", "A_t+1", "O_t+2"],
        "joint": joint,
        "old_conditional_mi_nats": old_mi,
        "old_normalized_score": old_mi / (2.0 * math.log(2.0)),
        "open_loop_sequence_kernels": kernels,
        "repaired_open_loop": repaired,
        "environment_ignores_actions": True,
        "reactive_policy_uses_intermediate_observation": True,
    }


def controlling_open_loop_kernels() -> np.ndarray:
    """Positive control: four open-loop binary sequences map to four outcomes."""
    return np.eye(4, dtype=float)
