from __future__ import annotations

from dataclasses import dataclass

from .config import AppConfig
from .form_filler import FillResult, FormFiller


@dataclass(frozen=True)
class SubmissionRequest:
    form_url: str
    count: int
    headless: bool
    preferred_name: str | None = None


class SubmissionService:
    def __init__(self, config: AppConfig, filler_factory=None):
        self.config = config
        self.filler_factory = filler_factory or (lambda settings: FormFiller(settings))

    def submit(self, request: SubmissionRequest) -> FillResult:
        settings = self.config.with_overrides(headless=request.headless)
        filler = self.filler_factory(settings)
        return filler.fill_and_submit(
            request.form_url,
            request.count,
            preferred_name=request.preferred_name,
        )
