from bs4 import BeautifulSoup, Comment, ResultSet
import htmlmin


def remove_tags(html: str, soup: BeautifulSoup | None, tags) -> str:
    if not soup:
        soup = BeautifulSoup(html, "lxml")

    for tag in soup(tags):
        tag.extract()

    return str(soup)


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    # Remove tags desnecessárias
    for tag in soup(["script", "style", "head", "meta", "noscript", "footer", "header", "svg", "iframe", "p", "i"]):
        tag.extract()

    # Remoção de atributos e atributos vazios
    for tag in soup.find_all(True):
        attributes_to_remove = ["style", "data-select", "data-selected", "data-deselect",
                                "tabindex"]  # Adicione mais se necessário

        for attr in attributes_to_remove:
            if tag.has_attr(attr):
                del tag[attr]

        empty_attributes = [attr for attr, value in tag.attrs.items() if not value]
        for attr in empty_attributes:
            del tag[attr]

    # Retorna o HTML limpo
    return minify(str(soup))


def minify(html: str) -> str:
    return htmlmin.minify(html, remove_comments=True, remove_empty_space=True)


def find_elements_by(soup: BeautifulSoup, element_id: str = None, element_class: str = None) -> ResultSet:
    if element_class:
        return soup.find_all(class_=element_class)

    return soup.find_all(id=element_id)


def get_html_elements(html: str, elements_to_find) -> list:
    soup = BeautifulSoup(html, features="lxml")
    unique_elements = []

    for criteria in elements_to_find:
        matched_elements = find_elements_by(soup, criteria.get("id"), criteria.get("class"))

        for element in matched_elements:
            element_str = minify(str(element))  # Minifica o elemento para economizar espaço
            if element_str not in unique_elements:  # Verifica se já está na lista
                unique_elements.append(element_str)  # Mantém a ordem de inserção

    return unique_elements


def remove_elements_by_class_name(html: str, class_name: str) -> str:
    soup = BeautifulSoup(html, features="lxml")

    for element in soup.find_all(class_=class_name):
        element.decompose()

    return str(soup)
