from __future__ import annotations

import random

from .form_parser import Question, QuestionType


class RandomStrategy:
    DEFAULT_WORDS = [
        "alpha",
        "bravo",
        "charlie",
        "delta",
        "echo",
        "foxtrot",
        "golf",
        "hotel",
    ]

    def __init__(self, seed: int | None = None, words: list[str] | None = None):
        self._random = random.Random(seed)
        self._words = words or self.DEFAULT_WORDS

    def choose_answer(self, question: Question, preferred_name: str | None = None):
        if question.type in {QuestionType.RADIO, QuestionType.DROPDOWN, QuestionType.LINEAR_SCALE}:
            return self._pick_single(question.options)
        if question.type == QuestionType.CHECKBOX:
            return self._pick_multiple(question.options)
        if question.type == QuestionType.SHORT_TEXT:
            if preferred_name and self._is_name_prompt(question.prompt):
                return preferred_name
            return self._build_text(min_words=2, max_words=4)
        if question.type == QuestionType.LONG_TEXT:
            return self._build_text(min_words=6, max_words=10)
        if question.type == QuestionType.GRID:
            answers = {}
            for index, row in enumerate(question.rows):
                option_count = len(row.options or question.options)
                if option_count == 0:
                    raise ValueError(f"No options available for grid row {row.label!r}")
                answers[index] = self._random.randrange(option_count)
            return answers
        raise ValueError(f"Unsupported question type: {question.type}")

    def _pick_single(self, options: list[str]) -> int:
        if not options:
            raise ValueError("Cannot choose from an empty option list")
        return self._random.randrange(len(options))

    def _pick_multiple(self, options: list[str]) -> list[int]:
        if not options:
            raise ValueError("Cannot choose from an empty option list")
        sample_size = self._random.randint(1, len(options))
        return sorted(self._random.sample(range(len(options)), sample_size))

    def _build_text(self, min_words: int, max_words: int) -> str:
        word_count = self._random.randint(min_words, max_words)
        return " ".join(self._random.choice(self._words) for _ in range(word_count))

    def _is_name_prompt(self, prompt: str) -> bool:
        normalized_prompt = prompt.strip().lower()
        name_markers = [
            "name",
            "your name",
            "full name",
            "ten",
            "ho ten",
            "họ tên",
        ]
        return any(marker in normalized_prompt for marker in name_markers)
