import sys
import os
import uuid

from settings import MEDIA_ROOT, SUPPORTED_TYPE_FILES
from src.services.beautiful_soup_manager import BeautifulSoupManager

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../../")

from src.services.openai_client import OpenAIClient
from src.constants.enums.application_stage import ApplicationStage
from src.api.websocket.web_socket_stage_utility import WebSocketStageUtility
from src.services.selenium.web_interaction_helper import WebInteractionHelper


class WebSocketStageManager(WebSocketStageUtility):

    def __init__(self):
        self.state_manager_id = uuid.uuid4()
        self.openai_client = OpenAIClient(model="gpt-4o-mini")
        self.web_interaction_helper = WebInteractionHelper(self.state_manager_id)

        super().__init__(self.openai_client, self.web_interaction_helper)

        self.data = None
        self.current_stage = None
        self.crawling_manager = None
        self.download_dir = os.path.join(MEDIA_ROOT, str(self.state_manager_id))

    def handle_stage(self, stage):
        actions = {
            ApplicationStage.SEND_INITIAL_URL.value: self.send_initial_url,
            ApplicationStage.REQUEST_ADDITIONAL_INFO.value: self.request_additional_info,
            ApplicationStage.SEND_ADDITIONAL_INFO.value: self.send_additional_info,
            ApplicationStage.REQUEST_DATA_DETAILS.value: self.request_data_details,
            ApplicationStage.SEND_DATA_DETAILS.value: self.send_data_details,
            ApplicationStage.WAITING.value: self.waiting,
            ApplicationStage.COMPLETED.value: self.completed,
        }

        return actions.get(stage, self.handle_error)()

    def send_initial_url(self):
        print("Sending initial url...")
        self.current_stage = ApplicationStage.SEND_INITIAL_URL
        response = self.search_for_fields(self.data["url"])

        if "jump_next_stage" in response and response["jump_next_stage"]:
            self.data = response["data"]
            return self.handle_stage(response["jump_next_stage"])

        return response

    def request_additional_info(self):
        print("Requesting additional info...")
        self.current_stage = ApplicationStage.REQUEST_ADDITIONAL_INFO

    def send_additional_info(self):
        print("Sending additional info...")
        self.current_stage = ApplicationStage.SEND_ADDITIONAL_INFO

        if self.web_interaction_helper.driver.current_url != self.data["url"]:
            self.web_interaction_helper.load_page(self.data["url"])

        beautiful_soup_manager = BeautifulSoupManager(self.web_interaction_helper.get_html_element("body"))

        if "fields" in self.data:
            fields_to_remove = set()

            for field in self.data["fields"]:
                self.handle_field_interaction(field)
                fields_to_remove.add(field["attributes"]["class"])

            self.web_interaction_helper.wait()
            beautiful_soup_manager = BeautifulSoupManager(self.web_interaction_helper.get_html_element("body"))

            for field in fields_to_remove:
                beautiful_soup_manager.remove_element_by_class(field, remove_all=True)

        if not "selected_action" in self.data:
            beautiful_soup_manager.clean_soup(
                attributes_to_remove=["style", "data-select", "data-selected", "data-deselect", "tabindex"],
                tags_to_remove=["script", "style", "head", "meta", "noscript", "footer", "header", "svg", "iframe", "p",
                                "i"],
            )

            actions = self.get_action_identifiers(
                beautiful_soup_manager.beautiful_soup_to_str(minify=True)
            )

            redirect_actions = [action for action in actions if action["action_type"] == "redirect"]
            download_actions = [
                action for action in actions
                if action["action_type"] == "download" and
                   ("download_format" in action and action["download_format"].lower() in SUPPORTED_TYPE_FILES)
            ]

            print(download_actions)

            if len(download_actions):
                for download_action in download_actions:
                    self.handle_download_element(download_action, self.download_dir)

                return {
                    "stage": ApplicationStage.REQUEST_DATA_DETAILS.value,
                    "data": {
                        "subsets": self.handle_downloaded_data(self.download_dir)
                    }
                }

            elif len(redirect_actions):
                return {
                    "stage": ApplicationStage.REQUEST_ADDITIONAL_INFO.value,
                    "data": {
                        "url": self.web_interaction_helper.driver.current_url,
                        "actions": redirect_actions
                    }
                }
            else:
                return self.handle_error("Não foram encontradas possíveis ações e locais de download")
        else:
            # Quando o usuário escolhe uma ação, o processo deve reiniciar :)
            should_switch_window = self.handle_selected_action(self.data["selected_action"])

            # Verificar se alguma ação não baixou algo
            self.web_interaction_helper.wait_for_download_completion(self.download_dir)
            if len(os.listdir(self.download_dir)):
                return {
                    "stage": ApplicationStage.REQUEST_DATA_DETAILS.value,
                    "data": {
                        "subsets": self.handle_downloaded_data(self.download_dir)
                    }
                }

            if should_switch_window:
                self.web_interaction_helper.switch_window()
                self.web_interaction_helper.wait()

                self.data["url"] = self.web_interaction_helper.driver.current_url
                return self.handle_stage(ApplicationStage.SEND_INITIAL_URL.value)

            # Volta para o estado inicial, porém numa nova página, ou com o seu conteúdo atualizado
            # Verificar se o fluxo tá certo, quando é um botão de submit

            del self.data["selected_action"]
            return self.handle_stage(ApplicationStage.SEND_ADDITIONAL_INFO.value)

    def request_data_details(self):
        print("Requesting data details...")
        self.current_stage = ApplicationStage.REQUEST_DATA_DETAILS

    def send_data_details(self):
        print("Sending data details...")
        self.current_stage = ApplicationStage.SEND_DATA_DETAILS

        if not "format" in self.data:
            return self.handle_error("Formato da exportação dos dados ausente.")
        if not self.data["format"].lower() in SUPPORTED_TYPE_FILES:
            return self.handle_error("O Formato da exportação dos dados escolhido não é suportado.")

        return {
            "stage": ApplicationStage.COMPLETED.value,
            "data": {
                "url_files": self.prepare_data_to_export(self.download_dir, self.data["format"], self.data["subsets"])
            }
        }

    def completed(self):
        self.current_stage = ApplicationStage.COMPLETED

        return {
            "stage": ApplicationStage.COMPLETED.value
        }

    def handle_error(self, message: str = None):
        print("Handling error...")
        self.current_stage = ApplicationStage.ERROR

        return {
            "stage": ApplicationStage.ERROR.value,
            "message": message if message else "Ocorreu um erro inesperado."
        }

    def waiting(self):
        print("Waiting stage")
        self.current_stage = ApplicationStage.WAITING
        return {"stage": ApplicationStage.WAITING.value}

    def clear_user_download_folder(self, remove_folder: bool = False):
        for file in os.listdir(self.download_dir):
            os.remove(f"{self.download_dir}/{file}")

        if remove_folder:
            os.rmdir(self.download_dir)
