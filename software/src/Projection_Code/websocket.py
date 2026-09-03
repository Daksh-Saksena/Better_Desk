from fastapi import WebSocket
from typing import List
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, msg: dict):
        data = json.dumps(msg)
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def send_to(self, ws: WebSocket, msg: dict):
        try:
            await ws.send_text(json.dumps(msg))
        except Exception:
            self.disconnect(ws)

ws_manager = ConnectionManager()
