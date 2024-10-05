import json
import sys
import os
import uuid

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../../")

from src.services.openai_client import OpenAIClient
from src.services.crawling_manager import CrawlingManager
from src.services.chunk import count_tokens, create_chunks
from src.constants.enums.application_stage import ApplicationStage
from src.services.selenium.web_interaction_helper import WebInteractionHelper
from src.services.html_parser import clean_html, get_html_elements, remove_elements_by_class_name
from src.constants.instructions import HTML_FILTER_ANALYSIS_INSTRUCTION, FILTER_ELEMENT_IDENTIFIERS_PROMPT, \
    ACTION_ELEMENT_IDENTIFIERS_PROMPT


def merge_dicts(d1, d2):
    merged = {}
    for key in set(d1) | set(d2):
        if key in d1 and key in d2:
            # Se ambos os valores forem dicionários, faz o merge recursivamente
            if isinstance(d1[key], dict) and isinstance(d2[key], dict):
                merged[key] = merge_dicts(d1[key], d2[key])
            # Se ambos os valores forem listas, faz a união das listas
            elif isinstance(d1[key], list) and isinstance(d2[key], list):
                merged[key] = d1[key] + d2[key]
            else:
                merged[key] = d2[key]  # Prioriza o valor de d2
        elif key in d1:
            merged[key] = d1[key]
        else:
            merged[key] = d2[key]
    return merged


class WebSocketStageManager:

    def __init__(self):
        self.data = None
        self.current_stage = None
        self.crawling_manager = None
        self.state_manager_id = uuid.uuid4()
        self.openai_client = OpenAIClient(model="gpt-4o-mini")

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

    def get_fields_identifiers(self, chunks: list[str]) -> set:
        fields = set()

        for chunk in chunks:
            openai_response = self.openai_client.send_to_openai(
                text=chunk,
                instruction=FILTER_ELEMENT_IDENTIFIERS_PROMPT
            )

            openai_response = json.loads(openai_response)["filter_identifiers"]

            for _field in openai_response:
                sorted_field = tuple(sorted(_field.items()))
                fields.add(sorted_field)

        return fields

    def get_fields(self, html_fields: list[str]) -> list:
        fields = []
        chunks = []

        for i, html_field in enumerate(html_fields):
            field_dict = {}

            if count_tokens(html_field, self.openai_client.model):
                chunks.extend(
                    create_chunks(
                        text=html_field,
                        max_chunk_size=12000,
                        model=self.openai_client.model
                    )
                )
            else:
                chunks.append(html_field)

            for chunk in chunks:
                openai_response = self.openai_client.send_to_openai(
                    text=chunk,
                    instruction=HTML_FILTER_ANALYSIS_INSTRUCTION,
                    model=self.openai_client.model
                )

                openai_response = json.loads(openai_response)
                field_dict = merge_dicts(field_dict, openai_response)

            fields.append(field_dict)

        return fields

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

    def get_action_identifiers(self, html: str) -> list:
        openai_response = self.openai_client.send_to_openai(
            text=html,
            instruction=ACTION_ELEMENT_IDENTIFIERS_PROMPT
        )

        return json.loads(openai_response)["action_identifiers"]

    def send_additional_info(self):
        print("Sending additional info...")
        self.current_stage = ApplicationStage.SEND_ADDITIONAL_INFO
        web_interaction_helper = WebInteractionHelper(self.state_manager_id)

        fields_to_remove = set()

        for field in self.data["fields"]:
            # xpath = f".//*[contains(@class, '{option["class"]}') and contains(., '{value}')]"
            # Aqui precisa testar os tipos de campos

            fields_to_remove.add(field["attributes"]["class"])

        html_page = web_interaction_helper.get_html_element("body")

        for field in fields_to_remove:
            html_page = remove_elements_by_class_name(html_page, field)

        html_page = clean_html(html_page)

        actions = self.get_action_identifiers(html_page)

        

        web_interaction_helper.quit()

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
