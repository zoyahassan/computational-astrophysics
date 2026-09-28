/* Apparent path of Mars against the stars: east, then west, then east again. */
(function () {
  const stage = document.getElementById("sky-stage");
  if (!stage) return;

  const canvas = document.createElement("canvas");
  stage.appendChild(canvas);
  const ctx = canvas.getContext("2d");

  const stars = Array.from({ length: 70 }, (_, i) => ({
    x: ((i * 47) % 100) / 100,
    y: ((i * 29) % 100) / 100,
    r: i % 5 === 0 ? 1.6 : 1,
  }));

  function resize() {
    const width = stage.clientWidth || 640;
    const height = Math.max(280, Math.round(width * 0.48));
    const dpr = window.devicePixelRatio || 1;
    canvas.style.width = width + "px";
    canvas.style.height = height + "px";
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function eastCoord(u) {
    return u + 0.28 * Math.sin(2 * Math.PI * u);
  }

  function northCoord(u) {
    return 0.22 * Math.sin(2 * Math.PI * u);
  }

  function movingWest(u) {
    const du = 0.002;
    return eastCoord(u + du) < eastCoord(u);
  }

  let start = null;

  function frame(now) {
    if (start === null) start = now;
    const u = ((now - start) / 1000 / 18) % 1;
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#070b14";
    ctx.fillRect(0, 0, width, height);

    for (const star of stars) {
      ctx.fillStyle = "rgba(232, 238, 246, 0.75)";
      ctx.beginPath();
      ctx.arc(star.x * width, 36 + star.y * (height - 80), star.r, 0, 2 * Math.PI);
      ctx.fill();
    }

    const left = 36;
    const right = width - 36;
    const midY = height * 0.52;

    function toScreen(t) {
      const east = eastCoord(t);
      const eastMin = -0.05;
      const eastMax = 1.05;
      const x = right - ((east - eastMin) / (eastMax - eastMin)) * (right - left);
      const y = midY - northCoord(t) * height * 0.9;
      return [x, y];
    }

    ctx.strokeStyle = "rgba(197, 208, 224, 0.35)";
    ctx.lineWidth = 1.25;
    ctx.beginPath();
    for (let t = 0; t <= 1.001; t += 0.01) {
      const [x, y] = toScreen(t);
      if (t === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    const [x, y] = toScreen(u);
    const west = movingWest(u);
    ctx.fillStyle = west ? "#e85d4c" : "#e07a5f";
    ctx.beginPath();
    ctx.arc(x, y, 6, 0, 2 * Math.PI);
    ctx.fill();

    ctx.font = "13px 'Source Sans 3', sans-serif";
    ctx.fillStyle = "#c5d0e0";
    ctx.fillText("east", left, 22);
    ctx.textAlign = "right";
    ctx.fillText("west", right, 22);
    ctx.textAlign = "left";

    ctx.font = "600 15px 'Outfit', sans-serif";
    ctx.fillStyle = west ? "#e85d4c" : "#8fbfa8";
    ctx.fillText(west ? "Westward — retrograde" : "Eastward", left, height - 18);

    requestAnimationFrame(frame);
  }

  resize();
  window.addEventListener("resize", resize);
  requestAnimationFrame(frame);
})();

/* Earth and Mars: lines of sight swing backward near opposition. */
(function () {
  const stage = document.getElementById("retrograde-stage");
  if (!stage) return;

  const P_EARTH = 365.26;
  const P_MARS = 686.98;
  const R_MARS = 1.524;
  const WINDOW = 110;

  const canvas = document.createElement("canvas");
  stage.appendChild(canvas);
  const ctx = canvas.getContext("2d");

  function resize() {
    const width = stage.clientWidth || 640;
    const height = Math.max(420, Math.round(width * 0.72));
    const dpr = window.devicePixelRatio || 1;
    canvas.style.width = width + "px";
    canvas.style.height = height + "px";
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function body(t, period, radius) {
    const angle = (2 * Math.PI * t) / period;
    return [radius * Math.cos(angle), radius * Math.sin(angle)];
  }

  function sightAngle(earth, mars) {
    return Math.atan2(mars[1] - earth[1], mars[0] - earth[0]);
  }

  let start = null;

  function frame(now) {
    if (start === null) start = now;
    const elapsed = (now - start) / 1000;
    const span = 2 * WINDOW;
    const day = -WINDOW + ((elapsed % 24) / 24) * span;

    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#070b14";
    ctx.fillRect(0, 0, width, height);

    const captionH = 56;
    const cx = width / 2;
    const cy = (height - captionH) / 2;
    const scale = Math.min(width * 0.42, (height - captionH) * 0.42) / R_MARS;

    function toScreen(p) {
      return [cx + p[0] * scale, cy - p[1] * scale];
    }

    ctx.strokeStyle = "rgba(126, 184, 201, 0.35)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(cx, cy, scale, 0, 2 * Math.PI);
    ctx.stroke();

    ctx.strokeStyle = "rgba(208, 138, 106, 0.4)";
    ctx.beginPath();
    ctx.arc(cx, cy, R_MARS * scale, 0, 2 * Math.PI);
    ctx.stroke();

    const samples = [];
    for (let t = -WINDOW; t <= day; t += 2) {
      const earth = body(t, P_EARTH, 1);
      const mars = body(t, P_MARS, R_MARS);
      samples.push({ t, earth, mars, angle: sightAngle(earth, mars) });
    }

    let retrograde = false;
    if (samples.length > 2) {
      const a0 = samples[samples.length - 2].angle;
      const a1 = samples[samples.length - 1].angle;
      let delta = a1 - a0;
      if (delta > Math.PI) delta -= 2 * Math.PI;
      if (delta < -Math.PI) delta += 2 * Math.PI;
      retrograde = delta < 0;
    }

    ctx.lineWidth = 1;
    for (let i = 0; i < samples.length; i += 3) {
      const s = samples[i];
      const e = toScreen(s.earth);
      const m = toScreen(s.mars);
      ctx.strokeStyle = "rgba(197, 208, 224, 0.13)";
      ctx.beginPath();
      ctx.moveTo(e[0], e[1]);
      ctx.lineTo(m[0], m[1]);
      ctx.stroke();
    }

    const earth = body(day, P_EARTH, 1);
    const mars = body(day, P_MARS, R_MARS);
    const e = toScreen(earth);
    const m = toScreen(mars);

    ctx.strokeStyle = retrograde ? "#e85d4c" : "#e8eef6";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(e[0], e[1]);
    ctx.lineTo(m[0], m[1]);
    ctx.stroke();

    ctx.fillStyle = "#f0c14a";
    ctx.beginPath();
    ctx.arc(cx, cy, 7, 0, 2 * Math.PI);
    ctx.fill();

    ctx.fillStyle = "#9fd0e0";
    ctx.beginPath();
    ctx.arc(e[0], e[1], 5, 0, 2 * Math.PI);
    ctx.fill();

    ctx.fillStyle = "#e07a5f";
    ctx.beginPath();
    ctx.arc(m[0], m[1], 5, 0, 2 * Math.PI);
    ctx.fill();

    ctx.font = "13px 'Source Sans 3', sans-serif";
    ctx.fillStyle = "#c5d0e0";
    ctx.fillText("Sun", cx + 10, cy + 4);
    ctx.fillText("Earth", e[0] + 8, e[1] - 8);
    ctx.fillText("Mars", m[0] + 8, m[1] - 8);

    ctx.fillStyle = retrograde ? "#e85d4c" : "#8fbfa8";
    ctx.font = "600 15px 'Outfit', sans-serif";
    const label = retrograde ? "Retrograde" : "Prograde";
    ctx.fillText(label, 24, height - 28);
    ctx.font = "13px 'Source Sans 3', sans-serif";
    ctx.fillStyle = "#c5d0e0";
    ctx.fillText("line of sight from Earth to Mars", 24, height - 48);

    requestAnimationFrame(frame);
  }

  resize();
  window.addEventListener("resize", resize);
  requestAnimationFrame(frame);
})();
