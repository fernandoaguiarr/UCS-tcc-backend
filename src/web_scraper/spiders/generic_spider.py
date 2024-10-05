import time

import scrapy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def get_browser_options() -> Options:
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Executa em modo headless
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-running-insecure-content')

    return chrome_options


class GenericSpider(scrapy.Spider):
    name = "generic_spider"
    allowed_domains = ["*"]
    start_urls = []

    def __init__(self, url: str, **kwargs):
        super(GenericSpider, self).__init__(**kwargs)
        self.start_urls = [url]
        self.driver = webdriver.Chrome(options=get_browser_options())

    def parse(self, response, **kwargs):
        self.driver.get(response.url)
        time.sleep(10)

        content = self.driver.find_element(by=By.TAG_NAME, value="body").get_attribute("innerHTML")
        self.driver.quit()

        yield {
            'content': content
        }

