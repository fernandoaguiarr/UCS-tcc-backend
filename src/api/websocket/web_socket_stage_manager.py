import sys
import os
import uuid

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../../")

from src.services.openai_client import OpenAIClient
from src.services.crawling_manager import CrawlingManager
from src.services.chunk import count_tokens, create_chunks
from src.constants.enums.application_stage import ApplicationStage
from src.constants.instructions import FILTER_ELEMENT_IDENTIFIERS_PROMPT
from src.api.websocket.web_socket_stage_utility import WebSocketStageUtility
from src.services.selenium.web_interaction_helper import WebInteractionHelper
from src.services.html_parser import clean_html, get_html_elements, remove_elements_by_class_name


class WebSocketStageManager(WebSocketStageUtility):

    def __init__(self):
        self.state_manager_id = uuid.uuid4()
        self.openai_client = OpenAIClient(model="gpt-4o-mini")
        self.web_interaction_helper = WebInteractionHelper(self.state_manager_id)

        super().__init__(self.openai_client, self.web_interaction_helper)

        self.data = None
        self.current_stage = None
        self.crawling_manager = None

    def init_crawling_manager(self):
        if not self.crawling_manager:
            self.crawling_manager = CrawlingManager()

    def handle_stage(self, stage):
        actions = {
            ApplicationStage.SEND_INITIAL_URL.value: self.send_initial_url,
            ApplicationStage.REQUEST_ADDITIONAL_INFO.value: self.request_additional_info,
            ApplicationStage.SEND_ADDITIONAL_INFO.value: self.send_additional_info,
            ApplicationStage.REQUEST_DATA_DETAILS.value: self.request_data_details,
            ApplicationStage.SEND_DATA_DETAILS.value: self.send_data_details,
            ApplicationStage.WAITING.value: self.waiting,
        }

        return actions.get(stage, self.handle_error)()

    def send_initial_url(self, url: str = None):
        self.init_crawling_manager()
        self.current_stage = ApplicationStage.SEND_INITIAL_URL
        page_content = clean_html(self.crawling_manager.start(url=url if url else self.data["url"]))

        # Criar chunks
        response_tokens = 5000
        max_tokens_model = 200000
        instruction_tokens = count_tokens(FILTER_ELEMENT_IDENTIFIERS_PROMPT, self.openai_client.model)

        chunks = create_chunks(
            text=page_content,
            max_chunk_size=(max_tokens_model - response_tokens - instruction_tokens),
            model=self.openai_client.model
        )

        print("Total chunks: {}".format(len(chunks)))

        fields_identifiers = self.get_fields_identifiers(chunks)

        # Caso não sejam encontrados campos de filtro, avançar para o próximo estágio
        if not len(fields_identifiers):
            self.data["fields"] = []
            return self.send_additional_info()

        html_fields = get_html_elements(page_content, [dict(identifier) for identifier in fields_identifiers])
        fields = self.get_fields(html_fields)

        print(fields)

        return {
            "stage": ApplicationStage.REQUEST_ADDITIONAL_INFO.value,
            "data": {
                "fields": fields
            }
        }

    def request_additional_info(self):
        print("Requesting additional info...")
        self.current_stage = ApplicationStage.REQUEST_ADDITIONAL_INFO

    def send_additional_info(self):
        print("Sending additional info...")
        self.current_stage = ApplicationStage.SEND_ADDITIONAL_INFO

        self.web_interaction_helper.load_page(self.data["url"])

        if "fields" in self.data and len(self.data["fields"]):
            fields_to_remove = set()

            for field in self.data["fields"]:
                self.handle_field_interaction(field)
                fields_to_remove.add(field["attributes"]["class"])

            self.web_interaction_helper.wait()
            html_page = self.web_interaction_helper.get_html_element("body")

            for field in fields_to_remove:
                html_page = remove_elements_by_class_name(html_page, field)

            html_page = clean_html(html_page)

            actions = self.get_action_identifiers(html_page)

            if len(actions):
                print(actions)
                return {
                    "stage": ApplicationStage.REQUEST_ADDITIONAL_INFO.value,
                    "data": {
                        "actions": actions
                    }
                }

            # Segue em busca do download...
            # return self.send_additional_info()
        elif "selected_action" in self.data:
            url = self.handle_selected_action(self.data["selected_action"])

            if url != self.data["url"]:
                self.data["url"] = url
                # Aqui precisa verificar se tem filtros
                pass

            self.get_download_elements()

    def request_data_details(self):
        print("Requesting data details...")
        self.current_stage = ApplicationStage.REQUEST_DATA_DETAILS

    def send_data_details(self):
        print("Sending data details...")
        self.current_stage = ApplicationStage.SEND_DATA_DETAILS

    def handle_error(self):
        print("Handling error...")
        self.current_stage = ApplicationStage.ERROR

    def waiting(self):
        print("Waiting stage")
        self.current_stage = ApplicationStage.WAITING
        return {"stage": ApplicationStage.WAITING.value}
