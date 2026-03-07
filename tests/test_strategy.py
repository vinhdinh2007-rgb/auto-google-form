from __future__ import annotations

import pytest

from app.form_parser import GridRow, Question, QuestionType
from app.strategy import RandomStrategy


@pytest.mark.parametrize(
    ("question", "assertion"),
    [
        (
            Question(identifier="q1", prompt="radio", type=QuestionType.RADIO, options=["A", "B", "C"]),
            lambda answer: isinstance(answer, int) and 0 <= answer <= 2,
        ),
        (
            Question(identifier="q2", prompt="dropdown", type=QuestionType.DROPDOWN, options=["A", "B"]),
            lambda answer: isinstance(answer, int) and 0 <= answer <= 1,
        ),
        (
            Question(identifier="q3", prompt="scale", type=QuestionType.LINEAR_SCALE, options=["1", "2", "3"]),
            lambda answer: isinstance(answer, int) and 0 <= answer <= 2,
        ),
        (
            Question(identifier="q4", prompt="checkbox", type=QuestionType.CHECKBOX, options=["A", "B", "C"]),
            lambda answer: isinstance(answer, list) and 1 <= len(answer) <= 3 and all(0 <= i <= 2 for i in answer),
        ),
        (
            Question(identifier="q5", prompt="short", type=QuestionType.SHORT_TEXT),
            lambda answer: isinstance(answer, str) and len(answer.split()) >= 2,
        ),
        (
            Question(identifier="q6", prompt="long", type=QuestionType.LONG_TEXT),
            lambda answer: isinstance(answer, str) and len(answer.split()) >= 6,
        ),
        (
            Question(
                identifier="q7",
                prompt="grid",
                type=QuestionType.GRID,
                rows=[GridRow(label="Row 1", options=["1", "2"]), GridRow(label="Row 2", options=["1", "2"])],
            ),
            lambda answer: isinstance(answer, dict) and set(answer.keys()) == {0, 1} and all(0 <= v <= 1 for v in answer.values()),
        ),
    ],
)
def test_random_strategy_returns_valid_answers(question, assertion):
    strategy = RandomStrategy(seed=7)
    answer = strategy.choose_answer(question)
    assert assertion(answer)


def test_random_strategy_rejects_empty_single_choice():
    strategy = RandomStrategy(seed=7)
    question = Question(identifier="q1", prompt="radio", type=QuestionType.RADIO, options=[])

    with pytest.raises(ValueError, match="empty option list"):
        strategy.choose_answer(question)


def test_random_strategy_uses_preferred_name_for_name_prompt():
    strategy = RandomStrategy(seed=7)
    question = Question(identifier="q8", prompt="What is your name?", type=QuestionType.SHORT_TEXT)

    answer = strategy.choose_answer(question, preferred_name="Vinh")

    assert answer == "Vinh"


def test_random_strategy_keeps_random_text_for_non_name_prompt():
    strategy = RandomStrategy(seed=7)
    question = Question(identifier="q9", prompt="What is your favorite color?", type=QuestionType.SHORT_TEXT)

    answer = strategy.choose_answer(question, preferred_name="Vinh")

    assert answer != "Vinh"
