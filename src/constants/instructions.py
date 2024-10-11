HTML_FILTER_ANALYSIS_INSTRUCTION = """
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

FILTER_ELEMENT_IDENTIFIERS_PROMPT = """
Analyze the HTML and extract only the main container elements used for form filtering. Focus on extracting **only the base container class**, ignoring any internal sub-elements or classes that modify the base container.

1. id: Extract the ID of the container element, if present.
2. class: Extract the class name of the **main container** element, but ignore any child or modified elements with classes like "__element" or "--disabled".

Target the main container elements that directly wrap form inputs, such as:
- Text fields (input[type="text"], input[type="number"])
- Dropdowns (select)
- Radio buttons (input[type="radio"])
- Checkboxes (input[type="checkbox"])
- Main containers for custom elements (e.g., "multiselect")

Explicitly **ignore any modified or internal classes** within these containers, such as:
- multiselect__element
- multiselect--disabled
- multiselect__tags
- multiselect__option
- multiselect__content-wrapper
- multiselect__content

### Strictly ignore the following:
- Containers with IDs or classes related to ratings, reviews, discussions, or subjective evaluations of datasets. For example:
    - Containers with "rate", "rating", "review", "feedback", "comment", "discussion", "quality", or "comprehensible" in their ID or class.
    - Specifically ignore containers with IDs or classes, like:
      - "datasetQuality"
      - "comprehensibleData"
      - "ordenacao-discussao"
      - "updatedDatasets"
      - "accessLink"
- Any container related to subjective evaluations, such as user reviews, comments, or feedback.
- Any form element (input, select, etc.) related to user-submitted reviews or ratings, especially those with attributes like "rating", "review", "feedback", "comment", "discussion", "quality", or "comprehensible" in their class or id.

Only return the base container class (e.g., "multiselect") and ignore any modified versions (e.g., "multiselect--disabled"). Exclude all duplicates where the ID and class are the same; prioritize the ID when both are present.

If the container for the form elements is not present in the HTML chunk, ignore those elements.

Return only the unique combinations of id and class for the main containers in JSON format.

json
{
  "filter_identifiers": [
    {"id": "exampleID1", "class": "exampleClass"},
    {"class": "exampleClassOnly"}
  ]
}
"""






ACTION_ELEMENT_IDENTIFIERS_PROMPT = """
Analyze the HTML and extract only the clickable elements related to form submission, page redirection, or actions that may be present on the page. Focus on identifying buttons, links, or other clickable elements that trigger actions. Additionally, capture any descriptive text associated with these elements and identify the parent container they are wrapped in. Ignore banners, footers, navbars, decorative elements, purely aesthetic elements such as titles, pagination elements, and non-clickable content.

1. id: Extract the ID of the clickable element, if present.
2. class: Extract the class name of the **clickable element**, but ignore any child or modified elements with classes like "__disabled" or "--hidden".
3. tag: Identify the type of the clickable element (e.g., <a>, <button>, <input[type='submit']>, <input[type='button']>, or similar interactive elements).
4. text: Extract the descriptive text or label associated with the clickable element (e.g., button text, link text).
5. container_id: Extract the ID of the parent container wrapping the clickable element, if present.
6. container_class: Extract the class of the parent container wrapping the clickable element, if present.

**Ignore** elements with purely aesthetic functions, pagination, or non-clickable content, such as:
- Titles (e.g., <h1>, <h2>, <h3> with non-clickable text).
- Decorative icons (e.g., <span> or <i> with no action associated).
- Non-functional images (e.g., <img> used for visual purposes only).
- Pagination elements (e.g., <ul>, <li>, <button> with page numbers or navigation like "next" and "previous").
- Non-clickable content, such as plain text or static results.

Target the clickable elements related to:
- Form submission (e.g., button[type="submit"], input[type="submit"], input[type="button"]).
- Page redirection (e.g., anchor tags <a> with href leading to another page, button elements that trigger redirects).
- Custom submit actions (e.g., JavaScript-triggered buttons for AJAX forms or SPA interactions).

