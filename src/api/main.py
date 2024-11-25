import os
import sys
import json

import magic
from fastapi import FastAPI, WebSocket
from starlette.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../")
from settings import MEDIA_ROOT

from src.constants.enums.application_stage import ApplicationStage
from src.api.websocket.web_socket_manager import WebSocketManager

app = FastAPI()
manager = WebSocketManager()

origins = [
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    state_manager = await manager.connect(websocket)

    try:
        while True:
            data = json.loads(await websocket.receive_text())
            if "data" in data:
                state_manager.data = data["data"]

                if "new_extraction" in data["data"] and data["data"]["new_extraction"]:
                    state_manager.clear_user_download_folder()

                if "stage" in data and data["stage"]:
                    # Sempre que receber um novo estágio mandar ao usuário o estágio WAITING
                    response = state_manager.handle_stage(ApplicationStage.WAITING.value)
                    await websocket.send_json(response)

                    response = state_manager.handle_stage(data["stage"])
                    state_manager.previous_data = data["data"]
                    print("Ending of stage")
                    await websocket.send_json(response)

    except WebSocketDisconnect:
        state_manager.clear_user_download_folder(True)
        manager.disconnect(websocket)


@app.get("/download/{session_id}/{file_name}")
async def download_file(session_id: str, file_name: str):
    file_path = os.path.join(MEDIA_ROOT, session_id, file_name)
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            filename=file_name,
            media_type=magic.from_file(file_path, mime=True)
        )
    else:
        return {"Error": "Arquivo não encontrado"}
