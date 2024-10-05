import os
import sys

from starlette.websockets import WebSocket

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../../")

from src.api.websocket.web_socket_stage_manager import WebSocketStageManager


class WebSocketManager:

    def __init__(self):
        self.connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()

        connection = {
            "websocket": websocket,
            "stageManager": WebSocketStageManager()
        }

        self.connections.append(connection)
        return connection["stageManager"]

    def disconnect(self, websocket: WebSocket):
        # self.connections.remove(websocket)
        pass
