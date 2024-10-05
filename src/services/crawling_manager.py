import os
import sys
import concurrent.futures

from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.signalmanager import dispatcher

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from src.web_scraper.spiders.generic_spider import GenericSpider


class CrawlingManager:

    def crawl(self, url: str):
        process = CrawlerProcess(get_project_settings())
        results = []

        def spider_results(item, response, spider):
            results.append(item)  # Coloca o item (resultado) na fila

        dispatcher.connect(spider_results, signal=signals.item_scraped)

        process.crawl(GenericSpider, url=url)
        process.start()  # Inicia o crawler

        return results[0]

    def start(self, url: str):
        with concurrent.futures.ProcessPoolExecutor() as executor:
            future = executor.submit(self.crawl, url=url)
            return future.result()["content"]