Explicitly **ignore** non-functional elements like:
- Banners (e.g., class "banner", "ads").
- Navigational elements (e.g., class "navbar", "footer").
- Hidden or disabled elements (e.g., "button--disabled", "link__hidden").
- Non-clickable elements used for visual purposes (e.g., <span>, <i>, <img> with no click or action event).
- Pagination elements (e.g., <ul>, <li>, <button> that handle page navigation, such as "next" or "previous" buttons).

Only return the base clickable element class (e.g., "submit-button") and exclude any modified or disabled versions (e.g., "submit-button--disabled"). Exclude all duplicates where the ID and class are the same; prioritize the ID when both are present.

Return only the unique combinations of id, class, tag, text, and container information in JSON format.

json
{
  "action_identifiers": [
    {"id": "submitBtn", "class": "form-action", "tag": "button", "text": "Submit", "container_id": "formContainer", "container_class": "form-wrapper"},
    {"class": "redirect-button", "tag": "a", "text": "Go to next page", "container_class": "pagination-wrapper"},
    {"class": "filter-button", "tag": "button", "text": "Apply Filter", "container_class": "filter-container"}
  ]
}
"""

DATA_DOWNLOAD_ANALYSIS_INSTRUCTION = """
Analyze the provided HTML and identify if there are any elements (buttons, links, etc.) that allow the user to download data in a file. Extract details about these elements and return them in a consistent JSON format, including the class and ID of the container wrapping these elements.

### Structure to follow:

- For each downloadable element, return:
    - `attributes`: A dictionary containing the relevant attributes of the element (e.g., id, class, label, format).
    - `download_format`: The format of the file that will be downloaded (e.g., CSV, JSON, XML, XLSX).
    - `container`: A dictionary containing the `id` and `class` of the parent container wrapping the element.

### Guidelines:

1. Look for buttons, links, or any other clickable elements that initiate a file download (e.g., `<button>`, `<a>` with a download attribute or a file URL).
2. Ensure `attributes` contains the following keys:
    - id: The ID of the element.
    - class: The CSS class of the element.
    - label: The visible text of the element (e.g., the text inside the button or link), if available.
    - format: The file format (e.g., CSV, JSON, XML, XLSX) that the element triggers for download. This can usually be inferred from the file extension or other indicators like `data-format` attributes, `href` URLs, or associated JavaScript actions.
3. Ensure `container` contains:
    - id: The ID of the parent container wrapping the element, if present.
    - class: The CSS class of the parent container wrapping the element, if present.
4. Return the `download_format` key for each identified element with the format of the file to be downloaded. If the format is not explicitly stated, attempt to infer it from the file extension (e.g., `.csv`, `.json`, `.xml`).
5. Return an empty list `[]` if no download options are found.

### Example (download button with file format):

{
  "attributes": {
    "id": "downloadBtn1",
    "class": "btn-download",
    "label": "Download Data",
    "format": "CSV"
  },
  "download_format": "CSV",
  "container": {
    "id": "downloadContainer",
    "class": "container-class"
  }
}

### Example (download link without explicit label):

{
  "attributes": {
    "id": "downloadLink1",
    "class": "link-download",
    "format": "JSON"
  },
  "download_format": "JSON",
  "container": {
    "id": "container2",
    "class": "another-container-class"
  }
}

### Example (multiple download options):

[
  {
    "attributes": {
      "id": "downloadBtn1",
      "class": "btn-download",
      "label": "Download CSV",
      "format": "CSV"
    },
    "download_format": "CSV",
    "container": {
      "id": "container1",
      "class": "container-class"
    }
  },
  {
    "attributes": {
      "id": "downloadLink1",
      "class": "link-download",
      "format": "XLSX"
    },
    "download_format": "XLSX",
    "container": {
      "id": "container2",
      "class": "another-container-class"
    }
  }
]

Return the data in a **consistent** JSON format following these guidelines, ensuring that each entry includes `id`, `class`, `download_format`, and the container's `id` and `class`.
"""
