"""Plots for orbit simulations and validation."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
from numpy.typing import NDArray

from src.physics import specific_angular_momentum, specific_energy
from src.simulation import KeplerLawSample, OrbitHistory, NBodyHistory

# Matches the portfolio background so figures sit on the dark site without a white box.
FIGURE_BG = "#070b14"
INK = "#e8eef6"
MUTED = "#c5d0e0"


def apply_dark_style() -> None:
    """Matplotlib defaults for dark notebook figures and the portfolio site."""
    plt.style.use("dark_background")
    plt.rcParams.update(
        {
            "figure.facecolor": FIGURE_BG,
            "axes.facecolor": FIGURE_BG,
            "savefig.facecolor": FIGURE_BG,
            "savefig.edgecolor": FIGURE_BG,
            "axes.edgecolor": MUTED,
            "axes.linewidth": 0.4,
            "xtick.major.width": 0.4,
            "ytick.major.width": 0.4,
            "xtick.major.size": 3,
            "ytick.major.size": 3,
            "axes.labelcolor": INK,
            "axes.titlecolor": "#ffffff",
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "text.color": INK,
            "grid.color": "#243044",
            "legend.facecolor": "#101826",
            "legend.edgecolor": "#2a3548",
            "legend.labelcolor": INK,
            "figure.dpi": 120,
        }
    )


def plot_orbit_plane(
    history: OrbitHistory,
    ax: plt.Axes | None = None,
    label: str = "orbit",
) -> plt.Axes:
    if ax is None:
        _, ax = plt.subplots(figsize=(6, 6))
    x = history.positions[:, 0]
    y = history.positions[:, 1]
    ax.plot(x, y, label=label)
    ax.plot(0, 0, "o", color="gold", markersize=10, label="central body")
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.legend()
    ax.set_title("Orbit in the orbital plane")
    return ax


def plot_orbit_diagnostics(history: OrbitHistory) -> plt.Figure:
    """Radius, specific energy, and |angular momentum| vs time."""
    t = history.times / (86400.0)
    r = np.linalg.norm(history.positions, axis=1)
    energies = [
        specific_energy(history.positions[i], history.velocities[i], history.central_mass)
        for i in range(len(t))
    ]
    h_mag = [
        np.linalg.norm(specific_angular_momentum(history.positions[i], history.velocities[i]))
        for i in range(len(t))
    ]

    fig, axes = plt.subplots(3, 1, figsize=(8, 8), sharex=True)
    axes[0].plot(t, r / 1.495978707e11)
    axes[0].set_ylabel("|r| (AU)")
    axes[0].set_title("Orbital diagnostics")

    axes[1].plot(t, energies)
    axes[1].set_ylabel("specific energy (J/kg)")

    axes[2].plot(t, h_mag)
    axes[2].set_ylabel("|h| (m²/s)")
    axes[2].set_xlabel("time (days)")

    fig.tight_layout()
    return fig


def focus_geometry(history: OrbitHistory) -> dict[str, np.ndarray | float]:
    """
    Center, both foci, and periapsis/apoapsis of a simulated orbit.

    The Sun is fixed at the origin, which is one focus. The empty focus is
    the same distance on the other side of the ellipse's center.
    """
    positions = history.positions[:, :2]
    radii = np.linalg.norm(positions, axis=1)
    periapsis = positions[int(np.argmin(radii))]
    apoapsis = positions[int(np.argmax(radii))]
    center = 0.5 * (periapsis + apoapsis)
    sun = np.zeros(2)
    empty_focus = 2 * center - sun
    semi_major_axis = 0.5 * float(np.linalg.norm(apoapsis - periapsis))
    focus_distance = float(np.linalg.norm(center - sun))
    eccentricity = focus_distance / semi_major_axis if semi_major_axis else 0.0
    return {
        "periapsis": periapsis,
        "apoapsis": apoapsis,
        "center": center,
        "sun": sun,
        "empty_focus": empty_focus,
        "semi_major_axis": semi_major_axis,
        "eccentricity": eccentricity,
    }


def plot_kepler_first_law(history: OrbitHistory) -> plt.Figure:
    """Ellipse with the Sun at one focus and the center marked separately."""
    from src.physics import AU

    apply_dark_style()
    geometry = focus_geometry(history)
    fig, ax = plt.subplots(figsize=(7, 7))
    orbit = history.positions[:, :2] / AU
    ax.plot(orbit[:, 0], orbit[:, 1], color=INK, lw=1.2, label="orbit")

    peri = np.asarray(geometry["periapsis"]) / AU
    apo = np.asarray(geometry["apoapsis"]) / AU
    sun = np.asarray(geometry["sun"]) / AU
    empty = np.asarray(geometry["empty_focus"]) / AU
    center = np.asarray(geometry["center"]) / AU

    major = apo - peri
    major = major / np.linalg.norm(major)
    minor = np.array([-major[1], major[0]])
    b_length = float(geometry["semi_major_axis"]) / AU * np.sqrt(
        1 - float(geometry["eccentricity"]) ** 2
    )
    b_end = center + minor * b_length

    ax.plot([peri[0], apo[0]], [peri[1], apo[1]], color=MUTED, lw=0.7, ls="--")
    ax.plot([center[0], b_end[0]], [center[1], b_end[1]], color=MUTED, lw=0.7, ls="--")
    ax.plot([center[0], sun[0]], [center[1], sun[1]], color="#8fbfa8", lw=0.9)

    ax.plot(sun[0], sun[1], "o", color="#f0c14a", ms=11, zorder=5, label="Sun (one focus)")
    ax.plot(empty[0], empty[1], "o", color=MUTED, ms=7, mfc="none", zorder=5, label="empty focus")
    ax.plot(center[0], center[1], "+", color="#8fbfa8", ms=12, mew=1.4, zorder=5, label="center")

    ax.annotate("periapsis", peri, textcoords="offset points", xytext=(-4, 16), ha="center", color=INK, fontsize=10)
    ax.annotate("apoapsis", apo, textcoords="offset points", xytext=(4, 16), ha="center", color=INK, fontsize=10)
    ax.annotate("$a$", (center + apo) / 2, textcoords="offset points", xytext=(0, 10), ha="center", color=INK, fontsize=12)
    ax.annotate("$b$", (center + b_end) / 2, textcoords="offset points", xytext=(8, 0), va="center", color=INK, fontsize=12)
    ax.annotate("$c$", (center + sun) / 2, textcoords="offset points", xytext=(0, -12), ha="center", color="#8fbfa8", fontsize=12)
    ax.set_aspect("equal", adjustable="box")
    pad = 0.22
    ax.set_xlim(float(min(peri[0], apo[0])) - pad, float(max(peri[0], apo[0])) + pad)
    ax.set_ylim(float(-b_length) - pad, float(b_length) + pad)
    ax.set_xlabel("x (AU)")
    ax.set_ylabel("y (AU)")
    ax.set_title("The Sun is at a focus, not the center")
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.12),
        ncol=2,
        frameon=False,
        fontsize=9,
    )
    fig.tight_layout()
    return fig


def plot_kepler_third_law(samples: list[KeplerLawSample]) -> plt.Figure:
    """
    P² versus a³ for orbits around the Sun.

    In years and AU, Kepler's third law is the straight line P² = a³.
    """
    from src.physics import AU, YEAR

    apply_dark_style()
    a_au = np.array([s.semi_major_axis / AU for s in samples])
    p_yr = np.array([s.period / YEAR for s in samples])
    a3 = a_au**3
    p2 = p_yr**2

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(a3, p2, s=40, zorder=3, label="simulated orbits")
    x_line = np.linspace(float(a3.min()) * 0.9, float(a3.max()) * 1.05, 40)
    slope, intercept = np.polyfit(a3, p2, 1)
    ax.plot(x_line, slope * x_line + intercept, label=f"fit, slope = {slope:.3f}")
    ax.plot(x_line, x_line, "--", label="theory: P² = a³")
    ax.set_xlabel("a³  (AU³)")
    ax.set_ylabel("P²  (years²)")
    ax.set_title("Kepler's third law")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_orbit_classification(
    speed_factors: NDArray[np.floating],
    eccentricities: NDArray[np.floating],
    energies: NDArray[np.floating],
) -> plt.Figure:
    fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    axes[0].plot(speed_factors, eccentricities, "o-")
    axes[0].axvline(1.0, color="gray", ls=":", label="v = v_circ")
    axes[0].axvline(np.sqrt(2), color="gray", ls="--", label="v = v_esc")
    axes[0].set_ylabel("eccentricity e")
    axes[0].legend()
    axes[0].set_title("Orbit type vs initial speed")

    axes[1].plot(speed_factors, energies, "o-")
    axes[1].axhline(0, color="k", lw=0.8)
    axes[1].set_xlabel("v / v_circ")
    axes[1].set_ylabel("specific energy (J/kg)")

    fig.tight_layout()
    return fig


def plot_retrograde_longitude(
    times_days: NDArray[np.floating],
    longitude_deg: NDArray[np.floating],
    retrograde_mask: NDArray[np.bool_],
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(times_days, longitude_deg, lw=0.8)
    if np.any(retrograde_mask):
        ax.scatter(
            times_days[retrograde_mask],
            longitude_deg[retrograde_mask],
            s=8,
            c="crimson",
            label="retrograde (dλ/dt < 0)",
            zorder=3,
        )
    ax.set_xlabel("time (days)")
    ax.set_ylabel("geocentric ecliptic longitude (deg)")
    ax.set_title("Apparent motion of Mars (simplified Sun–Earth–Mars model)")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_nbody_plane(history: NBodyHistory, body_labels: list[str] | None = None) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(7, 7))
    n = len(history.masses)
    if body_labels is None:
        body_labels = [f"body {i}" for i in range(n)]
    for i in range(n):
        ax.plot(
            history.positions[:, i, 0],
            history.positions[:, i, 1],
            label=body_labels[i],
        )
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.legend()
    ax.set_title("N-body trajectories (xy plane)")
    fig.tight_layout()
    return fig


def plot_kepler_second_law_sectors(
    history: OrbitHistory,
    sector_indices: NDArray[np.int_],
    areas: NDArray[np.floating] | None = None,
) -> plt.Figure:
    """
    Color equal-time sectors swept by the radius vector (Kepler's second law).

    Narrow wedges near periapsis and wide wedges near apoapsis should have
    similar area when Δt is fixed.
    """
    apply_dark_style()
    fig, ax = plt.subplots(figsize=(8, 8))
    orbit = history.positions[:, :2]
    ax.plot(orbit[:, 0], orbit[:, 1], color=INK, lw=1, zorder=1)

    n = len(sector_indices) - 1
    cmap = plt.cm.viridis(np.linspace(0.15, 0.85, n))
    patches = []
    for k in range(n):
        i0, i1 = sector_indices[k], sector_indices[k + 1]
        verts = [[0.0, 0.0]] + [orbit[j].tolist() for j in range(i0, i1 + 1)]
        patches.append(Polygon(verts, closed=True))
    collection = PatchCollection(
        patches, facecolors=cmap, edgecolors=MUTED, linewidths=0.25, alpha=0.7
    )
    ax.add_collection(collection)

    ax.plot(0, 0, "o", color="gold", markersize=12, zorder=5)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    title = "Kepler's second law: equal-time sectors (Sun at origin)"
    if areas is not None and len(areas) > 0:
        spread = (areas.max() - areas.min()) / areas.mean() * 100
        title += f"\narea spread ≈ {spread:.1f}% (mean over {len(areas)} intervals)"
    ax.set_title(title)
    fig.tight_layout()
    return fig


def plot_equal_time_areas(
    areas: NDArray[np.floating],
    areal_rate: float,
    dt_interval: float,
) -> plt.Figure:
    """Bar chart of swept area per equal time interval vs theory dA/dt * Δt."""
    apply_dark_style()
    fig, ax = plt.subplots(figsize=(9, 4))
    x = np.arange(len(areas))
    ax.bar(x, areas, color="steelblue", alpha=0.85, label="simulated sector area")
    expected = areal_rate * dt_interval
    ax.axhline(expected, color="crimson", ls="--", lw=2, label=f"|h|/2 × Δt = {expected:.3e} m²")
    ax.set_xlabel("equal-time interval index")
    ax.set_ylabel("swept area (m²)")
    ax.set_title("Equal areas in equal times")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_speed_vs_radius(history: OrbitHistory) -> plt.Figure:
    """Link Kepler II to faster motion at smaller radius (elliptical orbit)."""
    r = np.linalg.norm(history.positions, axis=1) / 1.495978707e11
    speed = np.linalg.norm(history.velocities, axis=1) / 1000.0
    apply_dark_style()
    fig, ax = plt.subplots(figsize=(7, 4))
    sc = ax.scatter(r, speed, c=history.times / 86400.0, cmap="plasma", s=8, alpha=0.7)
    ax.set_xlabel("|r| (AU)")
    ax.set_ylabel("|v| (km/s)")
    ax.set_title("Speed increases near periapsis (smaller r)")
    fig.colorbar(sc, ax=ax, label="time (days)")
    fig.tight_layout()
    return fig


def plot_energy_drift_nbody(
    times: NDArray[np.floating],
    energies: NDArray[np.floating],
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8, 3))
    rel = (energies - energies[0]) / abs(energies[0]) if energies[0] != 0 else energies
    ax.plot(times / 86400.0, rel)
    ax.set_xlabel("time (days)")
    ax.set_ylabel("ΔE / E₀")
    ax.set_title("Total energy drift (N-body)")
    fig.tight_layout()
    return fig
