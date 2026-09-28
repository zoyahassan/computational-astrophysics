"""Numerical integrators for gravitational orbits."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from src.physics import (
    AU,
    G,
    M_SUN,
    gravitational_acceleration,
    kepler_period,
    nbody_accelerations,
    semi_major_axis_from_energy,
    specific_energy,
    circular_orbital_speed,
)


@dataclass
class OrbitHistory:
    """Time series from a two-body integration (Sun at origin)."""

    times: NDArray[np.floating]
    positions: NDArray[np.floating]
    velocities: NDArray[np.floating]
    central_mass: float


@dataclass
class NBodyHistory:
    """Time series from an N-body integration."""

    times: NDArray[np.floating]
    positions: NDArray[np.floating]
    velocities: NDArray[np.floating]
    masses: NDArray[np.floating]


def velocity_verlet_step(
    position: NDArray[np.floating],
    velocity: NDArray[np.floating],
    acceleration: NDArray[np.floating],
    dt: float,
    acceleration_fn,
) -> tuple[NDArray[np.floating], NDArray[np.floating], NDArray[np.floating]]:
    """
    One velocity Verlet step with acceleration recomputed at the new position.

    acceleration_fn(r) -> a
    """
    v_half = velocity + 0.5 * dt * acceleration
    r_new = position + dt * v_half
    a_new = acceleration_fn(r_new)
    v_new = v_half + 0.5 * dt * a_new
    return r_new, v_new, a_new


def integrate_two_body(
    initial_position: NDArray[np.floating],
    initial_velocity: NDArray[np.floating],
    central_mass: float,
    dt: float,
    n_steps: int,
) -> OrbitHistory:
    """Integrate test body in fixed central gravity field."""

    def acc_fn(r: NDArray[np.floating]) -> NDArray[np.floating]:
        return gravitational_acceleration(r, central_mass)

    r = np.asarray(initial_position, dtype=float).copy()
    v = np.asarray(initial_velocity, dtype=float).copy()
    a = acc_fn(r)

    times = np.zeros(n_steps + 1)
    positions = np.zeros((n_steps + 1, 3))
    velocities = np.zeros((n_steps + 1, 3))
    positions[0] = r
    velocities[0] = v

    for i in range(n_steps):
        r, v, a = velocity_verlet_step(r, v, a, dt, acc_fn)
        times[i + 1] = (i + 1) * dt
        positions[i + 1] = r
        velocities[i + 1] = v

    return OrbitHistory(times, positions, velocities, central_mass)


def integrate_nbody(
    initial_positions: NDArray[np.floating],
    initial_velocities: NDArray[np.floating],
    masses: NDArray[np.floating],
    dt: float,
    n_steps: int,
) -> NBodyHistory:
    """Integrate N gravitationally interacting point masses (vectorized Verlet)."""

    positions = np.asarray(initial_positions, dtype=float).copy()
    velocities = np.asarray(initial_velocities, dtype=float).copy()
    masses = np.asarray(masses, dtype=float)
    n_bodies = len(masses)

    a = nbody_accelerations(positions, masses)
    times = np.zeros(n_steps + 1)
    pos_hist = np.zeros((n_steps + 1, n_bodies, 3))
    vel_hist = np.zeros((n_steps + 1, n_bodies, 3))
    pos_hist[0] = positions
    vel_hist[0] = velocities

    for i in range(n_steps):
        v_half = velocities + 0.5 * dt * a
        positions = positions + dt * v_half
        a_new = nbody_accelerations(positions, masses)
        velocities = v_half + 0.5 * dt * a_new
        a = a_new
        times[i + 1] = (i + 1) * dt
        pos_hist[i + 1] = positions
        vel_hist[i + 1] = velocities

    return NBodyHistory(times, pos_hist, vel_hist, masses)


MARS_AU = 1.524


@dataclass
class RetrogradeHistory:
    """Earth and Mars heliocentric trajectories and geocentric Mars longitude."""

    times: NDArray[np.floating]
    earth_positions: NDArray[np.floating]
    mars_positions: NDArray[np.floating]
    mars_longitude: NDArray[np.floating]


def simulate_sun_earth_mars_retrograde(
    dt: float,
    n_steps: int,
    mars_initial_angle_rad: float = 0.7,
) -> RetrogradeHistory:
    """
    Earth and Mars as test particles in the Sun's field (fixed M_SUN).

    Used to demonstrate apparent retrograde motion from Earth's frame.
    """
    r_earth = AU
    r_mars = MARS_AU * AU
    v_earth = circular_orbital_speed(r_earth, M_SUN)
    v_mars = circular_orbital_speed(r_mars, M_SUN)

    earth_pos0 = np.array([r_earth, 0.0, 0.0])
    earth_vel0 = np.array([0.0, v_earth, 0.0])

    mars_pos0 = np.array(
        [r_mars * np.cos(mars_initial_angle_rad), r_mars * np.sin(mars_initial_angle_rad), 0.0]
    )
    mars_vel0 = np.array(
        [-v_mars * np.sin(mars_initial_angle_rad), v_mars * np.cos(mars_initial_angle_rad), 0.0]
    )

    earth_hist = integrate_two_body(earth_pos0, earth_vel0, M_SUN, dt, n_steps)
    mars_hist = integrate_two_body(mars_pos0, mars_vel0, M_SUN, dt, n_steps)

    longitudes = np.array(
        [
            geocentric_longitude(mars_hist.positions[i], earth_hist.positions[i])
            for i in range(len(earth_hist.times))
        ]
    )

    return RetrogradeHistory(
        earth_hist.times,
        earth_hist.positions,
        mars_hist.positions,
        longitudes,
    )


def retrograde_mask_from_longitude(longitude_rad: NDArray[np.floating]) -> NDArray[np.bool_]:
    """True where unwrapped longitude decreases (apparent retrograde motion)."""
    unwrapped = np.unwrap(longitude_rad)
    derivative = np.gradient(unwrapped)
    mask = derivative < 0
    mask[0] = False
    return mask


def radial_distances(history: OrbitHistory) -> NDArray[np.floating]:
    return np.linalg.norm(history.positions, axis=1)


def find_periapse_times(
    times: NDArray[np.floating],
    radii: NDArray[np.floating],
) -> NDArray[np.floating]:
    """Times of local minima in |r| (periapses), skipping the first sample."""
    idx = []
    for i in range(1, len(radii) - 1):
        if radii[i] < radii[i - 1] and radii[i] < radii[i + 1]:
            idx.append(i)
    return times[np.array(idx, dtype=int)]


def measure_orbital_period(history: OrbitHistory) -> float | None:
    """Estimate period from successive periapse times; None if not enough data."""
    peri = find_periapse_times(history.times, radial_distances(history))
    if len(peri) < 2:
        return None
    return float(np.mean(np.diff(peri)))


def orbit_elements_from_history(history: OrbitHistory) -> dict[str, float]:
    """Semi-major axis and eccentricity from initial state and peri/apo radii."""
    r = radial_distances(history)
    r_min = float(np.min(r))
    r_max = float(np.max(r))
    a_geom = 0.5 * (r_min + r_max)
    e_geom = (r_max - r_min) / (r_max + r_min) if r_max + r_min > 0 else 0.0

    e0 = specific_energy(history.positions[0], history.velocities[0], history.central_mass)
    a_energy = semi_major_axis_from_energy(e0, history.central_mass)

    return {
        "semi_major_axis_geom": a_geom,
        "semi_major_axis_energy": a_energy,
        "eccentricity_geom": e_geom,
        "period_simulated": measure_orbital_period(history) or np.nan,
        "period_kepler": kepler_period(a_energy, history.central_mass)
        if np.isfinite(a_energy)
        else np.nan,
    }


@dataclass
class KeplerLawSample:
    semi_major_axis: float
    period: float
    central_mass: float


def sample_kepler_third_law(
    central_mass: float,
    base_radius: float,
    speed_factors: NDArray[np.floating],
    dt: float,
    n_steps: int,
) -> list[KeplerLawSample]:
    """
    Run elliptical orbits with tangential speed v = factor * v_circ at base_radius.
    """
    from src.physics import circular_orbital_speed

    v_circ = circular_orbital_speed(base_radius, central_mass)
    pos0 = np.array([base_radius, 0.0, 0.0])
    samples: list[KeplerLawSample] = []

    for factor in speed_factors:
        v0 = np.array([0.0, factor * v_circ, 0.0])
        hist = integrate_two_body(pos0, v0, central_mass, dt, n_steps)
        elems = orbit_elements_from_history(hist)
        period = elems["period_simulated"]
        a = elems["semi_major_axis_energy"]
        if period is None or not np.isfinite(a) or a <= 0:
            continue
        samples.append(KeplerLawSample(a, period, central_mass))

    return samples


def fit_kepler_law(samples: list[KeplerLawSample]) -> tuple[float, float]:
    """
    Linear fit T^2 = slope * a^3. Returns (slope, intercept).

    Theory: slope = 4 pi^2 / (G M).
    """
    if len(samples) < 2:
        raise ValueError("Need at least two bound orbits to fit Kepler's third law.")

    a3 = np.array([s.semi_major_axis**3 for s in samples])
    t2 = np.array([s.period**2 for s in samples])
    coeffs = np.polyfit(a3, t2, 1)
    return float(coeffs[0]), float(coeffs[1])


def theoretical_kepler_slope(central_mass: float) -> float:
    return 4 * np.pi**2 / (G * central_mass)


@dataclass
class OrbitClassificationPoint:
    speed_factor: float
    eccentricity: float
    energy: float
    bound: bool


def classify_orbits_by_speed(
    radius: float,
    central_mass: float,
    speed_factors: NDArray[np.floating],
    dt: float,
    n_steps: int,
) -> list[OrbitClassificationPoint]:
    """Sweep tangential speed as a fraction of circular speed at radius."""
    from src.physics import circular_orbital_speed, eccentricity_from_state

    v_circ = circular_orbital_speed(radius, central_mass)
    pos0 = np.array([radius, 0.0, 0.0])
    points: list[OrbitClassificationPoint] = []

    for factor in speed_factors:
        v0 = np.array([0.0, factor * v_circ, 0.0])
        e = specific_energy(pos0, v0, central_mass)
        ecc = eccentricity_from_state(pos0, v0, central_mass)
        bound = e < 0
        points.append(
            OrbitClassificationPoint(
                speed_factor=float(factor),
                eccentricity=ecc,
                energy=e,
                bound=bound,
            )
        )
    return points


def ecliptic_longitude(position: NDArray[np.floating]) -> float:
    """Longitude in the orbital plane (x-y), radians in (-pi, pi]."""
    return float(np.arctan2(position[1], position[0]))


def geocentric_longitude(
    planet_pos: NDArray[np.floating],
    earth_pos: NDArray[np.floating],
) -> float:
    """Apparent ecliptic longitude of a planet as seen from Earth."""
    rel = planet_pos - earth_pos
    return ecliptic_longitude(rel)
