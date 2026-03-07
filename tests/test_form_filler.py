from __future__ import annotations

from selenium.common.exceptions import ElementClickInterceptedException

from app.config import AppConfig
from app.form_filler import FormFiller
from app.form_parser import GridRow, ParsedPage, Question, QuestionType
from tests.conftest import FakeDriver, FakeElement


class StubBrowserManager:
    def __init__(self, config):
        self.driver = FakeDriver()

    def __enter__(self):
        return self.driver

    def __exit__(self, exc_type, exc, tb):
        return None


class StubParser:
    def __init__(self, container, driver=None):
        self._container = container
        self._driver = driver
        self._submit = FakeElement()
        original_click = self._submit.click

        def _click():
            original_click()
            if self._driver is not None:
                self._driver.current_url = "https://docs.google.com/forms/d/e/test/formResponse"

        self._submit.click = _click

    def parse_current_page(self, driver, page_index=0):
        return [
            Question(identifier="q1", prompt="Name", type=QuestionType.SHORT_TEXT),
            Question(identifier="q2", prompt="Choices", type=QuestionType.CHECKBOX, options=["A", "B", "C"]),
            Question(
                identifier="q3",
                prompt="Grid",
                type=QuestionType.GRID,
                rows=[GridRow(label="Row 1", options=["1", "2"])],
            ),
        ]

    def parse_page(self, driver, page_index=0):
        return ParsedPage(
            questions=self.parse_current_page(driver, page_index=page_index),
            containers=self.wait_for_question_containers(driver),
        )

    def wait_for_question_containers(self, driver):
        return [self._container["text"], self._container["checkbox"], self._container["grid"]]

    def find_next_button(self, driver):
        return None

    def find_submit_button(self, driver):
        return self._submit

    def find_checkbox_options(self, container):
        return container["options"]

    def find_radio_options(self, container):
        return container["options"]

    def find_dropdowns(self, container):
        return []

    def find_text_inputs(self, container):
        return [container["input"]]

    def find_textareas(self, container):
        return []

    def find_grid_rows(self, container):
        return container["rows"]

    def find_grid_row_options(self, row):
        return row["options"]


class StubStrategy:
    def choose_answer(self, question, preferred_name=None):
        if question.type == QuestionType.SHORT_TEXT:
            return preferred_name or "lorem ipsum"
        if question.type == QuestionType.CHECKBOX:
            return [0, 2]
        if question.type == QuestionType.GRID:
            return {0: 1}
        raise AssertionError("Unexpected question type")


def test_form_filler_populates_questions_and_submits():
    text_input = FakeElement(tag_name="input")
    checkbox_options = [FakeElement(), FakeElement(), FakeElement()]
    grid_options = [FakeElement(), FakeElement()]
    container = {
        "text": {"input": text_input},
        "checkbox": {"options": checkbox_options},
        "grid": {"rows": [{"options": grid_options}]},
    }

    browser_manager = StubBrowserManager(AppConfig(max_workers=1))
    parser = StubParser(container, driver=browser_manager.driver)
    filler = FormFiller(
        AppConfig(max_workers=1),
        browser_manager_cls=lambda config: browser_manager,
        parser=parser,
        strategy=StubStrategy(),
    )

    result = filler.fill_and_submit("https://docs.google.com/forms/d/e/test/viewform", 1, preferred_name="Vinh")

    assert result.succeeded == 1
    assert result.failed == 0
    assert text_input.cleared is True
    assert text_input.sent_keys == ["Vinh"]
    assert checkbox_options[0].clicked is True
    assert checkbox_options[2].clicked is True
    assert grid_options[1].clicked is True
    assert parser._submit.clicked is True


class MissingSubmitParser(StubParser):
    def find_submit_button(self, driver):
        return None


def test_form_filler_fails_if_no_navigation_or_submit_button():
    text_input = FakeElement(tag_name="input")
    container = {
        "text": {"input": text_input},
        "checkbox": {"options": [FakeElement(), FakeElement(), FakeElement()]},
        "grid": {"rows": [{"options": [FakeElement(), FakeElement()]}]},
    }

    browser_manager = StubBrowserManager(AppConfig(max_workers=1))
    filler = FormFiller(
        AppConfig(max_workers=1),
        browser_manager_cls=lambda config: browser_manager,
        parser=MissingSubmitParser(container, driver=browser_manager.driver),
        strategy=StubStrategy(),
    )

    result = filler.fill_and_submit("https://docs.google.com/forms/d/e/test/viewform", 1)

    assert result.succeeded == 0
    assert result.failed == 1
    assert "No next or submit button found" in result.errors[0]


class InterceptingSubmitButton(FakeElement):
    def click(self):
        raise ElementClickInterceptedException("intercepted")


class SubmitOnlyParser:
    def __init__(self, driver):
        self._driver = driver
        self._submit = InterceptingSubmitButton()

    def parse_current_page(self, driver, page_index=0):
        return []

    def parse_page(self, driver, page_index=0):
        return ParsedPage(questions=[], containers=[])

    def wait_for_question_containers(self, driver):
        return []

    def find_next_button(self, driver):
        return None

    def find_submit_button(self, driver):
        return self._submit


class ExecuteScriptBrowserManager:
    def __init__(self, config):
        self.driver = FakeDriver()

        def execute_script(script, element=None):
            if script == "arguments[0].click();":
                element.clicked = True
                self.driver.current_url = "https://docs.google.com/forms/d/e/test/formResponse"

        self.driver.execute_script = execute_script

    def __enter__(self):
        return self.driver

    def __exit__(self, exc_type, exc, tb):
        return None


def test_form_filler_falls_back_to_javascript_click_for_submit():
    browser_manager = ExecuteScriptBrowserManager(AppConfig(max_workers=1))
    filler = FormFiller(
        AppConfig(max_workers=1),
        browser_manager_cls=lambda config: browser_manager,
        parser=SubmitOnlyParser(browser_manager.driver),
        strategy=StubStrategy(),
    )

    result = filler.fill_and_submit("https://docs.google.com/forms/d/e/test/viewform", 1)

    assert result.succeeded == 1
    assert result.failed == 0
