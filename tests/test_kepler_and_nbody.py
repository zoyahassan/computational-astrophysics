"""Kepler third law fit and N-body energy drift."""

import numpy as np

from src.physics import AU, M_SUN, total_energy_nbody
from src.simulation import (
    fit_kepler_law,
    integrate_nbody,
    sample_kepler_third_law,
    theoretical_kepler_slope,
)


def test_kepler_third_law_slope():
    factors = np.linspace(0.85, 0.98, 6)
    dt = 6 * 3600.0
    n_steps = int(2 * 365.25 * 86400 / dt)
    samples = sample_kepler_third_law(M_SUN, AU, factors, dt, n_steps)
    assert len(samples) >= 3
    slope, _ = fit_kepler_law(samples)
    theory = theoretical_kepler_slope(M_SUN)
    assert abs(slope - theory) / theory < 0.05


def test_nbody_two_planets_bound_energy_drift_small():
    """Sun + two light planets: total energy should drift slowly with Verlet."""
    m_sun = M_SUN
    m_planet = 3e-6 * M_SUN
    masses = np.array([m_sun, m_planet, m_planet])

    r1 = AU
    r2 = 1.5 * AU
    v1 = np.sqrt(6.67430e-11 * m_sun / r1)
    v2 = np.sqrt(6.67430e-11 * m_sun / r2)

    positions = np.array([[0, 0, 0], [r1, 0, 0], [0, r2, 0]], dtype=float)
    velocities = np.array([[0, 0, 0], [0, v1, 0], [-v2, 0, 0]], dtype=float)

    dt = 3600.0
    n_steps = 2000
    hist = integrate_nbody(positions, velocities, masses, dt, n_steps)

    energies = [
        total_energy_nbody(hist.positions[i], hist.velocities[i], hist.masses)
        for i in range(len(hist.times))
    ]
    rel_drift = abs(energies[-1] - energies[0]) / abs(energies[0])
    assert rel_drift < 0.01
