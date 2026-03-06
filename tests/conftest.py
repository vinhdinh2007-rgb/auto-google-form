from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from flask.testing import FlaskClient
from selenium.common.exceptions import NoSuchElementException

from app import create_app
from app.config import AppConfig


@dataclass
class FakeElement:
    text: str = ""
    attributes: dict[str, str] = field(default_factory=dict)
    selectors: dict[tuple[str, str], list["FakeElement"]] = field(default_factory=dict)
    tag_name: str = "div"
    clicked: bool = False
    cleared: bool = False
    sent_keys: list[str] = field(default_factory=list)

    def find_elements(self, by: str, value: str):
        return list(self.selectors.get((by, value), []))

    def find_element(self, by: str, value: str):
        elements = self.find_elements(by, value)
        if not elements:
            raise NoSuchElementException(f"Missing selector: {(by, value)}")
        return elements[0]

    def get_attribute(self, name: str):
        return self.attributes.get(name)

    def click(self):
        self.clicked = True

    def clear(self):
        self.cleared = True

    def send_keys(self, value: str):
        self.sent_keys.append(value)


class FakeDriver(FakeElement):
    def __init__(self, selectors=None):
        super().__init__(selectors=selectors or {})
        self.visited_urls = []
        self.quit_called = False
        self.timeout = None
        self.current_url = ""
        self.page_source = ""

    def get(self, url: str):
        self.visited_urls.append(url)
        self.current_url = url

    def set_page_load_timeout(self, timeout: int):
        self.timeout = timeout

    def quit(self):
        self.quit_called = True


@pytest.fixture
def app_config():
    return AppConfig(wait_timeout=1, max_workers=1, secret_key="test")


@pytest.fixture
def flask_app(app_config):
    app = create_app(app_config)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(flask_app) -> FlaskClient:
    return flask_app.test_client()
