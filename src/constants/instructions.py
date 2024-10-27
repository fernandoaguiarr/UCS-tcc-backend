HTML_FORM_FIELD_ANALYSIS = """
Analyze the provided HTML form elements and return their attributes, options, and the field type in a consistent JSON format.

### Structure to follow:

- For each form element, return:
  - `field_type`: A string that indicates whether the element is a "select", "multiselect", or a specific `input` type (e.g., "text", "email", "checkbox").
  - `attributes`: A dictionary containing all attributes of the element (e.g., id, class, name, type, placeholder, etc.).
  - `options`: A list containing all available options for dropdowns or multiselects (with label, value, disabled status, and CSS class).

### Guidelines:

1. Always return `field_type`, `attributes`, and `options` keys, even if one of them is empty.
2. Ensure `field_type` clearly specifies the type of field:
   - `"select"` for a regular `<select>` element.
   - `"multiselect"` for a `<select>` element with the `multiple` attribute.
   - `"input"` followed by the value of the `type` attribute for `<input>` elements (e.g., `"input-text"`, `"input-email"`, `"input-checkbox"`).
3. Ensure `attributes` contains all relevant HTML attributes, like:
   - id
   - class
   - name
   - type
   - placeholder
   - maxlength
   - min, max, step
   - aria-label
4. Ensure `options` includes:
   - label: The visible text for the option.
   - value: The value associated with the option, if available.
   - disabled: Whether the option is disabled.
   - class: The CSS class of the option, if available.
5. Return an empty list `[]` for `options` if no options are present, and an empty dictionary `{}` for `attributes` if no attributes are found.

### Example (select element with options):

```json
{
  "field_type": "select",
  "attributes": {
    "id": "exampleID",
    "class": "exampleClass",
    "name": "dropdown"
  },
  "options": [
    {"label": "Option 1", "value": "1", "disabled": false, "class": "optionClass"},
    {"label": "Option 2", "value": "2", "disabled": true, "class": "optionClass"}
  ]
}

"""

HTML_FILTER_CONTAINER_IDENTIFIERS = """
Analyze the HTML and extract only the main container elements used for **form filtering**. Focus on extracting **only the base container class**, ensuring that the container and its related elements (e.g., form fields) are treated as a single unit when relevant. Ignore any internal sub-elements or classes that modify the base container.

1. id: Extract the ID of the container element if present, and ensure that it is associated with the relevant form input or filtering element.
2. class: Extract the class name of the **main container** element, but ignore any child or modified elements with classes like "__element" or "--disabled".

Target the main container elements that directly wrap form inputs used for filtering, such as:
- Text fields (input[type="text"], input[type="number"])
- Dropdowns (select)
- Radio buttons (input[type="radio"])
- Checkboxes (input[type="checkbox"])
- Main containers for custom elements (e.g., "multiselect")

Explicitly **ignore** any elements or containers related to user feedback, ratings, comments, discussions, sorting/ordering mechanisms, or navigation elements like navbars. This includes:
- Elements with IDs, classes, or attributes containing terms like "rate", "rating", "review", "feedback", "comment", "discussion", "quality", "comprehensible", "accessLink", "sort", "order", "ranking", "nav", "navbar", "navigation", or similar terms.
- Containers and elements with IDs or classes like:
  - "datasetQuality"
  - "comprehensibleData"
  - "ordenacao-discussao"
  - "updatedDatasets"
  - "sortBy"
  - "rankingPanel"
  - "reviewSection"
  - "navbar"
  - "menu-navigation"

### Exclusion Criteria:
- **Ignore containers** that include elements related to feedback, discussions (e.g., forums or reviews), subjective evaluations, sorting mechanisms, or navigation bars.
- Do not include elements like input fields, text areas, or buttons related to user reviews, comments, feedback, sorting options, or navigation.
- Ensure that when a container directly wraps a form input or filtering element, they are considered together, avoiding separation of the container and its main element.
- **Only include** containers that are directly related to filtering criteria like search parameters, categories, dates, or other filtering mechanisms.

Return only the base container class (e.g., "multiselect") and ignore any modified versions (e.g., "multiselect--disabled"). Exclude all duplicates where the ID and class are the same; prioritize the ID when both are present.

If the container for the filtering form elements is not present in the HTML chunk, ignore those elements.

Return only the unique combinations of id and class for the main containers in JSON format.

json
{
  "filter_identifiers": [
    {"id": "exampleID1", "class": "exampleClass"},
    {"class": "exampleClassOnly"}
  ]
}
"""

