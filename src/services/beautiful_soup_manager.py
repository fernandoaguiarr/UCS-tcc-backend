import htmlmin
from bs4 import BeautifulSoup, ResultSet


class BeautifulSoupManager:
    def __init__(self, html: str, features: str = "lxml"):
        self.html = html
        self.soup = BeautifulSoup(html, features=features)

    def find_element_by_id(self, element_id: str):
        return self.soup.find(id=element_id)

    def find_element_by_class(self, element_class: str):
        return self.soup.find(class_=element_class)

    def find_elements_by_class(self, element_class: str) -> ResultSet:
        return self.soup.find_all(class_=element_class)

    def remove_element_by_class(self, element_class: str, remove_all: bool = False):
        if remove_all:
            for element in self.find_element_by_class(element_class):
                element.decompose()
        else:
            element = self.find_element_by_class(element_class)
            element.decompose()

    def remove_element_by_id(self, element_id, remove_all: bool = False):
        if remove_all:
            for element in self.soup.find_all(class_=element_id):
                element.decompose()
        else:
            element = self.find_element_by_class(element_id)
            element.decompose()

    def extract_unique_html_elements(self, search_criteria):
        elements = []
        seen_elements = set()

        for criteria in search_criteria:
            element_id = criteria.get("id")
            element_class = criteria.get("class")

            if element_id:
                matched_elements = [self.find_element_by_id(element_id)]
            else:
                matched_elements = self.find_elements_by_class(element_class)

            for element in matched_elements:
                element = self.minify(str(element))

                if element not in seen_elements:
                    elements.append(element)
                    seen_elements.add(element)

        return elements

    def remove_tag(self, tags: str | list):
        if isinstance(tags, str):
            tags = [tags]

        for tag in self.soup(tags):
            tag.decompose()

    def remove_attribute(self, attributes: str | list, remove_empty_attributes: bool = False):
        if isinstance(attributes, str):
            attributes = [attributes]

        for tag in self.soup.find_all(True):
            for attr in attributes:
                if tag.has_attr(attr):
                    del tag[attr]

            if remove_empty_attributes:
                tag.attrs = {attr: value for attr, value in tag.attrs.items() if value}

    def clean_soup(
            self,
            tags_to_remove=None,
            attributes_to_remove=None
    ):

        if tags_to_remove is None:
            tags_to_remove = ["script", "style", "head", "meta", "noscript", "footer", "header", "svg", "iframe", "p",
                              "i"]
        if tags_to_remove is None:
            tags_to_remove = ["script", "style", "head", "meta", "noscript", "footer", "header", "svg", "iframe", "p",
                              "i"]
        if len(tags_to_remove): self.remove_tag(tags_to_remove)
        if len(attributes_to_remove): self.remove_attribute(attributes_to_remove)

    @staticmethod
    def minify(html: str) -> str:
        return htmlmin.minify(html, remove_empty_space=True, remove_comments=True)

    def beautiful_soup_to_str(self, minify: bool = False) -> str:
        html = str(self.soup)
        return self.minify(html) if minify else html
