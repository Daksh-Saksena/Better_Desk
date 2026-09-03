import asyncio
import uuid
import threading
from typing import Optional, Dict, Any, List
from .websocket import ws_manager
class OverlayManager:
    def __init__(self):
        self._scene: Dict[str, dict] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._lock = threading.Lock()
    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop
    def _dispatch(self, msg: dict):
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(ws_manager.broadcast(msg), self._loop)
    def _node(self, type_: str, id_: Optional[str], layer: int, **kwargs) -> dict:
        node = {
            "id": id_ or str(uuid.uuid4())[:8],
            "type": type_,
            "layer": layer,
            "visible": True,
            **kwargs
        }
        return node
    def add(self, node: dict) -> str:
        if "id" not in node:
            node["id"] = str(uuid.uuid4())[:8]
        with self._lock:
            self._scene[node["id"]] = node
        self._dispatch({"cmd": "add", "node": node})
        return node["id"]
    def update(self, id_: str, **kwargs):
        with self._lock:
            if id_ in self._scene:
                self._scene[id_].update(kwargs)
        self._dispatch({"cmd": "update", "id": id_, "params": kwargs})
    def remove(self, id_: str):
        with self._lock:
            self._scene.pop(id_, None)
        self._dispatch({"cmd": "remove", "id": id_})
    def clear(self):
        with self._lock:
            self._scene.clear()
        self._dispatch({"cmd": "clear"})
    def clear_layer(self, layer: int):
        with self._lock:
            to_del = [k for k, v in self._scene.items() if v.get("layer") == layer]
            for k in to_del:
                del self._scene[k]
        self._dispatch({"cmd": "clear_layer", "layer": layer})
    def remove_all(self):
        self.clear()
    async def sync_client(self, ws):
        """Send full scene state to a freshly connected client."""
        with self._lock:
            nodes = list(self._scene.values())
        for node in nodes:
            await ws_manager.send_to(ws, {"cmd": "add", "node": node})
    def draw_line(self, x1: float, y1: float, x2: float, y2: float,
                  id_: str = None, layer: int = 2, **style) -> str:
        return self.add(self._node("line", id_, layer, x1=x1, y1=y1, x2=x2, y2=y2, **style))
    def draw_arrow(self, start: tuple, end: tuple,
                   arrow_type: str = "straight",
                   id_: str = None, layer: int = 2, **style) -> str:
        return self.add(self._node("arrow", id_, layer,
                                   x1=start[0], y1=start[1],
                                   x2=end[0], y2=end[1],
                                   arrowType=arrow_type, **style))
    def draw_rectangle(self, x: float, y: float, w: float, h: float,
                       id_: str = None, layer: int = 1, **style) -> str:
        return self.add(self._node("rect", id_, layer, x=x, y=y, w=w, h=h, **style))
    def draw_rounded_rectangle(self, x: float, y: float, w: float, h: float,
                                radius: float = 0.01, id_: str = None, layer: int = 1, **style) -> str:
        return self.add(self._node("rounded_rect", id_, layer, x=x, y=y, w=w, h=h, radius=radius, **style))
    def draw_circle(self, cx: float, cy: float, r: float,
                    id_: str = None, layer: int = 1, **style) -> str:
        return self.add(self._node("circle", id_, layer, cx=cx, cy=cy, r=r, **style))
    def draw_ellipse(self, cx: float, cy: float, rx: float, ry: float,
                     id_: str = None, layer: int = 1, **style) -> str:
        return self.add(self._node("ellipse", id_, layer, cx=cx, cy=cy, rx=rx, ry=ry, **style))
    def draw_polygon(self, points: List[tuple], id_: str = None, layer: int = 1, **style) -> str:
        return self.add(self._node("polygon", id_, layer,
                                   points=[[p[0], p[1]] for p in points], **style))
    def draw_text(self, x: float, y: float, text: str,
                  id_: str = None, layer: int = 3, **style) -> str:
        return self.add(self._node("text", id_, layer, x=x, y=y, text=text, **style))
    def draw_image(self, x: float, y: float, w: float, h: float, src: str,
                   id_: str = None, layer: int = 1, **style) -> str:
        return self.add(self._node("image", id_, layer, x=x, y=y, w=w, h=h, src=src, **style))
    def draw_grid(self, cols: int = 10, rows: int = 10,
                  id_: str = None, layer: int = 0, **style) -> str:
        return self.add(self._node("grid", id_, layer, cols=cols, rows=rows, **style))
    def draw_crosshair(self, x: float, y: float, size: float = 0.02,
                       id_: str = None, layer: int = 4, **style) -> str:
        return self.add(self._node("crosshair", id_, layer, x=x, y=y, size=size, **style))
    def draw_highlight(self, x: float, y: float, w: float, h: float,
                       label: str = None, id_: str = None, layer: int = 1, **style) -> str:
        return self.add(self._node("highlight", id_, layer, x=x, y=y, w=w, h=h, label=label, **style))
    def draw_path(self, points: List[tuple], id_: str = None, layer: int = 2, **style) -> str:
        return self.add(self._node("path", id_, layer,
                                   points=[[p[0], p[1]] for p in points], **style))
    def draw_dashed_line(self, x1: float, y1: float, x2: float, y2: float,
                         dash: list = None, id_: str = None, layer: int = 2, **style) -> str:
        return self.add(self._node("dashed_line", id_, layer,
                                   x1=x1, y1=y1, x2=x2, y2=y2,
                                   dash=dash or [0.01, 0.01], **style))
    def draw_bezier(self, x1: float, y1: float, cx1: float, cy1: float,
                    cx2: float, cy2: float, x2: float, y2: float,
                    id_: str = None, layer: int = 2, **style) -> str:
        return self.add(self._node("bezier", id_, layer,
                                   x1=x1, y1=y1, cx1=cx1, cy1=cy1,
                                   cx2=cx2, cy2=cy2, x2=x2, y2=y2, **style))
    def highlight_bbox(self, bbox: tuple, label: str = None,
                       id_: str = None, layer: int = 1, **style) -> str:
        """bbox = (x1_norm, y1_norm, x2_norm, y2_norm) in 0-1 coords."""
        x1, y1, x2, y2 = bbox
        return self.draw_highlight(x1, y1, x2 - x1, y2 - y1,
                                   label=label, id_=id_, layer=layer, **style)
    def label_bbox(self, bbox: tuple, text: str, id_: str = None, **style) -> str:
        x1, y1, x2, y2 = bbox
        return self.draw_text(x1, y1 - 0.04, text, id_=id_, **style)
    def draw_arrow_between(self, bbox1: tuple, bbox2: tuple,
                            id_: str = None, **style) -> str:
        cx1 = (bbox1[0] + bbox1[2]) / 2
        cy1 = (bbox1[1] + bbox1[3]) / 2
        cx2 = (bbox2[0] + bbox2[2]) / 2
        cy2 = (bbox2[1] + bbox2[3]) / 2
        return self.draw_arrow((cx1, cy1), (cx2, cy2), id_=id_, **style)
overlay = OverlayManager()
