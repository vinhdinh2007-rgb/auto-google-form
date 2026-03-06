from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from .config import AppConfig


class QuestionType(str, Enum):
    RADIO = "radio"
    CHECKBOX = "checkbox"
    DROPDOWN = "dropdown"
    SHORT_TEXT = "short_text"
    LONG_TEXT = "long_text"
    LINEAR_SCALE = "linear_scale"
    GRID = "grid"


@dataclass
class GridRow:
    label: str
    options: list[str] = field(default_factory=list)


@dataclass
class Question:
    identifier: str
    prompt: str
    type: QuestionType
    required: bool = False
    options: list[str] = field(default_factory=list)
    rows: list[GridRow] = field(default_factory=list)
    page: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class FormParser:
    QUESTION_SELECTORS = [
        '[data-question-container="true"]',
        ".Qr7Oae",
        'div[role="listitem"]',
    ]
    PROMPT_SELECTORS = [
        "[data-question-title]",
        '[role="heading"]',
        ".M7eMe",
        ".HoXoMd",
    ]
    REQUIRED_SELECTORS = [
        "[data-required]",
        '[aria-label*="Required"]',
        ".vnumgf",
    ]
    RADIO_OPTION_SELECTORS = [
        '[data-option-kind="radio"]',
        '[role="radio"]',
        '[jscontroller="EcW08c"]',
    ]
    CHECKBOX_OPTION_SELECTORS = [
        '[data-option-kind="checkbox"]',
        '[role="checkbox"]',
        '[jscontroller="D8e5bc"]',
    ]
    DROPDOWN_SELECTORS = [
        "select",
        '[role="listbox"]',
        '[data-question-type="dropdown"]',
    ]
    TEXT_INPUT_SELECTORS = [
        'input[type="text"]',
        'input[type="email"]',
    ]
    TEXTAREA_SELECTORS = ["textarea"]
    GRID_ROW_SELECTORS = [
        "[data-grid-row]",
        ".appsMaterialWizToggleRadiogroupGroupContainer",
    ]
    OPTION_LABEL_SELECTORS = [
        "[data-option-label]",
        ".aDTYNe",
        ".docssharedWizToggleLabeledLabelText",
        ".OA0qNb",
    ]
    NEXT_BUTTON_XPATHS = [
        "//span[normalize-space()='Next']/ancestor::*[@role='button'][1]",
        "//span[normalize-space()='Sau']/ancestor::*[@role='button'][1]",
    ]
    SUBMIT_BUTTON_XPATHS = [
        "//*[@role='button' and @aria-label='Submit']",
        "//span[normalize-space()='Submit']/ancestor::*[@role='button'][1]",
        "//span[normalize-space()='Gui']/ancestor::*[@role='button'][1]",
    ]

    def __init__(self, config: AppConfig):
        self.config = config

    def parse(self, driver: WebDriver, url: str) -> list[Question]:
        driver.get(url)
        questions: list[Question] = []
        page_index = 0
        while True:
            questions.extend(self.parse_current_page(driver, page_index=page_index))
            next_button = self.find_next_button(driver)
            if next_button is None:
                break
            next_button.click()
            page_index += 1
        return questions

    def parse_current_page(self, driver: WebDriver, page_index: int = 0) -> list[Question]:
        containers = self.wait_for_question_containers(driver)
        return [
            self._parse_question(container, order=index, page_index=page_index)
            for index, container in enumerate(containers)
        ]

    def wait_for_question_containers(self, driver: WebDriver):
        wait = WebDriverWait(driver, self.config.wait_timeout)

        def _locate(active_driver: WebDriver):
            for selector in self.QUESTION_SELECTORS:
                elements = active_driver.find_elements(By.CSS_SELECTOR, selector)
                if selector == 'div[role="listitem"]':
                    elements = self._filter_top_level_list_items(elements)
                if elements:
                    return elements
            return False

        try:
            return wait.until(_locate)
        except TimeoutException:
            return []

    def find_next_button(self, driver: WebDriver):
        return self._find_first_xpath(driver, self.NEXT_BUTTON_XPATHS)

    def find_submit_button(self, driver: WebDriver):
        return self._find_first_xpath(driver, self.SUBMIT_BUTTON_XPATHS)

    def find_radio_options(self, container):
        return self._find_elements_any(container, self.RADIO_OPTION_SELECTORS)

    def find_checkbox_options(self, container):
        return self._find_elements_any(container, self.CHECKBOX_OPTION_SELECTORS)

    def find_dropdowns(self, container):
        return self._find_elements_any(container, self.DROPDOWN_SELECTORS)

    def find_text_inputs(self, container):
        return self._find_elements_any(container, self.TEXT_INPUT_SELECTORS)

    def find_textareas(self, container):
        return self._find_elements_any(container, self.TEXTAREA_SELECTORS)

    def find_grid_rows(self, container):
        return self._find_elements_any(container, self.GRID_ROW_SELECTORS)

    def find_grid_row_options(self, row):
        return self.find_radio_options(row) or self._find_elements_any(
            row,
            ['[data-option-kind="radio"]', "[data-option]"],
        )

    def _parse_question(self, container, order: int, page_index: int) -> Question:
        question = Question(
            identifier=f"page-{page_index}-question-{order}",
            prompt=self._extract_prompt(container) or f"Question {order + 1}",
            type=self._detect_question_type(container),
            required=self._is_required(container),
            page=page_index,
        )

        if question.type == QuestionType.RADIO:
            question.options = self._collect_option_labels(self.find_radio_options(container))
        elif question.type == QuestionType.CHECKBOX:
            question.options = self._collect_option_labels(self.find_checkbox_options(container))
        elif question.type == QuestionType.DROPDOWN:
            question.options = self._collect_dropdown_labels(container)
        elif question.type == QuestionType.LINEAR_SCALE:
            question.options = self._collect_option_labels(self.find_radio_options(container))
        elif question.type == QuestionType.GRID:
            rows = []
            for row in self.find_grid_rows(container):
                rows.append(
                    GridRow(
                        label=self._extract_prompt(row) or self._extract_text(row) or "Row",
                        options=self._collect_option_labels(self.find_grid_row_options(row)),
                    )
                )
            question.rows = rows
            if rows:
                question.options = rows[0].options

        return question

    def _detect_question_type(self, container) -> QuestionType:
        declared = (container.get_attribute("data-question-type") or "").strip().lower()
        if declared:
            return {
                "radio": QuestionType.RADIO,
                "checkbox": QuestionType.CHECKBOX,
                "dropdown": QuestionType.DROPDOWN,
                "short_text": QuestionType.SHORT_TEXT,
                "long_text": QuestionType.LONG_TEXT,
                "linear_scale": QuestionType.LINEAR_SCALE,
                "grid": QuestionType.GRID,
            }.get(declared, QuestionType.RADIO)

        if self.find_grid_rows(container):
            return QuestionType.GRID
        if self.find_textareas(container):
            return QuestionType.LONG_TEXT
        if self.find_text_inputs(container):
            return QuestionType.SHORT_TEXT
        if self.find_checkbox_options(container):
            return QuestionType.CHECKBOX
        if self.find_dropdowns(container):
            return QuestionType.DROPDOWN

        radio_options = self.find_radio_options(container)
        if radio_options and self._looks_like_linear_scale(radio_options):
            return QuestionType.LINEAR_SCALE
        return QuestionType.RADIO

    def _looks_like_linear_scale(self, radio_options) -> bool:
        labels = [self._extract_option_label(option) for option in radio_options]
        numeric = [label for label in labels if label.isdigit()]
        return len(numeric) == len(labels) and len(labels) >= 3

    def _extract_prompt(self, element) -> str:
        for selector in self.PROMPT_SELECTORS:
            children = element.find_elements(By.CSS_SELECTOR, selector)
            if children:
                text = self._extract_text(children[0])
                if text:
                    return text
        return self._extract_text(element)

    def _is_required(self, element) -> bool:
        aria_required = (element.get_attribute("aria-required") or "").strip().lower()
        if aria_required == "true":
            return True
        for selector in self.REQUIRED_SELECTORS:
            if element.find_elements(By.CSS_SELECTOR, selector):
                return True
        return False

    def _collect_option_labels(self, option_elements) -> list[str]:
        labels = [self._extract_option_label(element) for element in option_elements]
        return [label for label in labels if label]

    def _collect_dropdown_labels(self, container) -> list[str]:
        dropdowns = self.find_dropdowns(container)
        if not dropdowns:
            return []
        dropdown = dropdowns[0]
        option_elements = dropdown.find_elements(By.TAG_NAME, "option")
        if option_elements:
            return [self._extract_text(option) for option in option_elements if self._extract_text(option)]
        return self._collect_option_labels(
            dropdown.find_elements(By.CSS_SELECTOR, '[role="option"], [data-option]')
        )

    def _extract_option_label(self, element) -> str:
        for selector in self.OPTION_LABEL_SELECTORS:
            children = element.find_elements(By.CSS_SELECTOR, selector)
            if children:
                label = self._extract_text(children[0])
                if label:
                    return label
        return self._extract_text(element)

    def _extract_text(self, element) -> str:
        text = getattr(element, "text", "") or ""
        text = text.strip()
        if text:
            return text
        for attribute in ("aria-label", "value", "data-label"):
            value = element.get_attribute(attribute)
            if value:
                return value.strip()
        return ""

    def _find_elements_any(self, element, selectors: list[str]):
        for selector in selectors:
            elements = element.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                return elements
        return []

    def _find_first_xpath(self, driver: WebDriver, xpaths: list[str]):
        for xpath in xpaths:
            elements = driver.find_elements(By.XPATH, xpath)
            if elements:
                return elements[0]
        return None

    def _filter_top_level_list_items(self, elements):
        filtered = []
        for element in elements:
            classes = (element.get_attribute("class") or "").split()
            if "Qr7Oae" in classes or "freebirdFormviewerViewNumberedItemContainer" in classes:
                filtered.append(element)
        return filtered or elements
