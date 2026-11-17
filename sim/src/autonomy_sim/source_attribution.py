"""Exact finite-binary directed-information source attribution guards.

The routines in this module enumerate a supplied joint law; they do not sample,
fit, or externally validate a model.  Every information quantity whose name
ends in ``_nats`` uses natural logarithms.  Use :func:`nats_to_bits` when bits
are required.

Sequence-joint layout
---------------------
For ``V`` variables and horizon ``T``, a law has shape ``(2,) * (V * T)`` and
variable-major axes::

    (variable_0 at t=1, ..., variable_0 at t=T,
     variable_1 at t=1, ..., variable_1 at t=T, ...).

Time arguments in the implementation are zero-based, while the formulas below
use one-based notation.  For one source ``X``, conditioning sources ``Z``, and
action ``A``, ordered residual directed information is

``I(X^T -> A^T || Z^T)
  = sum_t I(X^t; A_t | A^(t-1), Z^t)``.

For multiple source variables, ``X^t`` contains *every* selected source's
history through ``t``.  All irrelevant axes, including future axes, are summed
out of the original joint law separately at every time step.  In particular,
histories are never obtained by multiplying one-step marginals or by dropping
a conditioning variable before its history has been marginalized.

The chain functions implement the causally conditioned chain rule.  The
optional Shapley-order average is only an order-sensitivity descriptor, not a
causal/PID-identified unique decomposition.  These are exact model guards, not
external validation of autonomy or of any real-world construct.
"""
from __future__ import annotations

import itertools
import math
import numbers
import operator
from collections.abc import Iterable

import numpy as np

__all__ = [
    "LN_2",
    "entropy_nats",
    "flow_share",
    "joint_directed_information_nats",
    "nats_to_bits",
    "ordered_attribution_nats",
    "ordered_residual_di_nats",
    "shapley_order_average_nats",
    "validate_binary_sequence_joint",
]

LN_2 = math.log(2.0)
_NORMALIZATION_ATOL = 1e-12
_ROUND_OFF_ATOL = 1e-12


