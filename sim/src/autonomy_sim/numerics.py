"""Shared numerical boundary discipline for unit-interval channel measures.

Only round-off sized excursions are clipped.  Larger excursions and non-finite
values are evidence of an implementation/model error and remain fail-closed.
Every clipping event emits :class:`NumericalBoundaryWarning` so batch drivers
can capture it in their logs; clipping is never silent.
"""
from __future__ import annotations

import math
import warnings

import numpy as np

UNIT_INTERVAL_TOL = 1e-9


class NumericalBoundaryWarning(RuntimeWarning):
    """A unit-interval value was clipped within the registered tolerance."""


def clip_unit_value(value: float, *, tol: float = UNIT_INTERVAL_TOL,
                    label: str = "component") -> float:
    """Return a scalar clipped to [0, 1] under the shared tolerance contract."""
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite, got {value}")
    if 0.0 <= value <= 1.0:
        return value
    if value < 0.0 and -value <= tol:
        warnings.warn(f"{label}={value:.17g} clipped to 0 within tol={tol}",
                      NumericalBoundaryWarning, stacklevel=2)
        return 0.0
    if value > 1.0 and value - 1.0 <= tol:
        warnings.warn(f"{label}={value:.17g} clipped to 1 within tol={tol}",
                      NumericalBoundaryWarning, stacklevel=2)
        return 1.0
    raise ValueError(f"{label} outside [0,1] beyond tol={tol}: {value:.17g}")


def clip_unit_interval(values, *, tol: float = UNIT_INTERVAL_TOL,
                       label: str = "components") -> tuple:
    """Vector-shaped public wrapper returning a tuple of validated scalars."""
    array = np.asarray(values, dtype=float)
    if array.ndim != 1:
        raise ValueError(f"{label} must be one-dimensional, got {array.shape}")
    return tuple(clip_unit_value(v, tol=tol, label=f"{label}[{i}]")
                 for i, v in enumerate(array))
