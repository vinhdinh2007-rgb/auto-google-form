from __future__ import annotations

from app.form_filler import FillResult


class StubFiller:
    def __init__(self, config):
        self.config = config

    def fill_and_submit(self, url, count):
        return FillResult(requested=count, succeeded=count, failed=0, duration_seconds=1.25)


def test_index_route_renders(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Google Forms Automation" in response.data


def test_submit_route_validates_inputs(client):
    response = client.post(
        "/submit",
        data={"form_url": "https://example.com/form", "count": "0"},
    )

    assert response.status_code == 400
    assert b"valid Google Forms URL" in response.data
    assert b"positive integer" in response.data


def test_submit_route_runs_filler(flask_app):
    flask_app.config["FORM_FILLER_FACTORY"] = lambda config: StubFiller(config)
    client = flask_app.test_client()

    response = client.post(
        "/submit",
        data={
            "form_url": "https://docs.google.com/forms/d/e/test/viewform",
            "count": "2",
            "headless": "on",
        },
    )

    assert response.status_code == 200
    assert b"Run Complete" in response.data
    assert b">2<" in response.data
