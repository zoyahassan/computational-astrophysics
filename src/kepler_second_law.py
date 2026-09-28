"""Kepler's second law: equal areas in equal times."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from src.physics import specific_angular_momentum
from src.simulation import OrbitHistory


def swept_area_xy(
    position_a: NDArray[np.floating],
    position_b: NDArray[np.floating],
) -> float:
    """
    Area swept by the radius vector from position_a to position_b (Sun at origin).

    Uses the triangle (0, r_a, r_b) in the orbital plane; valid when the arc
    between the two points does not wrap past periapsis in one step.
    """
    ra = np.asarray(position_a, dtype=float)[:2]
    rb = np.asarray(position_b, dtype=float)[:2]
    return 0.5 * abs(ra[0] * rb[1] - ra[1] * rb[0])


def indices_at_equal_time_steps(
    times: NDArray[np.floating],
    n_intervals: int,
    t_start: float | None = None,
    t_end: float | None = None,
) -> NDArray[np.int_]:
    """Sample indices along a trajectory so each consecutive pair spans equal Δt."""
    t0 = float(times[0] if t_start is None else t_start)
    t1 = float(times[-1] if t_end is None else t_end)
    if t1 <= t0:
        raise ValueError("t_end must be greater than t_start.")

    target_times = np.linspace(t0, t1, n_intervals + 1)
    indices = np.searchsorted(times, target_times, side="left")
    indices = np.clip(indices, 0, len(times) - 1)
    indices[-1] = min(int(np.argmin(np.abs(times - t1))), len(times) - 1)
    return indices.astype(int)


def swept_area_along_path(
    positions: NDArray[np.floating],
    index_start: int,
    index_end: int,
) -> float:
    """Sum of infinitesimal triangles along the integrated path (index_start → index_end)."""
    if index_end <= index_start:
        return 0.0
    total = 0.0
    for j in range(index_start, index_end):
        total += swept_area_xy(positions[j], positions[j + 1])
    return total


def areas_in_equal_time_intervals(
    history: OrbitHistory,
    n_intervals: int,
    t_start: float | None = None,
    t_end: float | None = None,
) -> tuple[NDArray[np.floating], NDArray[np.int_]]:
    """
    Areas swept in n_intervals equal-duration chunks of the simulation.

    Each area is the sum of small triangles along the orbit segment (accurate
    even when the planet moves quickly near periapsis).

    Returns (areas, boundary_indices) marking the start of each equal-time slice.
    """
    idx = indices_at_equal_time_steps(history.times, n_intervals, t_start, t_end)
    areas = np.array(
        [
            swept_area_along_path(history.positions, idx[k], idx[k + 1])
            for k in range(n_intervals)
        ]
    )
    return areas, idx


def theoretical_areal_rate(history: OrbitHistory) -> float:
    """
    Constant areal velocity dA/dt = |h| / 2 (specific angular momentum h = r × v).
    """
    h0 = specific_angular_momentum(history.positions[0], history.velocities[0])
    return 0.5 * np.linalg.norm(h0)
