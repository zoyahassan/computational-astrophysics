"""Newtonian gravity and orbital mechanics (SI units)."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

# SI constants
G = 6.67430e-11  # m^3 kg^-1 s^-2
M_SUN = 1.989e30  # kg
AU = 1.495978707e11  # m
DAY = 86400.0  # s
YEAR = 365.25 * DAY


def gravitational_acceleration(
    position: NDArray[np.floating],
    central_mass: float,
) -> NDArray[np.floating]:
    """
    Acceleration of a test body due to a point mass at the origin.

    a = -G M r / |r|^3
    """
    r = np.asarray(position, dtype=float)
    r_mag = np.linalg.norm(r)
    if r_mag == 0:
        raise ValueError("Position must be non-zero.")
    return -G * central_mass * r / r_mag**3


def specific_energy(
    position: NDArray[np.floating],
    velocity: NDArray[np.floating],
    central_mass: float,
) -> float:
    """Specific orbital energy E/m = v^2/2 - G M / r."""
    r = np.linalg.norm(position)
    v = np.linalg.norm(velocity)
    return 0.5 * v**2 - G * central_mass / r


def specific_angular_momentum(
    position: NDArray[np.floating],
    velocity: NDArray[np.floating],
) -> NDArray[np.floating]:
    """Specific angular momentum vector h = r x v."""
    return np.cross(position, velocity)


def circular_orbital_speed(radius: float, central_mass: float) -> float:
    """Speed for a circular orbit at radius r: v = sqrt(G M / r)."""
    return np.sqrt(G * central_mass / radius)


def escape_speed(radius: float, central_mass: float) -> float:
    """Escape speed at radius r: v_esc = sqrt(2 G M / r)."""
    return np.sqrt(2 * G * central_mass / radius)


def semi_major_axis_from_energy(energy: float, central_mass: float) -> float:
    """
    Semi-major axis for bound orbits (E < 0): a = -G M / (2 E).
    """
    if energy >= 0:
        return np.inf
    return -G * central_mass / (2 * energy)


def eccentricity_from_state(
    position: NDArray[np.floating],
    velocity: NDArray[np.floating],
    central_mass: float,
) -> float:
    """
    Eccentricity from r, v and M (two-body, Sun at origin).

    e = sqrt(1 + 2 E h^2 / (G M)^2) with h = |r x v|.
    """
    e = specific_energy(position, velocity, central_mass)
    h = np.linalg.norm(specific_angular_momentum(position, velocity))
    gm = G * central_mass
    return float(np.sqrt(max(0.0, 1.0 + 2.0 * e * h**2 / gm**2)))


def kepler_period(semi_major_axis: float, central_mass: float) -> float:
    """Orbital period P = 2 pi sqrt(a^3 / (G M))."""
    return 2 * np.pi * np.sqrt(semi_major_axis**3 / (G * central_mass))


# Sidereal period of Earth used in the synodic-period relation, in days.
P_EARTH_DAYS = 365.26


def synodic_period_days(
    sidereal_period_days: float,
    *,
    superior: bool,
    earth_period_days: float = P_EARTH_DAYS,
) -> float:
    """
    Synodic period S from the planet's sidereal period P.

    Superior planets (outside Earth's orbit): 1/S = 1/P_earth - 1/P
    Inferior planets (inside Earth's orbit):  1/S = 1/P - 1/P_earth
    """
    p = sidereal_period_days
    pe = earth_period_days
    inverse = (1.0 / pe - 1.0 / p) if superior else (1.0 / p - 1.0 / pe)
    if inverse <= 0:
        raise ValueError("Sidereal period is on the wrong side of Earth's period.")
    return 1.0 / inverse


def nbody_accelerations(
    positions: NDArray[np.floating],
    masses: NDArray[np.floating],
) -> NDArray[np.floating]:
    """
    Pairwise Newtonian accelerations for N point masses.

    positions: shape (N, 3), masses: shape (N,)
    """
    n = len(masses)
    acc = np.zeros_like(positions)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            r_ij = positions[j] - positions[i]
            dist = np.linalg.norm(r_ij)
            if dist == 0:
                continue
            acc[i] += G * masses[j] * r_ij / dist**3
    return acc


def total_energy_nbody(
    positions: NDArray[np.floating],
    velocities: NDArray[np.floating],
    masses: NDArray[np.floating],
) -> float:
    """Total kinetic + gravitational potential energy of an N-body system."""
    ke = 0.5 * np.sum(masses * np.sum(velocities**2, axis=1))
    pe = 0.0
    n = len(masses)
    for i in range(n):
        for j in range(i + 1, n):
            dist = np.linalg.norm(positions[j] - positions[i])
            pe -= G * masses[i] * masses[j] / dist
    return ke + pe
