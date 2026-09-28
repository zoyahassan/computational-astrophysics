/* Planet moving on the same ellipse as the Kepler I figure. Sun stays at a focus. */
(function () {
  const stage = document.getElementById("ellipse-stage");
  if (!stage) return;

  const canvas = document.createElement("canvas");
  stage.appendChild(canvas);
  const ctx = canvas.getContext("2d");

  // Matches the notebook: start at 1 AU with 0.65 times circular speed.
  const speedFactor = 0.65;
  const apoapsis = 1;
  const a = apoapsis / (2 - speedFactor * speedFactor);
  const periapsis = 2 * a - apoapsis;
  const e = (apoapsis - periapsis) / (apoapsis + periapsis);
  const b = a * Math.sqrt(1 - e * e);
  const centerX = (apoapsis - periapsis) / 2;

  function resize() {
    const width = stage.clientWidth || 640;
    const height = Math.max(420, Math.round(width * 0.85));
    const dpr = window.devicePixelRatio || 1;
    canvas.style.width = width + "px";
    canvas.style.height = height + "px";
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function eccentricAnomaly(meanAnomaly) {
    let E = meanAnomaly;
    for (let i = 0; i < 8; i += 1) {
      E -= (E - e * Math.sin(E) - meanAnomaly) / (1 - e * Math.cos(E));
    }
    return E;
  }

  function planetPosition(fraction) {
    const mean = 2 * Math.PI * fraction;
    const E = eccentricAnomaly(mean);
    const cosE = Math.cos(E);
    const sinE = Math.sin(E);
    const cosTheta = (cosE - e) / (1 - e * cosE);
    const sinTheta = (Math.sqrt(1 - e * e) * sinE) / (1 - e * cosE);
    const radius = (a * (1 - e * e)) / (1 + e * cosTheta);
    return [-radius * cosTheta, radius * sinTheta];
  }

  let start = null;

  function frame(now) {
    if (start === null) start = now;
    const fraction = ((now - start) / 1000 / 12) % 1;
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#070b14";
    ctx.fillRect(0, 0, width, height);

    const cx = width / 2;
    const cy = height / 2 + 8;
    const scale = Math.min(width, height) * 0.72 / (2 * a);

    function screen(x, y) {
      return [cx + (x - centerX) * scale, cy - y * scale];
    }

    ctx.strokeStyle = "#e8eef6";
    ctx.lineWidth = 1.25;
    ctx.beginPath();
    for (let i = 0; i <= 180; i += 1) {
      const [x, y] = planetPosition(i / 180);
      const [sx, sy] = screen(x, y);
      if (i === 0) ctx.moveTo(sx, sy);
      else ctx.lineTo(sx, sy);
    }
    ctx.closePath();
    ctx.stroke();

    const peri = screen(-periapsis, 0);
    const apo = screen(apoapsis, 0);
    const sun = screen(0, 0);
    const empty = screen(2 * centerX, 0);
    const center = screen(centerX, 0);
    const top = screen(centerX, b);

    ctx.strokeStyle = "#c5d0e0";
    ctx.setLineDash([3, 4]);
    ctx.lineWidth = 0.8;
    ctx.beginPath();
    ctx.moveTo(peri[0], peri[1]);
    ctx.lineTo(apo[0], apo[1]);
    ctx.moveTo(center[0], center[1]);
    ctx.lineTo(top[0], top[1]);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.strokeStyle = "#8fbfa8";
    ctx.beginPath();
    ctx.moveTo(center[0], center[1]);
    ctx.lineTo(sun[0], sun[1]);
    ctx.stroke();

    const planet = planetPosition(fraction);
    const p = screen(planet[0], planet[1]);
    ctx.strokeStyle = "rgba(232, 238, 246, 0.7)";
    ctx.beginPath();
    ctx.moveTo(sun[0], sun[1]);
    ctx.lineTo(p[0], p[1]);
    ctx.stroke();

    function dot(point, radius, color, fill) {
      ctx.beginPath();
      ctx.arc(point[0], point[1], radius, 0, 2 * Math.PI);
      if (fill) {
        ctx.fillStyle = color;
        ctx.fill();
      } else {
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.2;
        ctx.stroke();
      }
    }

    dot(sun, 7, "#f0c14a", true);
    dot(empty, 5, "#c5d0e0", false);
    ctx.strokeStyle = "#8fbfa8";
    ctx.lineWidth = 1.4;
    ctx.beginPath();
    ctx.moveTo(center[0] - 6, center[1]);
    ctx.lineTo(center[0] + 6, center[1]);
    ctx.moveTo(center[0], center[1] - 6);
    ctx.lineTo(center[0], center[1] + 6);
    ctx.stroke();
    dot(p, 5.5, "#e07a5f", true);

    ctx.font = "13px 'Source Sans 3', sans-serif";
    ctx.fillStyle = "#e8eef6";
    ctx.textAlign = "center";
    ctx.fillText("periapsis", peri[0], peri[1] - 14);
    ctx.fillText("apoapsis", apo[0], apo[1] - 14);
    ctx.textAlign = "left";
    ctx.fillText("Sun", sun[0] + 10, sun[1] + 4);
    ctx.fillText("center", center[0] + 10, center[1] - 10);
    ctx.fillStyle = "#c5d0e0";
    ctx.font = "12px 'Source Sans 3', sans-serif";
    ctx.fillText("empty focus", empty[0] - 78, empty[1] + 18);

    requestAnimationFrame(frame);
  }

  resize();
  window.addEventListener("resize", resize);
  requestAnimationFrame(frame);
})();
