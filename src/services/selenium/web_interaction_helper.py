from pydantic.v1 import UUID4
from selenium.common import ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from src.services.selenium.selenium_helper import SeleniumHelper


class WebInteractionHelper(SeleniumHelper):

    def __init__(self, state_manager_id: UUID4):
        super().__init__(state_manager_id)

    @staticmethod
    def click(element: WebElement):
        try:
            element.click()
        except ElementNotInteractableException:
            pass

    def wait_for_element_presence_by_id(self, element_id: str, timeout: float = 10):
        return WebDriverWait(self.driver, timeout).until(
            expected_conditions.presence_of_element_located((By.ID, element_id))
        )

    def wait_for_element_presence_by_xpath(self, xpath: str, timeout: float = 10):
        return WebDriverWait(self.driver, timeout).until(
            expected_conditions.presence_of_element_located((By.XPATH, xpath))
        )

    def wait_for_presence_of_all_elements_by_xpath(self, xpath, timeout: float = 10):
        return WebDriverWait(self.driver, timeout).until(
            expected_conditions.presence_of_all_elements_located((By.XPATH, xpath))
        )

    def remove_css_classes(self, element: WebElement):
        self.driver.execute_script("arguments[0].className = '';", element)

    def remove_inline_styles(self, element: WebElement):
        self.driver.execute_script("arguments[0].removeAttribute('style');", element)
