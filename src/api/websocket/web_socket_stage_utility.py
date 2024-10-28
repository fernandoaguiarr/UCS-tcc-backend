import os
import sys
import json

import magic
from selenium.common import TimeoutException

from settings import SUPPORTED_MIME_TYPE_FILES
from src.services.beautiful_soup_manager import BeautifulSoupManager
from src.services.file_data_manager import FileDataManager

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../../")

from src.services.openai_client import OpenAIClient
from src.services.chunk import count_tokens, create_chunks
from src.constants.enums.application_stage import ApplicationStage
from src.services.selenium.web_interaction_helper import WebInteractionHelper
from src.constants.instructions import HTML_FILTER_CONTAINER_IDENTIFIERS, HTML_FORM_FIELD_ANALYSIS, \
    HTML_ACTIONABLE_ELEMENT_ANALYSIS


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

    def search_for_fields(self, url: str):
        self.web_interaction_helper.load_page(url)
        self.web_interaction_helper.wait()

        beautiful_soup_manager = BeautifulSoupManager(self.web_interaction_helper.get_html_element("body"))
        beautiful_soup_manager.clean_soup(
            attributes_to_remove=["style", "data-select", "data-selected", "data-deselect", "tabindex"],
            tags_to_remove=["script", "style", "head", "meta", "noscript", "footer", "header", "svg", "iframe", "p",
                            "i"]
        )

        page_content = beautiful_soup_manager.beautiful_soup_to_str(minify=True)

        # Criar chunks
        response_tokens = 5000
        max_tokens_model = 200000
        instruction_tokens = count_tokens(HTML_FILTER_CONTAINER_IDENTIFIERS, self.openai_client.model)

        chunks = create_chunks(
            text=page_content,
            max_chunk_size=(max_tokens_model - response_tokens - instruction_tokens),
            model=self.openai_client.model
        )

        print("Total chunks: {}".format(len(chunks)))

        fields_identifiers = self.get_fields_identifiers(chunks)

        # Caso não sejam encontrados campos de filtro, avançar para o próximo estágio
        if not len(fields_identifiers):
            return {
                "jump_next_stage": ApplicationStage.SEND_ADDITIONAL_INFO.value,
                "data": {
                    "url": url,
                    "fields": fields_identifiers
                }
            }

        html_fields = beautiful_soup_manager.extract_unique_html_elements(
            search_criteria=[dict(identifier) for identifier in fields_identifiers]
        )

        fields = self.get_fields(html_fields)

        return {
            "stage": ApplicationStage.REQUEST_ADDITIONAL_INFO.value,
            "data": {
                "fields": fields
            }
        }

    def get_fields_identifiers(self, chunks: list[str]) -> set:
        fields = set()

        for chunk in chunks:
            openai_response = self.openai_client.send_to_openai(
                text=chunk,
                instruction=HTML_FILTER_CONTAINER_IDENTIFIERS
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
                    instruction=HTML_FORM_FIELD_ANALYSIS,
                    model=self.openai_client.model
                )

                openai_response = json.loads(openai_response)
                field_dict = merge_dicts(field_dict, openai_response)

            fields.append(field_dict)

        return fields

    def get_action_identifiers(self, html: str) -> list:
        openai_response = self.openai_client.send_to_openai(
            text=html,
            instruction=HTML_ACTIONABLE_ELEMENT_ANALYSIS
        )

        return json.loads(openai_response)["actions"]

    def handle_field_interaction(self, field):
        attributes = field["attributes"]

        if attributes["id"]:
            element = self.web_interaction_helper.wait_for_element_presence_by_id(attributes["id"])
        else:
            xpath = f"//*[contains(@class, '{attributes["class"]}')]"
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
                        xpath = f".//*[contains(text(), '{value}')]"

                    option_element = self.web_interaction_helper.wait_for_element_presence_by_xpath(xpath)
                    self.web_interaction_helper.click(option_element)

            return
        # Caso não seja clicável, assume-se que é para ser digitado
        else:
            self.web_interaction_helper.fill_input_field(element, attributes["value"])
            return

    def handle_selected_action(self, action) -> bool:
        if "id" in action and action["id"]:
            element = self.web_interaction_helper.wait_for_element_presence_by_id(action["id"])
        else:
            xpath = f".//*[contains(@class, '{action['class']}') and contains(normalize-space(.), '{action['text'].strip()}')]"
            element = self.web_interaction_helper.wait_for_element_presence_by_xpath(xpath)

        open_windows_length = self.web_interaction_helper.get_open_windows_length()

        if not self.web_interaction_helper.click(element):
            self.web_interaction_helper.click_using_javascript(element)

        self.web_interaction_helper.wait()

        return self.web_interaction_helper.get_open_windows_length() > open_windows_length

    def handle_download_element(self, download_action, download_dir: str):
        element_xpath = self.web_interaction_helper.create_default_xpath_sentence(download_action)
        xpath_tag = f"{download_action['tag'] if 'tag' in download_action else '*'}"

        if "download_format" in download_action and download_action["download_format"]:
            xpath = (f"//*[normalize-space(text()) = '{download_action['download_format']}']"
                     f"/following::{xpath_tag}[{element_xpath}][1]")
        else:
            xpath = f"//{xpath_tag}[{element_xpath}]"

        try:
            # Caso o xpath com o download_format não funcione, faz a busca com o normal
            element = self.web_interaction_helper.wait_for_element_presence_by_xpath(xpath)
        except TimeoutException:
            xpath = f"//{xpath_tag}[{element_xpath}]"
            element = self.web_interaction_helper.wait_for_element_presence_by_xpath(xpath)

        if not self.web_interaction_helper.click(element):
            self.web_interaction_helper.click_using_javascript(element)

        self.web_interaction_helper.wait(1)
        self.web_interaction_helper.wait_for_download_completion(download_dir)

    @staticmethod
    def handle_downloaded_data(download_dir):

        file_data_manager = FileDataManager()
        samples = []
        zip_files = [
            os.path.join(download_dir, filename)
            for filename in os.listdir(download_dir)
            if os.path.isfile(os.path.join(download_dir, filename)) and magic.from_file(
                os.path.join(download_dir, filename), mime=True) == "application/zip"
        ]

        for zip_file in zip_files:
            file_data_manager.unpack_file(zip_file, download_dir)
            file_data_manager.delete_file(zip_file)

        for file_name in os.listdir(download_dir):
            file_path = f"{download_dir}/{file_name}"
            mime = magic.from_file(file_path, mime=True)

            if mime in SUPPORTED_MIME_TYPE_FILES:
                df = file_data_manager.open_file(file_path, mime)

                if isinstance(df, dict):
                    continue

                df = file_data_manager.create_sample(df)
                samples.append(file_data_manager.convert_dataframe_to_json(df))

        return samples
