from uuid import UUID

from selenium.common import ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from src.services.selenium.selenium_helper import SeleniumHelper


class WebInteractionHelper(SeleniumHelper):

    def __init__(self, state_manager_id: UUID):
        super().__init__(state_manager_id)

    @staticmethod
    def click(element: WebElement) -> bool:
        try:
            element.click()
            return True
        except ElementNotInteractableException:
            return False

    @staticmethod
    def fill_input_field(element: WebElement, value):
        element.clear()
        element.send_keys(value)

    @staticmethod
    def create_default_xpath_sentence(attributes, function: str = "contains") -> str | None:
        if "id" in attributes and attributes["id"]:
            return f"{function}(@id, '{attributes['id']}')"

        elif "class" in attributes and attributes["class"]:
            return f"{function}(@class, '{attributes['class']}')"

        return None

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

    def click_using_javascript(self, element):
        self.driver.execute_script("arguments[0].click();", element)
