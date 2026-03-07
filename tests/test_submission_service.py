from __future__ import annotations

from app.config import AppConfig
from app.form_filler import FillResult
from app.submission_service import SubmissionRequest, SubmissionService


class RecordingFiller:
    def __init__(self, config):
        self.config = config
        self.calls = []

    def fill_and_submit(self, form_url, count, preferred_name=None):
        self.calls.append((form_url, count, preferred_name))
        return FillResult(requested=count, succeeded=count, failed=0)


def test_submission_service_applies_request_overrides():
    captured_configs = []
    fillers = []

    def filler_factory(config):
        captured_configs.append(config)
        filler = RecordingFiller(config)
        fillers.append(filler)
        return filler

    service = SubmissionService(AppConfig(headless=True, max_workers=2), filler_factory=filler_factory)

    result = service.submit(
        SubmissionRequest(
            form_url="https://docs.google.com/forms/d/e/test/viewform",
            count=3,
            headless=False,
            preferred_name="Vinh",
        )
    )

    assert result.requested == 3
    assert captured_configs[0].headless is False
    assert captured_configs[0].max_workers == 2
    assert fillers[0].calls == [("https://docs.google.com/forms/d/e/test/viewform", 3, "Vinh")]
