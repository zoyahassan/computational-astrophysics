"""Validation tests for two-body circular orbits."""

import numpy as np

from src.physics import (
    AU,
    M_SUN,
    circular_orbital_speed,
    kepler_period,
    specific_angular_momentum,
    specific_energy,
)
from src.simulation import integrate_two_body, measure_orbital_period, orbit_elements_from_history


def test_circular_orbit_constant_radius():
    r0 = AU
    v0 = circular_orbital_speed(r0, M_SUN)
    pos0 = np.array([r0, 0.0, 0.0])
    vel0 = np.array([0.0, v0, 0.0])
    dt = 3600.0
    n_orbits = 2
    t_period = kepler_period(r0, M_SUN)
    n_steps = int(n_orbits * t_period / dt)

    hist = integrate_two_body(pos0, vel0, M_SUN, dt, n_steps)
    radii = np.linalg.norm(hist.positions, axis=1)

    assert np.std(radii) / r0 < 1e-4


def test_energy_and_angular_momentum_near_constant():
    r0 = AU
    v0 = circular_orbital_speed(r0, M_SUN)
    pos0 = np.array([r0, 0.0, 0.0])
    vel0 = np.array([0.0, v0, 0.0])
    dt = 1800.0
    n_steps = 5000

    hist = integrate_two_body(pos0, vel0, M_SUN, dt, n_steps)
    energies = [
        specific_energy(hist.positions[i], hist.velocities[i], M_SUN)
        for i in range(len(hist.times))
    ]
    h_mag = [
        np.linalg.norm(specific_angular_momentum(hist.positions[i], hist.velocities[i]))
        for i in range(len(hist.times))
    ]

    e0 = energies[0]
    h0 = h_mag[0]
    assert abs((energies[-1] - e0) / e0) < 1e-5
    assert abs((h_mag[-1] - h0) / h0) < 1e-5


def test_period_matches_kepler_for_circular_orbit():
    r0 = AU
    v0 = circular_orbital_speed(r0, M_SUN)
    pos0 = np.array([r0, 0.0, 0.0])
    vel0 = np.array([0.0, v0, 0.0])
    dt = 7200.0
    t_analytic = kepler_period(r0, M_SUN)
    n_steps = int(3 * t_analytic / dt)

    hist = integrate_two_body(pos0, vel0, M_SUN, dt, n_steps)
    t_sim = measure_orbital_period(hist)
    assert t_sim is not None
    assert abs(t_sim - t_analytic) / t_analytic < 0.01

    elems = orbit_elements_from_history(hist)
    assert abs(elems["eccentricity_geom"]) < 0.01