HTML_ACTIONABLE_ELEMENT_ANALYSIS = """
Analyze the HTML and extract elements related to **form submission, page redirection, actions**, or **data downloads**. Focus on identifying buttons, links, or other clickable elements that trigger actions or initiate downloads. Additionally, capture any descriptive text associated with these elements.

1. id: Extract the ID of the clickable element itself, not of its parent or surrounding elements. Focus on the element where the action is directly initiated, such as the `<a>` tag.
2. class: Extract the class name of the **clickable element**, but ignore any child or modified elements with classes like "__disabled" or "--hidden".
3. tag: Identify the type of the clickable element (e.g., <a>, <button>, <input[type='submit']>, <input[type='button']>, or similar interactive elements).
4. text: Extract the descriptive text or label associated with the clickable element (e.g., button text, link text).
5. download_format: If the element initiates a file download, extract the format of the file (e.g., CSV, JSON, XML, XLSX).
6. action_type: Distinguish the type of action the element performs:
    - Use "download" if the element initiates a file download.
    - Use "redirect" if the element leads to another page or triggers navigation.

### Exclusion Criteria:
- **Ignore elements** with purely aesthetic functions, pagination, or non-clickable content, such as:
  - Titles (e.g., <h1>, <h2>, <h3> with non-clickable text).
  - Decorative icons (e.g., <span> or <i> with no action associated).
  - Non-functional images (e.g., <img> used for visual purposes only).
  - Pagination elements (e.g., <ul>, <li>, <button> with page numbers or navigation like "next" and "previous").
  - Static or non-interactive content.

### Explicitly ignore the following:
- **Ignore `<form>` tags** themselves unless analyzing the **buttons or inputs within them** that are directly related to form submission actions:
  - Focus only on `<button>` elements or `<input>` elements with `type="submit"` or `type="button"` inside the form.
  - Do not consider the `<form>` tag as an action by itself.
- **Ignore form elements** that are not directly related to form submission actions:
  - Exclude elements like `<select>`, `<textarea>`, `<input>` (including `type="text"`, `type="checkbox"`, `type="radio"`, `type="search"`, etc.), unless they are of `type="submit"` or `type="button"`.
- **Ignore elements related to cookies or consent management**:
  - Ignore any elements or containers that include IDs, classes, other attributes, or visible text containing terms like:
    - "cookie", "consent", "accept", "reject", "agree", "decline", "cookie-banner", "cookie-settings", "privacy-policy", "gdpr", "compliance", or any variations of these terms.
    - This applies to attributes like data-*, aria-label, title, alt, or any other attribute that may indicate relevance to consent management.
  - Additionally, ignore any elements where the visible text (e.g., inner text of buttons, links, or labels) contains phrases like "Accept Cookies", "Manage Cookies", "Cookie Settings", "This site uses cookies", or similar notices.
- **Ignore elements related to menus or navigation trees**:
  - Ignore elements that include IDs, classes, or visible text containing terms like:
    - "menu", "tree", "jstree", "navigation", "nav", "dropdown", "sidebar", "accordion", "expand", "collapse", "panel", "tabs", or similar terms.
    - This applies to elements with classes like "treeview", "menu-item", "nav-item", "accordion-panel", or any other structure related to hierarchical navigation.
  - Exclude elements that control or are part of expandable/collapsible menus, dropdowns, or tab navigations.

### Target Elements:
- **Form submission** (e.g., button[type="submit"], input[type="submit"], input[type="button"]).
- **Page redirection** (e.g., anchor tags <a> with href leading to another page, button elements that trigger redirects).
- **Custom submit actions** (e.g., JavaScript-triggered buttons for AJAX forms or SPA interactions).
- **Data download elements** (e.g., buttons or links with a download attribute or file URLs that initiate a download).
  - Ensure that download_format is included if a file format can be inferred (e.g., CSV, JSON, XML, XLSX).

Only return the base clickable element class (e.g., "submit-button") and exclude any modified or disabled versions (e.g., "submit-button--disabled"). Exclude all duplicates where the ID and class are the same; prioritize the ID when both are present.

Return the results in a **consistent** JSON format, ensuring each entry includes id, class, tag, text, action_type, and download_format (if applicable).

json
{
  "actions": [
    {
      "id": "j1_5_anchor",
      "class": "jstree-anchor",
      "tag": "a",
      "text": "estimativa_populacao_1992_ods.zip",
      "action_type": "download",
      "download_format": "ZIP"
    },
    {
      "id": "j1_6_anchor",
      "class": "jstree-anchor",
      "tag": "a",
      "text": "estimativa_populacao_1992_xls.zip",
      "action_type": "download",
      "download_format": "ZIP"
    },
    {
      "id": "j1_7_anchor",
      "class": "jstree-anchor",
      "tag": "a",
      "text": "estimativa_populacao_1992.pdf",
      "action_type": "download",
      "download_format": "PDF"
    }
  ]
}
"""
