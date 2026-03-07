from __future__ import annotations

from app.form_filler import FillResult
from app.submission_service import SubmissionRequest


class StubFiller:
    def __init__(self, config):
        self.config = config

    def fill_and_submit(self, url, count):
        return FillResult(requested=count, succeeded=count, failed=0, duration_seconds=1.25)


class StubSubmissionService:
    def __init__(self):
        self.requests = []

    def submit(self, request: SubmissionRequest):
        self.requests.append(request)
        return FillResult(requested=request.count, succeeded=request.count, failed=0, duration_seconds=1.25)


def test_index_route_renders(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Let's play a game!" in response.data
    assert b"Your Name" in response.data


def test_submit_route_validates_inputs(client):
    response = client.post(
        "/submit",
        data={"form_url": "https://example.com/form", "count": "0", "preferred_name": "Vinh"},
    )

    assert response.status_code == 400
    assert b"valid Google Forms URL" in response.data
    assert b"positive integer" in response.data


def test_submit_route_runs_filler(flask_app):
    stub_service = StubSubmissionService()
    flask_app.config["SUBMISSION_SERVICE_FACTORY"] = lambda: stub_service
    client = flask_app.test_client()

    response = client.post(
        "/submit",
        data={
            "form_url": "https://docs.google.com/forms/d/e/test/viewform",
            "count": "2",
            "preferred_name": "Vinh",
            "headless": "on",
        },
    )

    assert response.status_code == 200
    assert b"Performance Complete!" in response.data
    assert b">2<" in response.data
    assert stub_service.requests == [
        SubmissionRequest(
            form_url="https://docs.google.com/forms/d/e/test/viewform",
            count=2,
            headless=True,
            preferred_name="Vinh",
        )
    ]
