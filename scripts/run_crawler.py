import sys
import os

from typer.cli import state

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from src.services.openai_client import OpenAIClient
from src.api.websocket.web_socket_stage_manager import WebSocketStageManager
from src.constants.enums.application_stage import ApplicationStage

stateManager = WebSocketStageManager()

# stateManager.data = {"url": "https://dados.gov.br/dados/conjuntos-dados/qualidade-telefonia-movel"}
# html = stateManager.handle_stage(ApplicationStage.SEND_INITIAL_URL.value)

stateManager.data = {
    "url": "https://dados.gov.br/dados/conjuntos-dados",
    "fields": [
        {
            "field_type": "multiselect",
            "attributes": {
                "id": "multiSelectTema",
                "class": "multiselect__input",
                "placeholder": "Selecione um tema",
                "type": "text",
                "autocomplete": "off"
            },
            "selected_options": [
                {
                    "label": "Administração",
                    "disabled": False,
                    "class": "multiselect__option"
                },
            ]
        }
    ]
    # "selected_action": {
    #     "class": "search-result-title",
    #     "tag": "a",
    #     "text": "Entrada de Estrangeiros",
    #     "container_class": "search-result container my-2"
    # }
}

html = stateManager.handle_stage(ApplicationStage.SEND_ADDITIONAL_INFO.value)
stateManager.data = {
    "url": "https://dados.gov.br/dados/conjuntos-dados",
    # "fields": [
    #     {
    #         "field_type": "multiselect",
    #         "attributes": {
    #             "id": "multiSelectTema",
    #             "class": "multiselect__input",
    #             "placeholder": "Selecione um tema",
    #             "type": "text",
    #             "autocomplete": "off"
    #         },
    #         "selected_options": [
    #             {
    #                 "label": "Administração",
    #                 "disabled": False,
    #                 "class": "multiselect__option"
    #             },
    #         ]
    #     }
    # ]
    "selected_action": {
        "class": "search-result-title",
        "tag": "a",
        "text": "Entrada de Estrangeiros",
        "container_class": "search-result container my-2"
    }
}
# html = stateManager.handle_stage(ApplicationStage.SEND_ADDITIONAL_INFO.value)

print(html)
