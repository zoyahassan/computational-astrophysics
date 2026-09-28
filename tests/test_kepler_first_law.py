"""Kepler's first law: the Sun is a focus of the ellipse."""

import numpy as np

from src.physics import AU, M_SUN, circular_orbital_speed, kepler_period
from src.simulation import integrate_two_body
from src.visualization import focus_geometry


def test_distances_to_both_foci_sum_to_the_long_axis():
    r0 = AU
    speed = 0.65 * circular_orbital_speed(r0, M_SUN)
    history = integrate_two_body(
        np.array([r0, 0.0, 0.0]),
        np.array([0.0, speed, 0.0]),
        M_SUN,
        dt=3600.0,
        n_steps=int(1.3 * kepler_period(0.7 * r0, M_SUN) / 3600.0),
    )
    geometry = focus_geometry(history)
    positions = history.positions[::50, :2]
    distances = np.linalg.norm(positions - geometry["sun"], axis=1) + np.linalg.norm(
        positions - geometry["empty_focus"], axis=1
    )
    long_axis = 2 * geometry["semi_major_axis"]
    assert geometry["eccentricity"] > 0.4
    assert np.max(np.abs(distances - long_axis) / long_axis) < 0.02
