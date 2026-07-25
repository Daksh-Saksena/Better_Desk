"""
overlay_api.py
Public-facing API for the BetterDesk Overlay Engine.
Import this from detector.py or any other subsystem.

Usage:
    from overlay import api as overlay
    overlay.start()
    id = overlay.highlight_bbox((0.2, 0.3, 0.5, 0.6), label="Arduino")
    overlay.draw_text(0.5, 0.1, "Place Motor Here")
    overlay.remove(id)
"""
from .overlay_manager import overlay
from . import server as _server

def start(port: int = 8000):
    """Start the overlay WebSocket server in a background thread."""
    _server.start(port=port)

# ── Scene management ────────────────────────────────────────────────────────

def clear():
    overlay.clear()

def clear_layer(layer: int):
    overlay.clear_layer(layer)

def remove(id_: str):
    overlay.remove(id_)

def remove_all():
    overlay.remove_all()

def update(id_: str, **kwargs):
    overlay.update(id_, **kwargs)

# ── Primitives ───────────────────────────────────────────────────────────────

def draw_line(x1, y1, x2, y2, **kw) -> str:
    return overlay.draw_line(x1, y1, x2, y2, **kw)

def draw_arrow(start: tuple, end: tuple, arrow_type="straight", **kw) -> str:
    return overlay.draw_arrow(start, end, arrow_type=arrow_type, **kw)

def draw_rectangle(x, y, w, h, **kw) -> str:
    return overlay.draw_rectangle(x, y, w, h, **kw)

def draw_rounded_rectangle(x, y, w, h, radius=0.01, **kw) -> str:
    return overlay.draw_rounded_rectangle(x, y, w, h, radius=radius, **kw)

def draw_circle(cx, cy, r, **kw) -> str:
    return overlay.draw_circle(cx, cy, r, **kw)

def draw_ellipse(cx, cy, rx, ry, **kw) -> str:
    return overlay.draw_ellipse(cx, cy, rx, ry, **kw)

def draw_polygon(points, **kw) -> str:
    return overlay.draw_polygon(points, **kw)

def draw_text(x, y, text, **kw) -> str:
    return overlay.draw_text(x, y, text, **kw)

def draw_image(x, y, w, h, src, **kw) -> str:
    return overlay.draw_image(x, y, w, h, src, **kw)

def draw_grid(cols=10, rows=10, **kw) -> str:
    return overlay.draw_grid(cols=cols, rows=rows, **kw)

def draw_crosshair(x, y, size=0.02, **kw) -> str:
    return overlay.draw_crosshair(x, y, size=size, **kw)

def draw_highlight(x, y, w, h, label=None, **kw) -> str:
    return overlay.draw_highlight(x, y, w, h, label=label, **kw)

def draw_path(points, **kw) -> str:
    return overlay.draw_path(points, **kw)

def draw_dashed_line(x1, y1, x2, y2, dash=None, **kw) -> str:
    return overlay.draw_dashed_line(x1, y1, x2, y2, dash=dash, **kw)

def draw_bezier(x1, y1, cx1, cy1, cx2, cy2, x2, y2, **kw) -> str:
    return overlay.draw_bezier(x1, y1, cx1, cy1, cx2, cy2, x2, y2, **kw)

# ── Semantic helpers ─────────────────────────────────────────────────────────

def highlight_bbox(bbox: tuple, label: str = None, **kw) -> str:
    """
    bbox = (x1, y1, x2, y2) in normalized 0-1 coordinates.
    Draws an animated glowing highlight around the bounding box.
    """
    return overlay.highlight_bbox(bbox, label=label, **kw)

def label_bbox(bbox: tuple, text: str, **kw) -> str:
    return overlay.label_bbox(bbox, text, **kw)

def draw_arrow_between(bbox1: tuple, bbox2: tuple, **kw) -> str:
    return overlay.draw_arrow_between(bbox1, bbox2, **kw)
