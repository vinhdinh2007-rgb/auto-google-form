from __future__ import annotations

from urllib.parse import urlparse

from flask import Blueprint, current_app, render_template, request

from .form_filler import FormFiller


ui = Blueprint("ui", __name__)


def _is_google_forms_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and parsed.netloc == "docs.google.com" and "/forms/" in parsed.path


@ui.get("/")
def index():
    return render_template("index.html", form_data={"count": 1, "headless": True})


@ui.post("/submit")
def submit():
    form_url = request.form.get("form_url", "").strip()
    count_raw = request.form.get("count", "").strip()
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
                form_data={"form_url": form_url, "count": count_raw or 1, "headless": headless},
            ),
            400,
        )

    settings = current_app.config["APP_SETTINGS"].with_overrides(headless=headless)
    filler_factory = current_app.config.get("FORM_FILLER_FACTORY", lambda config: FormFiller(config))
    filler = filler_factory(settings)
    result = filler.fill_and_submit(form_url, count)
    return render_template(
        "result.html",
        form_url=form_url,
        result=result,
        headless=headless,
    )
