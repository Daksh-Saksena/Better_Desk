import asyncio
import threading
import socket
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .websocket import ws_manager
from .overlay_manager import overlay
DIR = Path(__file__).parent
app = FastAPI(title="BetterDesk Overlay Engine")
app.mount("/static", StaticFiles(directory=DIR), name="static")
@app.get("/")
async def index():
    return FileResponse(DIR / "index.html")
@app.get("/renderer.js")
async def renderer_js():
    return FileResponse(DIR / "renderer.js", media_type="application/javascript")
@app.get("/style.css")
async def style_css():
    return FileResponse(DIR / "style.css", media_type="text/css")
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    await overlay.sync_client(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"
def start(host: str = "0.0.0.0", port: int = 8000, daemon: bool = True):
    """
    Start the overlay server.
    If daemon=True (default), runs in a background thread so it doesn't block detector.py.
    """
    loop = asyncio.new_event_loop()
    overlay.set_loop(loop)
    config = uvicorn.Config(app, host=host, port=port,
                            loop="none", log_level="error")
    server = uvicorn.Server(config)
    def _run():
        loop.run_until_complete(server.serve())
    ip = get_local_ip()
    pass
    pass
    t = threading.Thread(target=_run, daemon=daemon, name="overlay-server")
    t.start()
    return t
if __name__ == "__main__":
    start(daemon=False)
