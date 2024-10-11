import os
import time

from pydantic import UUID4
from selenium import webdriver
from selenium.common import ElementNotInteractableException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions


def get_browser_options(state_manager_id: UUID4) -> Options:
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless=chrome")  # Executa em modo headless
    # chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--window-size=1920,1080')

    prefs = {
        "download.default_directory": os.path.join(os.getcwd(), f"temp/{state_manager_id}/"),
        "download.prompt_for_download": False,
        "directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_setting_values.automatic_downloads": 1
    }

    chrome_options.add_experimental_option("prefs", prefs)

    return chrome_options


def wait(secs: float = 10):
    time.sleep(secs)


class SeleniumHelper:

    def __init__(self, state_manager_id: UUID4):
        self.driver = webdriver.Chrome(get_browser_options(state_manager_id))

    def quit(self):
        self.driver.quit()

    def load_page(self, url: str):
        self.driver.get(url)
        self.wait()

    def switch_window(self, tab: int):
        self.driver.switch_to.window(self.driver.window_handles[tab])

    def get_open_windows_length(self):
        return len(self.driver.window_handles)

    def close_window(self):
        self.driver.close()

    def get_html_element(self, element: str) -> str:
        return self.driver.find_element(by=By.TAG_NAME, value=element).get_attribute("innerHTML")

    @staticmethod
    def wait(secs: float = 10):
        time.sleep(secs)

    @staticmethod
    def wait_for_download_completion(state_manager_id: UUID4):
        download_dir = os.path.join(os.getcwd(), f"temp/{state_manager_id}")
        """
        Aguarda a conclusão do download no diretório especificado.
        Retorna True se o arquivo foi baixado com sucesso antes do timeout, False caso contrário.
        """
        download_in_progress = True

        while download_in_progress:
            # Verifica os arquivos no diretório de download
            files = os.listdir(download_dir)
            # Filtra os arquivos que continuam sendo baixados (arquivos temporários)
            download_in_progress = any(file.endswith('.crdownload') or file.endswith('.part') for file in files)

            # Se não houver arquivos temporários, o download está completo
            if not download_in_progress:
                return True

            # Espera 1 segundo e verifica novamente
            wait(1)

        # Se o timeout for atingido e o download não tiver sido concluído
        return False
#
# class FormInteractionHelper:
#
#     def change_element_style(self, element, style_property, value):
#         script = f"arguments[0].style.{style_property} = '{value}';"
#         self.driver.execute_script(script, element)
