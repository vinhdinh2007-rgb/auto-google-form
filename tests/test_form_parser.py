from __future__ import annotations

from selenium.webdriver.common.by import By

from app.config import AppConfig
from app.form_parser import FormParser, QuestionType
from tests.conftest import FakeDriver, FakeElement


def build_option(label: str, kind: str = "radio") -> FakeElement:
    label_element = FakeElement(text=label)
    return FakeElement(
        text=label,
        attributes={"data-option-kind": kind},
        selectors={
            (By.CSS_SELECTOR, "[data-option-label]"): [label_element],
        },
    )


def build_question(kind: str, prompt: str, options=None, rows=None) -> FakeElement:
    prompt_element = FakeElement(text=prompt)
    selectors = {
        (By.CSS_SELECTOR, "[data-question-title]"): [prompt_element],
    }
    attributes = {"data-question-type": kind}

    if kind == "radio":
        selectors[(By.CSS_SELECTOR, '[data-option-kind="radio"]')] = options or []
    elif kind == "checkbox":
        selectors[(By.CSS_SELECTOR, '[data-option-kind="checkbox"]')] = options or []
    elif kind == "dropdown":
        dropdown = FakeElement(
            tag_name="select",
            selectors={(By.TAG_NAME, "option"): options or []},
        )
        selectors[(By.CSS_SELECTOR, "select")] = [dropdown]
    elif kind == "short_text":
        selectors[(By.CSS_SELECTOR, 'input[type="text"]')] = [FakeElement(tag_name="input")]
    elif kind == "long_text":
        selectors[(By.CSS_SELECTOR, "textarea")] = [FakeElement(tag_name="textarea")]
    elif kind == "linear_scale":
        selectors[(By.CSS_SELECTOR, '[data-option-kind="radio"]')] = options or []
    elif kind == "grid":
        selectors[(By.CSS_SELECTOR, "[data-grid-row]")] = rows or []

    return FakeElement(text=prompt, attributes=attributes, selectors=selectors)


def build_grid_row(label: str, options) -> FakeElement:
    prompt_element = FakeElement(text=label)
    return FakeElement(
        text=label,
        selectors={
            (By.CSS_SELECTOR, "[data-question-title]"): [prompt_element],
            (By.CSS_SELECTOR, '[data-option-kind="radio"]'): options,
        },
    )


def test_form_parser_detects_all_supported_question_types():
    parser = FormParser(AppConfig(wait_timeout=1))

    grid_row = build_grid_row("Row 1", [build_option("One"), build_option("Two")])
    containers = [
        build_question("radio", "Radio", [build_option("Yes"), build_option("No")]),
        build_question("checkbox", "Checkbox", [build_option("A", "checkbox"), build_option("B", "checkbox")]),
        build_question("dropdown", "Dropdown", [FakeElement(text="First", tag_name="option"), FakeElement(text="Second", tag_name="option")]),
        build_question("short_text", "Short Text"),
        build_question("long_text", "Long Text"),
        build_question("linear_scale", "Scale", [build_option("1"), build_option("2"), build_option("3")]),
        build_question("grid", "Grid", rows=[grid_row]),
    ]
    driver = FakeDriver(selectors={(By.CSS_SELECTOR, '[data-question-container="true"]'): containers})

    questions = parser.parse_current_page(driver)

    assert [question.type for question in questions] == [
        QuestionType.RADIO,
        QuestionType.CHECKBOX,
        QuestionType.DROPDOWN,
        QuestionType.SHORT_TEXT,
        QuestionType.LONG_TEXT,
        QuestionType.LINEAR_SCALE,
        QuestionType.GRID,
    ]
    assert questions[0].options == ["Yes", "No"]
    assert questions[2].options == ["First", "Second"]
    assert questions[6].rows[0].label == "Row 1"
    assert questions[6].rows[0].options == ["One", "Two"]


def test_form_parser_prefers_top_level_question_containers():
    parser = FormParser(AppConfig(wait_timeout=1))
    nested_option = FakeElement(text="Nested", attributes={"class": "eBFwI"})
    top_level = build_question("radio", "Radio", [build_option("Yes"), build_option("No")])
    driver = FakeDriver(
        selectors={
            (By.CSS_SELECTOR, ".Qr7Oae"): [top_level],
            (By.CSS_SELECTOR, 'div[role="listitem"]'): [top_level, nested_option],
        }
    )

    containers = parser.wait_for_question_containers(driver)

    assert containers == [top_level]


def test_form_parser_uses_most_complete_container_match():
    parser = FormParser(AppConfig(wait_timeout=1))
    partial_matches = [
        build_question("radio", "Radio 1", [build_option("Yes"), build_option("No")]),
        build_question("radio", "Radio 2", [build_option("Yes"), build_option("No")]),
    ]
    complete_matches = [
        build_question("radio", "Radio 1", [build_option("Yes"), build_option("No")]),
        build_question("radio", "Radio 2", [build_option("Yes"), build_option("No")]),
        build_question("short_text", "Name"),
        build_question("long_text", "Details"),
    ]
    driver = FakeDriver(
        selectors={
            (By.CSS_SELECTOR, ".Qr7Oae"): partial_matches,
            (By.CSS_SELECTOR, 'div[role="listitem"]'): complete_matches,
        }
    )

    containers = parser.wait_for_question_containers(driver)

    assert containers == complete_matches


def test_form_parser_finds_submit_button_by_aria_label():
    parser = FormParser(AppConfig(wait_timeout=1))
    submit_button = FakeElement(attributes={"aria-label": "Submit"})
    driver = FakeDriver(
        selectors={
            (By.XPATH, "//*[@role='button' and @aria-label='Submit']"): [submit_button],
        }
    )

    found = parser.find_submit_button(driver)

    assert found is submit_button
