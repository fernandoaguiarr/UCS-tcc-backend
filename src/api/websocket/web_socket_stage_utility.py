import json
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../../")

from src.services.chunk import count_tokens, create_chunks
from src.services.openai_client import OpenAIClient
from src.services.selenium.web_interaction_helper import WebInteractionHelper
from src.constants.instructions import FILTER_ELEMENT_IDENTIFIERS_PROMPT, HTML_FILTER_ANALYSIS_INSTRUCTION, \
    ACTION_ELEMENT_IDENTIFIERS_PROMPT, DATA_DOWNLOAD_ANALYSIS_INSTRUCTION


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


class WebSocketStageUtility:

    def __init__(self, openai_client: OpenAIClient, web_interaction_helper: WebInteractionHelper):
        self.openai_client = openai_client
        self.web_interaction_helper = web_interaction_helper

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
            print("field", i + 1)
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

    def get_action_identifiers(self, html: str) -> list:
        openai_response = self.openai_client.send_to_openai(
            text=html,
            instruction=ACTION_ELEMENT_IDENTIFIERS_PROMPT
        )

        return json.loads(openai_response)["action_identifiers"]

    def handle_field_interaction(self, field):
        attributes = field["attributes"]

        if attributes["id"]:
            element = self.web_interaction_helper.wait_for_element_presence_by_id(attributes["id"])
        else:
            xpath = "//*[contains(@class, 'search-result')]"
            element = self.web_interaction_helper.wait_for_element_presence_by_xpath(xpath)

        # Remover css para evitar elementos escondidos
        self.web_interaction_helper.remove_css_classes(element)
        self.web_interaction_helper.remove_inline_styles(element)

        # Multiselects podem não ter uma estrutura html padrão
        # Caso seja um select
        if field["field_type"] in ["select", "multiselect"] or attributes["type"] in ["checkbox", "radio"]:
            # Para exibir a lista no dom, caso não esteja com algum style
            element.click()

            if "selected_options" in field:
                for option in field["selected_options"]:
                    value = option["value"] if "value" in option and option["value"] else option["label"]

                    if "class" in option and option["class"]:
                        xpath = f".//*[contains(@class, '{option['class']}') and contains(., '{value}')]"
                    else:
                        xpath = f".//*[contains(., '{value}')]"

                    option_element = self.web_interaction_helper.wait_for_element_presence_by_xpath(xpath)
                    self.web_interaction_helper.click(option_element)

            return
        # Caso não seja clicável, assume-se que é para ser digitado
        else:
            self.web_interaction_helper.fill_input_field(element, attributes["value"])
            return

    def handle_selected_action(self, action):
        # print(self.web_interaction_helper.get_html_element("body"))
        if "id" in action and action["id"]:
            element = self.web_interaction_helper.wait_for_element_presence_by_id(action["id"])
        elif "container_class" and action["container_class"]:
            xpath = f".//*[contains(@class, '{action['container_class']}') and contains(., '{action["text"]}')]"
            print(xpath)
            element = self.web_interaction_helper.wait_for_element_presence_by_xpath(xpath)
        else:
            xpath = f".//*[contains(@class, '{action['class']}') and contains(., '{action["text"]}')]"
            element = self.web_interaction_helper.wait_for_element_presence_by_xpath(xpath)

        open_windows_length = self.web_interaction_helper.get_open_windows_length()

        self.web_interaction_helper.click(element)
        self.web_interaction_helper.wait()

        if self.web_interaction_helper.get_open_windows_length() > open_windows_length:
            self.web_interaction_helper.switch_window(-1)

        return self.web_interaction_helper.driver.current_url

    def get_download_elements(self):
        page_content = self.web_interaction_helper.get_html_element("body")

        download_elements = self.openai_client.send_to_openai(
            text=page_content,
            instruction=DATA_DOWNLOAD_ANALYSIS_INSTRUCTION
        )

        print(download_elements)
