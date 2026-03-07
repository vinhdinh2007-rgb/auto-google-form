from __future__ import annotations

from urllib.parse import urlparse

from flask import Blueprint, current_app, render_template, request

from .submission_service import SubmissionRequest, SubmissionService


ui = Blueprint("ui", __name__)


def _is_google_forms_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and parsed.netloc == "docs.google.com" and "/forms/" in parsed.path


@ui.get("/")
def index():
    return render_template(
        "index.html",
        form_data={"count": 1, "headless": True, "preferred_name": ""},
    )


@ui.post("/submit")
def submit():
    form_url = request.form.get("form_url", "").strip()
    count_raw = request.form.get("count", "").strip()
    preferred_name = request.form.get("preferred_name", "").strip()
    headless = request.form.get("headless") == "on"

    errors = []
    if not _is_google_forms_url(form_url):
        errors.append("Enter a valid Google Forms URL.")

    try:
        count = int(count_raw)
        if count <= 0:
            raise ValueError
    except ValueError:
        errors.append("Submission count must be a positive integer.")
        count = 1

    if errors:
        return (
            render_template(
                "index.html",
                errors=errors,
                form_data={
                    "form_url": form_url,
                    "count": count_raw or 1,
                    "preferred_name": preferred_name,
                    "headless": headless,
                },
            ),
            400,
        )

    service_factory = current_app.config.get("SUBMISSION_SERVICE_FACTORY", _create_submission_service)
    submission_service = service_factory()
    result = submission_service.submit(
        SubmissionRequest(
            form_url=form_url,
            count=count,
            headless=headless,
            preferred_name=preferred_name or None,
        )
    )
    return render_template(
        "result.html",
        form_url=form_url,
        result=result,
        headless=headless,
    )


def _create_submission_service() -> SubmissionService:
    app_settings = current_app.config["APP_SETTINGS"]
    filler_factory = current_app.config.get("FORM_FILLER_FACTORY")
    return SubmissionService(app_settings, filler_factory=filler_factory)
