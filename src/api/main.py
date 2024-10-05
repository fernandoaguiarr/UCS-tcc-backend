import os
import sys
import json
import time
import asyncio

from fastapi import FastAPI, WebSocket
from starlette.responses import HTMLResponse
from starlette.websockets import WebSocketDisconnect

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../")

from src.constants.enums.application_stage import ApplicationStage
from src.api.websocket.web_socket_manager import WebSocketManager

app = FastAPI()
manager = WebSocketManager()


@app.get("/")
async def get():
    html = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Chat</title>
        </head>
        <body>
            <h1>WebSocket Chat</h1>
            <form action="" onsubmit="sendMessage(event)">
                <input type="text" id="messageText" value="https://dados.gov.br/dados/conjuntos-dados" autocomplete="off"/>
                <button>Send</button>
            </form>
            
            <form action="" onsubmit="sendFilters(event)">
                <input type="text" id="filterText" autocomplete="off"/>
                <button>Send</button>
            </form>
            <ul id='messages'>
            </ul>
            <script>
                var ws = new WebSocket("ws://127.0.0.1:8000/ws");
                ws.onmessage = function(event) {
                    var messages = document.getElementById('messages')
                    var message = document.createElement('li')
                    var content = document.createTextNode(event.data)
                    console.log(event.data)
                    message.appendChild(content)
                    messages.appendChild(message)
                };
                function sendMessage(event) {
                    var input = document.getElementById("messageText")
                    ws.send(JSON.stringify({
                        'stage':'SEND_INITIAL_URL',
                        'data': {
                            'url': input.value
                        }
                    }))
                    event.preventDefault()
                }
                
                function sendFilters(event){
                   var input = document.getElementById("filterText")
                    ws.send(JSON.stringify({
                        'stage':'SEND_ADDITIONAL_INFO',
                        'data': {
                            'filters': [
                                {
                                    'class':'multiselect',
                                    'field_id':3,
                                    'id':'multiSelectPalavraChave'
                                    'value':input.value
                                }
                            ]
                        }
                    })) 
                     event.preventDefault()
                }
            </script>
        </body>
    </html>
    """

    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    state_manager = await manager.connect(websocket)

    try:
        while True:
            data = json.loads(await websocket.receive_text())
            state_manager.data = data["data"]

            if data["stage"]:
                # Sempre que receber um novo estágio mandar ao usuário o estágio WAITING
                response = state_manager.handle_stage(ApplicationStage.WAITING.value)
                await websocket.send_text(f"{response}")
                await asyncio.sleep(1)

                response = state_manager.handle_stage(data["stage"])
                state_manager.previous_data = data["data"]
                print("Ending of stage")
                await websocket.send_text(f"{response}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
