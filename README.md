# Kepler's second law — visual simulation

Computational experiment for *An Introduction to Modern Astrophysics*: **a line from the Sun to a planet sweeps out equal areas in equal times**.

## Physics (short)

**Kepler's second law:** In equal amounts of time, the Sun–planet line sweeps out equal areas.

**Angular momentum (why the law holds):** Gravity pulls toward the Sun; it does not "twist" the orbit. A quantity called **angular momentum** stays nearly constant. In code we write **h** for the specific angular momentum vector:

- **r** — vector from Sun to planet  
- **v** — planet velocity  
- **h = r × v** — a vector whose **length |h|** measures how much the motion wraps around the Sun  

Constant **|h|** means **area per second = |h|/2** is constant, so equal times give equal areas.

**What you should see on an ellipse:** Near the Sun the planet moves faster (thin, long pie slices). Far from the Sun it moves slower (wide, short slices). The **areas** still match if you use the same time step.

## Model

- Sun fixed at the origin, point-mass planet.
- Newtonian gravity: \(\ddot{\mathbf{r}} = -GM\,\mathbf{r}/|\mathbf{r}|^3\).
- **Velocity Verlet** integration (symplectic; good for long orbit runs).
- SI units internally (`AU`, `M_SUN`, `G` in `src/physics.py`).

## Portfolio website

Architecture: [`docs/WEBSITE_ARCHITECTURE.md`](docs/WEBSITE_ARCHITECTURE.md).

```bash
cd website
npm install
npm run render:projects   # executes notebooks → HTML articles
npm run dev               # http://localhost:4321
```

Published projects live in `projects/*/meta.json`. The Kepler notebook stays at `notebooks/kepler_second_law.ipynb`.

## Run simulation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
jupyter notebook notebooks/kepler_second_law.ipynb
```

## Layout

| Path | Role |
|------|------|
| [`src/physics.py`](src/physics.py) | Gravity, constants, angular momentum |
| [`src/simulation.py`](src/simulation.py) | Orbit integrator |
| [`src/kepler_second_law.py`](src/kepler_second_law.py) | Equal-time sectors and swept areas |
| [`src/visualization.py`](src/visualization.py) | Sector plot, area bar chart, speed vs \(r\) |
| [`notebooks/kepler_second_law.ipynb`](notebooks/kepler_second_law.ipynb) | Guided experiment |

## Validation

- Sector areas over one orbital period vs \((|h|/2)\,\Delta t\).
- `tests/test_kepler_second_law.py` — areas uniform within numerical tolerance.
- `tests/test_circular_orbit.py` — integrator sanity (energy and \(|h|\) drift).

## Limitations

- Sun is infinitely massive (two-body reduced problem).
- Swept area uses triangle \((0, \mathbf{r}_i, \mathbf{r}_{i+1})\) over each equal **time** step; small integration timestep keeps this accurate.
- No relativity, drag, or other bodies.

## Reference

Carroll & Ostlie, *An Introduction to Modern Astrophysics* — Kepler's laws and conservation of angular momentum.