def _validate_probability(distribution, *, expected_shape=None) -> np.ndarray:
    """Return a float array only after fail-closed probability checks."""
    try:
        array = np.asarray(distribution, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("distribution must be a real numeric array") from exc
    if array.size == 0:
        raise ValueError("distribution must be nonempty")
    if expected_shape is not None and array.shape != expected_shape:
        raise ValueError(
            f"distribution has shape {array.shape}; expected {expected_shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError("distribution entries must all be finite")
    if np.any(array < 0.0):
        raise ValueError("distribution entries must all be nonnegative")
    total = math.fsum(float(value) for value in array.ravel())
    if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=_NORMALIZATION_ATOL):
        raise ValueError(f"distribution must be normalized to 1, got sum {total!r}")
    return array


def _validate_horizon(horizon: int) -> int:
    if isinstance(horizon, (bool, np.bool_)) or not isinstance(horizon, numbers.Integral):
        raise ValueError("horizon must be a positive integer")
    horizon = int(horizon)
    if horizon <= 0:
        raise ValueError("horizon must be a positive integer")
    return horizon


def validate_binary_sequence_joint(joint, horizon: int, *,
                                   n_variables: int | None = None) -> np.ndarray:
    """Validate and return a finite binary variable-major sequence-joint law.

    No silent normalization, clipping, reshaping, or axis transposition is
    performed.  Supplying ``n_variables`` makes the expected shape fully
    explicit; otherwise it is inferred only after checking divisibility of the
    number of axes by ``horizon``.
    """
    horizon = _validate_horizon(horizon)
    try:
        array = np.asarray(joint, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("joint must be a real numeric array") from exc
    if n_variables is not None:
        if (isinstance(n_variables, (bool, np.bool_))
                or not isinstance(n_variables, numbers.Integral)):
            raise ValueError("n_variables must be an integer of at least two")
        n_variables = int(n_variables)
        if n_variables < 2:
            raise ValueError("n_variables must be an integer of at least two")
        expected_shape = (2,) * (n_variables * horizon)
        return _validate_probability(array, expected_shape=expected_shape)
    if array.ndim == 0 or array.ndim % horizon:
        raise ValueError(
            "joint axis count must be a nonzero multiple of horizon for "
            "variable-major binary sequence layout")
    inferred = array.ndim // horizon
    if inferred < 2:
        raise ValueError("a sequence joint must contain at least two variables")
    expected_shape = (2,) * array.ndim
    return _validate_probability(array, expected_shape=expected_shape)


def _index(value, *, label: str) -> int:
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{label} must be an integer variable index")
    try:
        return operator.index(value)
    except TypeError as exc:
        raise ValueError(f"{label} must be an integer variable index") from exc


def _variable_indices(values: Iterable[int], *, label: str,
                      allow_empty: bool = False) -> tuple[int, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{label} must be an iterable of integer variable indices")
    try:
        raw = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{label} must be an iterable of integer variable indices") from exc
    if not raw and not allow_empty:
        raise ValueError(f"{label} must not be empty")
    result = tuple(_index(value, label=label) for value in raw)
    if len(set(result)) != len(result):
        raise ValueError(f"{label} must not contain duplicate variable indices")
    return result


def _check_variables(n_variables: int, action: int, sources: Iterable[int],
                     conditioning: Iterable[int] = ()) -> tuple[int, tuple[int, ...], tuple[int, ...]]:
    action = _index(action, label="action")
    sources = _variable_indices(sources, label="sources")
    conditioning = _variable_indices(conditioning, label="conditioning", allow_empty=True)
    if not 0 <= action < n_variables:
        raise ValueError("action variable index is out of range")
    if any(not 0 <= source < n_variables for source in sources):
        raise ValueError("source variable index is out of range")
    if any(not 0 <= variable < n_variables for variable in conditioning):
        raise ValueError("conditioning variable index is out of range")
    if action in sources or action in conditioning:
        raise ValueError("action cannot also be a source or conditioning variable")
    if set(sources) & set(conditioning):
        raise ValueError("sources and conditioning variables must be disjoint")
    return action, sources, conditioning


def _entropy_unchecked(probability: np.ndarray) -> float:
    # Marginals produced by exact array summation remain normalized.  fsum
    # avoids accumulation-order loss when many trajectory atoms are present.
    return math.fsum(
        -float(value) * math.log(float(value))
        for value in probability.ravel() if value > 0.0)


def entropy_nats(distribution) -> float:
    """Entropy of a validated finite discrete distribution, in nats."""
    return _entropy_unchecked(_validate_probability(distribution))


def _marginal(joint: np.ndarray, axes: tuple[int, ...]) -> np.ndarray:
    """Marginalize *to* ``axes`` while preserving their original axis order."""
    summed = tuple(axis for axis in range(joint.ndim) if axis not in axes)
    return joint.sum(axis=summed) if summed else joint


def _marginal_entropy(joint: np.ndarray, axes: tuple[int, ...]) -> float:
    if not axes:
        return 0.0
    return _entropy_unchecked(np.asarray(_marginal(joint, axes)))


def _conditional_mi_nats(joint: np.ndarray, x_axes: tuple[int, ...],
                         y_axes: tuple[int, ...],
                         z_axes: tuple[int, ...]) -> float:
    """I(X;Y|Z) from entropies of full-joint marginals (never product histories)."""
    if not x_axes or not y_axes or set(x_axes) & set(y_axes):
        raise ValueError("X and Y axis sets must be nonempty and disjoint")
    if set(z_axes) & (set(x_axes) | set(y_axes)):
        raise ValueError("conditioning axes must be disjoint from X and Y")
    xz = tuple(sorted(x_axes + z_axes))
    yz = tuple(sorted(y_axes + z_axes))
    xyz = tuple(sorted(x_axes + y_axes + z_axes))
    value = math.fsum((
        _marginal_entropy(joint, xz),
        _marginal_entropy(joint, yz),
        -_marginal_entropy(joint, z_axes),
        -_marginal_entropy(joint, xyz),
    ))
    # CMI is nonnegative mathematically.  Remove only a negative floating
    # cancellation residue; a materially negative value indicates a defect.
    if value < 0.0:
        if value < -_ROUND_OFF_ATOL:
            raise ArithmeticError(f"conditional mutual information is negative: {value!r}")
        return 0.0
    return value


def _prefix_axes(variables: tuple[int, ...], time: int,
                 horizon: int) -> tuple[int, ...]:
    """Axes for all selected variables' histories through zero-based ``time``."""
    return tuple(variable * horizon + past
                 for variable in variables for past in range(time + 1))


def _directed_information_nats(joint: np.ndarray, horizon: int,
                               sources: tuple[int, ...], action: int,
                               conditioning: tuple[int, ...]) -> float:
    terms = []
    for time in range(horizon):
        x_axes = _prefix_axes(sources, time, horizon)
        z_axes = _prefix_axes(conditioning, time, horizon)
        action_history = tuple(action * horizon + past for past in range(time))
        current_action = (action * horizon + time,)
        terms.append(_conditional_mi_nats(
            joint, x_axes, current_action, action_history + z_axes))
    return math.fsum(terms)


def ordered_residual_di_nats(joint, *, horizon: int, source: int, action: int,
                             condition_on: Iterable[int] = ()) -> float:
    """Return ``I(X^T -> A^T || Z^T)`` in nats by exact joint enumeration.

    ``source`` is one variable index, ``condition_on`` contains the preceding
    sources ``Z`` in an attribution chain, and ``action`` is the action
    variable index.  Variables absent from all three arguments are marginal
    variables and are correctly summed out at each time step.
    """
    horizon = _validate_horizon(horizon)
    joint = validate_binary_sequence_joint(joint, horizon)
    n_variables = joint.ndim // horizon
    source = _index(source, label="source")
    action, sources, conditioning = _check_variables(
        n_variables, action, (source,), condition_on)
    return _directed_information_nats(joint, horizon, sources, action, conditioning)


def ordered_attribution_nats(joint, *, horizon: int, order: Iterable[int],
                             action: int) -> tuple[float, ...]:
    """Residual source flows for ``order``, returned in that same order, in nats.

    At stage ``k``, the preceding sources are exactly the conditioning set.
    Their sum equals :func:`joint_directed_information_nats` for the same set
    of sources, regardless of chain order (up to floating-point round-off).
    """
    horizon = _validate_horizon(horizon)
    joint = validate_binary_sequence_joint(joint, horizon)
    n_variables = joint.ndim // horizon
    action, order, _ = _check_variables(n_variables, action, order)
    flows = []
    preceding: list[int] = []
    for source in order:
        flows.append(_directed_information_nats(
            joint, horizon, (source,), action, tuple(preceding)))
        preceding.append(source)
    return tuple(flows)


def joint_directed_information_nats(joint, *, horizon: int,
                                    sources: Iterable[int], action: int) -> float:
    """Return joint ``I(X_1,...,X_k -> A)`` in nats, independently of any chain sum.

    This evaluates the grouped-source definition directly.  It does not call
    :func:`ordered_attribution_nats`, so comparing the two checks the chain
    equality rather than merely repeating one computation.
    """
    horizon = _validate_horizon(horizon)
    joint = validate_binary_sequence_joint(joint, horizon)
    n_variables = joint.ndim // horizon
    action, sources, _ = _check_variables(n_variables, action, sources)
    return _directed_information_nats(joint, horizon, sources, action, ())


def shapley_order_average_nats(joint, *, horizon: int, sources: Iterable[int],
                               action: int) -> dict[int, float]:
    """Average each source's residual flow over every source order, in nats.

    This optional average is an **order-sensitivity descriptor only**.  It is
    not a causal attribution theorem, not a partial-information decomposition,
    and not a uniquely identified causal/PID decomposition.
    """
    horizon = _validate_horizon(horizon)
    joint = validate_binary_sequence_joint(joint, horizon)
    n_variables = joint.ndim // horizon
    action, sources, _ = _check_variables(n_variables, action, sources)
    accumulated = {source: [] for source in sources}
    for order in itertools.permutations(sources):
        # The law has already been validated, but using the public chain API
        # here keeps the descriptor exactly aligned with ordered attribution.
        flows = ordered_attribution_nats(
            joint, horizon=horizon, order=order, action=action)
        for source, flow in zip(order, flows):
            accumulated[source].append(flow)
    return {source: math.fsum(accumulated[source]) / len(accumulated[source])
            for source in sources}


def flow_share(part: float, total: float) -> float:
    """Return a well-posed nonnegative ``part / total`` flow share.

    A zero denominator is a 0/0 decomposition and is rejected rather than
    assigned a conventional autonomy value.
    """
    part, total = float(part), float(total)
    if not math.isfinite(part) or not math.isfinite(total):
        raise ValueError("part and total must be finite")
    if part < 0.0 or total <= 0.0:
        raise ValueError("part must be nonnegative and total must be positive")
    if part > total + _ROUND_OFF_ATOL:
        raise ValueError("part cannot exceed total in a source-flow share")
    ratio = part / total
    if ratio > 1.0 and ratio <= 1.0 + _ROUND_OFF_ATOL:
        return 1.0
    return ratio


def nats_to_bits(value: float) -> float:
    """Convert an information quantity from nats to bits (divide by ln 2)."""
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("information value must be finite")
    return value / LN_2
