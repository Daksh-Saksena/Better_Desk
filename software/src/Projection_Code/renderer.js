/**
 * BetterDesk Overlay Renderer
 * ─────────────────────────────────────────────────────────────────────────────
 * Connects to the BetterDesk WebSocket server, maintains a local scene graph,
 * and renders everything at 60 FPS using HTML5 Canvas.
 *
 * Coordinate system: ALL positions are normalized 0.0 – 1.0.
 *   (0, 0) = top-left of the projector area
 *   (1, 1) = bottom-right of the projector area
 *
 * Layer order (ascending z-index):
 *   0  Grid          3  Text
 *   1  Highlights    4  Animations / FX
 *   2  Arrows
 */
const canvas = document.getElementById("overlay");
const ctx = canvas.getContext("2d");
const status = document.getElementById("status");
function resize() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}
resize();
window.addEventListener("resize", resize);
const W = () => canvas.width;
const H = () => canvas.height;
const px = (v) => v * W();
const py = (v) => v * H();
const ps = (v) => v * Math.min(W(), H());
const scene = new Map();
const imgCache = {};
function loadImage(src) {
  if (!imgCache[src]) {
    const img = new Image();
    img.src = src;
    imgCache[src] = img;
  }
  return imgCache[src];
}
function computeAnimatedOpacity(node, t) {
  const dur = (node.animationDuration || 1000) / 1000;
  const phase = (t % dur) / dur;
  switch (node.animation) {
    case "pulse": return 0.45 + 0.55 * Math.abs(Math.sin(phase * Math.PI));
    case "blink": return phase < 0.5 ? 1 : 0;
    case "fade_in": return Math.min(1, (performance.now() - node._born) / (node.animationDuration || 1000));
    case "fade_out": return Math.max(0, 1 - (performance.now() - node._born) / (node.animationDuration || 1000));
    case "glow": return 1;
    default: return 1;
  }
}
function computeAnimatedScale(node, t) {
  const dur = (node.animationDuration || 1000) / 1000;
  const phase = (t % dur) / dur;
  if (node.animation === "scale") return 0.9 + 0.2 * Math.abs(Math.sin(phase * Math.PI));
  return 1;
}
function computeAnimatedRotation(node, t) {
  const dur = (node.animationDuration || 3000) / 1000;
  if (node.animation === "rotation") return (t / dur) * Math.PI * 2;
  return (node.rotation || 0) * Math.PI / 180;
}
function computeGlowRadius(node, t) {
  const dur = (node.animationDuration || 1000) / 1000;
  const phase = (t % dur) / dur;
  const base = node.shadow || 0;
  if (node.animation === "glow" || node.animation === "pulse") {
    return base + 8 + 12 * Math.abs(Math.sin(phase * Math.PI));
  }
  return base;
}
function applyStroke(node) {
  ctx.strokeStyle = node.color || "#00aaff";
  ctx.lineWidth = node.thickness || 2;
}
function applyFill(node) {
  ctx.fillStyle = node.fillColor || "transparent";
}
function applyShadow(node, t) {
  const r = computeGlowRadius(node, t);
  if (r > 0) {
    ctx.shadowColor = node.glow || node.color || "#00aaff";
    ctx.shadowBlur = r;
  } else {
    ctx.shadowBlur = 0;
  }
}
function applyFont(node) {
  const size = node.fontSize || 22;
  const face = node.font || "system-ui, sans-serif";
  ctx.font = `${Math.round(size)}px ${face}`;
}
function drawLine(node, t) {
  ctx.beginPath();
  applyStroke(node);
  applyShadow(node, t);
  ctx.moveTo(px(node.x1), py(node.y1));
  ctx.lineTo(px(node.x2), py(node.y2));
  ctx.stroke();
}
function drawDashedLine(node, t) {
  const dash = (node.dash || [0.01, 0.01]).map(ps);
  ctx.setLineDash(dash);
  drawLine(node, t);
  ctx.setLineDash([]);
}
function drawArrowHead(x, y, angle, size, color) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(angle);
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(-size, -size * 0.5);
  ctx.lineTo(-size, size * 0.5);
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();
  ctx.restore();
}
function drawArrow(node, t) {
  const x1 = px(node.x1), y1 = py(node.y1);
  const x2 = px(node.x2), y2 = py(node.y2);
  const color = node.color || "#ffaa00";
  const thick = node.thickness || 2.5;
  const type = node.arrowType || "straight";
  const hs = thick * 5;
  ctx.save();
  applyStroke(node);
  ctx.strokeStyle = color;
  ctx.lineWidth = thick;
  applyShadow(node, t);
  if (type === "dashed") {
    ctx.setLineDash([ps(0.015), ps(0.01)]);
  }
  let dashOffset = 0;
  if (node.animation === "move") {
    dashOffset = -(performance.now() / 10) % ps(0.05);
    ctx.lineDashOffset = dashOffset;
    ctx.setLineDash([ps(0.015), ps(0.01)]);
  }
  const angle = Math.atan2(y2 - y1, x2 - x1);
  if (type === "curved") {
    const mx = (x1 + x2) / 2 - (y2 - y1) * 0.3;
    const my = (y1 + y2) / 2 + (x2 - x1) * 0.3;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.quadraticCurveTo(mx, my, x2, y2);
    ctx.stroke();
    const curveAngle = Math.atan2(y2 - my, x2 - mx);
    drawArrowHead(x2, y2, curveAngle, hs, color);
    if (node.arrowType === "double") drawArrowHead(x1, y1, Math.atan2(y1 - my, x1 - mx), hs, color);
  } else {
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
    drawArrowHead(x2, y2, angle, hs, color);
    if (type === "double") drawArrowHead(x1, y1, angle + Math.PI, hs, color);
  }
  ctx.setLineDash([]);
  ctx.restore();
}
function drawRect(node, t) {
  const x = px(node.x), y = py(node.y);
  const w = px(node.w), h = py(node.h);
  applyStroke(node);
  applyFill(node);
  applyShadow(node, t);
  ctx.beginPath();
  ctx.rect(x, y, w, h);
  if (node.fillColor) ctx.fill();
  ctx.stroke();
}
function drawRoundedRect(node, t) {
  const x = px(node.x), y = py(node.y);
  const w = px(node.w), h = py(node.h);
  const r = ps(node.radius || 0.01);
  applyStroke(node);
  applyFill(node);
  applyShadow(node, t);
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, r);
  if (node.fillColor) ctx.fill();
  ctx.stroke();
}
function drawCircle(node, t) {
  const cx = px(node.cx), cy = py(node.cy);
  const r = ps(node.r);
  applyStroke(node);
  applyFill(node);
  applyShadow(node, t);
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  if (node.fillColor) ctx.fill();
  ctx.stroke();
}
function drawEllipse(node, t) {
  const cx = px(node.cx), cy = py(node.cy);
  const rx = ps(node.rx), ry = ps(node.ry);
  applyStroke(node);
  applyFill(node);
  applyShadow(node, t);
  ctx.beginPath();
  ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
  if (node.fillColor) ctx.fill();
  ctx.stroke();
}
function drawPolygon(node, t) {
  if (!node.points || node.points.length < 2) return;
  applyStroke(node);
  applyFill(node);
  applyShadow(node, t);
  ctx.beginPath();
  ctx.moveTo(px(node.points[0][0]), py(node.points[0][1]));
  for (let i = 1; i < node.points.length; i++) {
    ctx.lineTo(px(node.points[i][0]), py(node.points[i][1]));
  }
  ctx.closePath();
  if (node.fillColor) ctx.fill();
  ctx.stroke();
}
function drawPath(node, t) {
  if (!node.points || node.points.length < 2) return;
  applyStroke(node);
  applyShadow(node, t);
  ctx.beginPath();
  ctx.moveTo(px(node.points[0][0]), py(node.points[0][1]));
  for (let i = 1; i < node.points.length; i++) {
    ctx.lineTo(px(node.points[i][0]), py(node.points[i][1]));
  }
  ctx.stroke();
}
function drawBezier(node, t) {
  applyStroke(node);
  applyShadow(node, t);
  ctx.beginPath();
  ctx.moveTo(px(node.x1), py(node.y1));
  ctx.bezierCurveTo(px(node.cx1), py(node.cy1), px(node.cx2), py(node.cy2), px(node.x2), py(node.y2));
  ctx.stroke();
}
function drawText(node, t) {
  const x = px(node.x), y = py(node.y);
  const text = node.text || "";
  const color = node.color || "#ffffff";
  const bg = node.fillColor || null;
  const maxW = node.maxWidth ? px(node.maxWidth) : null;
  applyFont(node);
  applyShadow(node, t);
  const words = text.split(" ");
  const lineH = (node.fontSize || 22) * 1.4;
  const lines = [];
  let line = "";
  if (maxW) {
    for (const w of words) {
      const test = line + (line ? " " : "") + w;
      if (ctx.measureText(test).width > maxW && line) {
        lines.push(line);
        line = w;
      } else {
        line = test;
      }
    }
    lines.push(line);
  } else {
    lines.push(text);
  }
  if (bg) {
    const tw = lines.reduce((m, l) => Math.max(m, ctx.measureText(l).width), 0);
    ctx.fillStyle = bg;
    ctx.beginPath();
    ctx.roundRect(x - 8, y - lineH * 0.8, tw + 16, lineH * lines.length + 8, 6);
    ctx.fill();
  }
  ctx.fillStyle = color;
  lines.forEach((l, i) => ctx.fillText(l, x, y + i * lineH));
}
function drawImage(node) {
  if (!node.src) return;
  const img = loadImage(node.src);
  if (!img.complete || img.naturalWidth === 0) return;
  const x = px(node.x), y = py(node.y);
  const w = px(node.w), h = py(node.h);
  ctx.globalAlpha *= (node.opacity ?? 1);
  ctx.drawImage(img, x, y, w, h);
}
function drawGrid(node, t) {
  const cols = node.cols || 10;
  const rows = node.rows || 10;
  ctx.strokeStyle = node.color || "rgba(255,255,255,0.12)";
  ctx.lineWidth = node.thickness || 1;
  applyShadow(node, t);
  for (let i = 0; i <= cols; i++) {
    const x = (i / cols) * W();
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, H());
    ctx.stroke();
  }
  for (let j = 0; j <= rows; j++) {
    const y = (j / rows) * H();
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(W(), y);
    ctx.stroke();
  }
}
function drawCrosshair(node, t) {
  const cx = px(node.x), cy = py(node.y);
  const size = ps(node.size || 0.02);
  ctx.strokeStyle = node.color || "#00ffaa";
  ctx.lineWidth = node.thickness || 1.5;
  applyShadow(node, t);
  ctx.beginPath();
  ctx.moveTo(cx - size, cy); ctx.lineTo(cx + size, cy);
  ctx.moveTo(cx, cy - size); ctx.lineTo(cx, cy + size);
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(cx, cy, size * 0.35, 0, Math.PI * 2);
  ctx.stroke();
}
function drawHighlight(node, t) {
  const x = px(node.x), y = py(node.y);
  const w = px(node.w), h = py(node.h);
  const phase = (t % 1.0);
  const pulsed = 0.5 + 0.5 * Math.abs(Math.sin(phase * Math.PI));
  const color = node.color || "#00aaff";
  const r = ps(0.008);
  ctx.fillStyle = hexToRgba(color, 0.08 * pulsed);
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, r);
  ctx.fill();
  ctx.shadowColor = color;
  ctx.shadowBlur = 10 + 14 * pulsed;
  ctx.strokeStyle = color;
  ctx.lineWidth = 2 + pulsed * 1.5;
  ctx.stroke();
  const ca = ps(0.015);
  ctx.shadowBlur = 0;
  ctx.strokeStyle = color;
  ctx.lineWidth = 3;
  const corners = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]];
  const dirs = [[1, 1], [-1, 1], [-1, -1], [1, -1]];
  corners.forEach(([cx, cy], i) => {
    ctx.beginPath();
    ctx.moveTo(cx + dirs[i][0] * ca, cy);
    ctx.lineTo(cx, cy);
    ctx.lineTo(cx, cy + dirs[i][1] * ca);
    ctx.stroke();
  });
  if (node.label) {
    applyFont({ font: node.font || "system-ui", fontSize: node.fontSize || 18 });
    const tw = ctx.measureText(node.label).width;
    const pad = 8;
    ctx.fillStyle = hexToRgba(color, 0.85);
    ctx.beginPath();
    ctx.roundRect(x, y - 28, tw + pad * 2, 24, 4);
    ctx.fill();
    ctx.fillStyle = "#ffffff";
    ctx.shadowBlur = 0;
    ctx.fillText(node.label, x + pad, y - 10);
  }
}
function drawNode(node, t) {
  ctx.save();
  const opacity = computeAnimatedOpacity(node, t);
  ctx.globalAlpha = (node.opacity ?? 1) * opacity;
  const scale = computeAnimatedScale(node, t);
  if (scale !== 1 || node.animation === "rotation") {
    const cx = node.cx ? px(node.cx) : (node.x != null ? px(node.x + (node.w || 0) / 2) : W() / 2);
    const cy = node.cy ? py(node.cy) : (node.y != null ? py(node.y + (node.h || 0) / 2) : H() / 2);
    const rot = computeAnimatedRotation(node, t);
    ctx.translate(cx, cy);
    ctx.rotate(rot);
    ctx.scale(scale, scale);
    ctx.translate(-cx, -cy);
  } else if (node.rotation) {
    const rot = (node.rotation * Math.PI) / 180;
    const cx = node.cx ? px(node.cx) : W() / 2;
    const cy = node.cy ? py(node.cy) : H() / 2;
    ctx.translate(cx, cy); ctx.rotate(rot); ctx.translate(-cx, -cy);
  }
  switch (node.type) {
    case "line": drawLine(node, t); break;
    case "dashed_line": drawDashedLine(node, t); break;
    case "arrow": drawArrow(node, t); break;
    case "rect": drawRect(node, t); break;
    case "rounded_rect": drawRoundedRect(node, t); break;
    case "circle": drawCircle(node, t); break;
    case "ellipse": drawEllipse(node, t); break;
    case "polygon": drawPolygon(node, t); break;
    case "path": drawPath(node, t); break;
    case "bezier": drawBezier(node, t); break;
    case "text": drawText(node, t); break;
    case "image": drawImage(node); break;
    case "grid": drawGrid(node, t); break;
    case "crosshair": drawCrosshair(node, t); break;
    case "highlight": drawHighlight(node, t); break;
    default: break;
  }
  ctx.restore();
}
function render(now) {
  const t = now / 1000;
  ctx.clearRect(0, 0, W(), H());
  const nodes = [...scene.values()];
  nodes.sort((a, b) => (a.layer ?? 0) - (b.layer ?? 0));
  for (const node of nodes) {
    if (node.visible === false) continue;
    drawNode(node, t);
  }
  requestAnimationFrame(render);
}
requestAnimationFrame(render);
let ws;
function connect() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const url = `${proto}://${location.host}/ws`;
  ws = new WebSocket(url);
  ws.onopen = () => {
    status.textContent = "● Connected";
    status.style.color = "rgba(60,220,120,0.5)";
  };
  ws.onclose = () => {
    status.textContent = "○ Reconnecting…";
    status.style.color = "rgba(255,120,80,0.5)";
    setTimeout(connect, 1500);
  };
  ws.onerror = () => {
    status.textContent = "✕ Error";
    status.style.color = "rgba(255,60,60,0.5)";
  };
  ws.onmessage = (evt) => {
    const msg = JSON.parse(evt.data);
    handleCommand(msg);
  };
}
function handleCommand(msg) {
  switch (msg.cmd) {
    case "add": {
      const node = msg.node;
      node._born = performance.now();
      scene.set(node.id, node);
      break;
    }
    case "update": {
      const node = scene.get(msg.id);
      if (node) Object.assign(node, msg.params);
      break;
    }
    case "remove":
      scene.delete(msg.id);
      break;
    case "clear":
      scene.clear();
      break;
    case "clear_layer":
      scene.forEach((v, k) => { if (v.layer === msg.layer) scene.delete(k); });
      break;
    default:
      console.warn("Unknown overlay cmd:", msg.cmd);
  }
}
connect();
function hexToRgba(hex, alpha) {
  hex = hex.replace("#", "");
  if (hex.length === 3) hex = hex.split("").map(c => c + c).join("");
  const r = parseInt(hex.slice(0, 2), 16);
  const g = parseInt(hex.slice(2, 4), 16);
  const b = parseInt(hex.slice(4, 6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}
