from __future__ import annotations

import cProfile
import logging
import pstats
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from io import StringIO
from time import perf_counter

from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait

from .browser import BrowserManager
from .config import AppConfig
from .form_parser import FormParser, Question, QuestionType
from .strategy import RandomStrategy


logger = logging.getLogger(__name__)


@dataclass
class FillResult:
    requested: int
    succeeded: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0


class FormFiller:
    def __init__(
        self,
        config: AppConfig,
        browser_manager_cls=BrowserManager,
        parser: FormParser | None = None,
        strategy: RandomStrategy | None = None,
    ):
        self.config = config
        self.browser_manager_cls = browser_manager_cls
        self.parser = parser or FormParser(config)
        self.strategy = strategy or RandomStrategy()

    def fill_and_submit(self, url: str, count: int, preferred_name: str | None = None) -> FillResult:
        started_at = perf_counter()
        result = FillResult(requested=count)
        workers = min(self.config.max_workers, count) if count > 0 else 1
        chunks = self._build_chunks(count, workers)

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(self._process_chunk, url, chunk, preferred_name)
                for chunk in chunks
                if chunk
            ]
            for future in as_completed(futures):
                chunk_result = future.result()
                result.succeeded += chunk_result.succeeded
                result.failed += chunk_result.failed
                result.errors.extend(chunk_result.errors)

        result.duration_seconds = perf_counter() - started_at
        return result

    def _build_chunks(self, count: int, workers: int) -> list[list[int]]:
        chunks = [[] for _ in range(max(1, workers))]
        for submission_id in range(1, count + 1):
            chunks[(submission_id - 1) % len(chunks)].append(submission_id)
        return chunks

    def _process_chunk(self, url: str, submission_ids: list[int], preferred_name: str | None) -> FillResult:
        result = FillResult(requested=len(submission_ids))
        with self.browser_manager_cls(self.config) as driver:
            for submission_id in submission_ids:
                try:
                    self._submit_once(driver, url, submission_id, preferred_name)
                    result.succeeded += 1
                except Exception as exc:
                    result.failed += 1
                    message = f"Submission {submission_id} failed: {exc}"
                    result.errors.append(message)
                    logger.exception(message)
        return result

    def _submit_once(
        self,
        driver,
        url: str,
        submission_id: int,
        preferred_name: str | None,
    ) -> None:
        if self.config.enable_profiling:
            profiler = cProfile.Profile()
            profiler.enable()
            try:
                self._submit_once_core(driver, url, preferred_name)
            finally:
                profiler.disable()
                self._log_profile(submission_id, profiler)
        else:
            self._submit_once_core(driver, url, preferred_name)

    def _submit_once_core(self, driver, url: str, preferred_name: str | None) -> None:
        driver.get(url)
        page_index = 0
        while True:
            parsed_page = self.parser.parse_page(driver, page_index=page_index)
            for question, container in zip(parsed_page.questions, parsed_page.containers):
                answer = self.strategy.choose_answer(question, preferred_name=preferred_name)
                self._apply_answer(container, question, answer)

            if self._advance_to_next_page(driver):
                page_index += 1
                continue
            self._submit_current_page(driver)
            return

    def _apply_answer(self, container, question: Question, answer) -> None:
        if question.type in {QuestionType.RADIO, QuestionType.LINEAR_SCALE}:
            options = self.parser.find_radio_options(container)
            options[answer].click()
            return
        if question.type == QuestionType.CHECKBOX:
            options = self.parser.find_checkbox_options(container)
            for index in answer:
                options[index].click()
            return
        if question.type == QuestionType.DROPDOWN:
            self._fill_dropdown(container, answer)
            return
        if question.type in {QuestionType.SHORT_TEXT, QuestionType.LONG_TEXT}:
            field = self._find_text_field(container, question.type)
            field.clear()
            field.send_keys(answer)
            return
        if question.type == QuestionType.GRID:
            rows = self.parser.find_grid_rows(container)
            for row_index, column_index in answer.items():
                options = self.parser.find_grid_row_options(rows[row_index])
                options[column_index].click()
            return
        raise ValueError(f"Unsupported question type: {question.type}")

    def _fill_dropdown(self, container, answer_index: int) -> None:
        dropdown = self.parser.find_dropdowns(container)[0]
        if getattr(dropdown, "tag_name", "").lower() == "select":
            Select(dropdown).select_by_index(answer_index)
            return
        dropdown.click()
        options = dropdown.find_elements(By.CSS_SELECTOR, '[role="option"], [data-option]')
        options[answer_index].click()

    def _find_text_field(self, container, question_type: QuestionType):
        if question_type == QuestionType.LONG_TEXT:
            return self.parser.find_textareas(container)[0]
        inputs = self.parser.find_text_inputs(container)
        if not inputs:
            raise ValueError("Text input field not found")
        return inputs[0]

    def _log_profile(self, submission_id: int, profiler: cProfile.Profile) -> None:
        stats_stream = StringIO()
        stats = pstats.Stats(profiler, stream=stats_stream).sort_stats("cumtime")
        stats.print_stats(10)
        logger.info("Submission %s profile:\n%s", submission_id, stats_stream.getvalue())

    def _advance_to_next_page(self, driver) -> bool:
        next_button = self.parser.find_next_button(driver)
        submit_button = self.parser.find_submit_button(driver)
        if next_button is None or submit_button is not None:
            return False
        self._click_element(driver, next_button)
        return True

    def _submit_current_page(self, driver) -> None:
        submit_button = self.parser.find_submit_button(driver)
        if submit_button is None:
            raise RuntimeError("No next or submit button found after answering the form")
        self._click_element(driver, submit_button)
        self._verify_submission_completed(driver)

    def _verify_submission_completed(self, driver) -> None:
        def _submission_visible(active_driver):
            current_url = active_driver.current_url or ""
            if "formResponse" in current_url:
                return True
            page_source = getattr(active_driver, "page_source", "") or ""
            text = page_source.lower()
            confirmations = [
                "your response has been recorded",
                "đã được ghi lại",
                "câu trả lời của bạn đã được ghi lại",
            ]
            if any(message in text for message in confirmations):
                return True
            return False

        try:
            WebDriverWait(driver, self.config.wait_timeout).until(_submission_visible)
        except Exception as exc:
            raise RuntimeError("Submit was clicked but no confirmation page was detected") from exc

    def _click_element(self, driver, element) -> None:
        if hasattr(driver, "execute_script"):
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        try:
            element.click()
            return
        except ElementClickInterceptedException:
            pass

        try:
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ESCAPE)
        except Exception:
            pass

        if hasattr(driver, "execute_script"):
            driver.execute_script("arguments[0].click();", element)
            return

        raise RuntimeError("Element click was intercepted and no JavaScript fallback is available")
