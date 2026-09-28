"""Kepler's second law: equal areas in equal times."""

import numpy as np

from src.kepler_second_law import areas_in_equal_time_intervals, theoretical_areal_rate
from src.physics import AU, M_SUN, circular_orbital_speed
from src.simulation import integrate_two_body, measure_orbital_period


def test_equal_time_sector_areas_nearly_constant():
    """Elliptical orbit: swept areas over equal Δt should match |h|/2 × Δt."""
    r0 = AU
    v_circ = circular_orbital_speed(r0, M_SUN)
    pos0 = np.array([r0, 0.0, 0.0])
    vel0 = np.array([0.0, 0.72 * v_circ, 0.0])
    dt = 1800.0
    hist = integrate_two_body(pos0, vel0, M_SUN, dt, int(400 * 86400 / dt))
    period = measure_orbital_period(hist)
    assert period is not None

    n_intervals = 12
    t_start = hist.times[0]
    t_end = t_start + period
    areas, _ = areas_in_equal_time_intervals(hist, n_intervals, t_start, t_end)
    areal = theoretical_areal_rate(hist)
    dt_interval = period / n_intervals
    expected = areal * dt_interval

    rel_err = np.abs(areas - expected) / expected
    assert np.max(rel_err) < 0.08
    assert np.std(areas) / np.mean(areas) < 0.06
