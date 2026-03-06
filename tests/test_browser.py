from __future__ import annotations

from unittest.mock import Mock

import app.browser as browser_module
from app.browser import BrowserManager
from app.config import AppConfig


def test_browser_manager_builds_chrome_options():
    manager = BrowserManager(AppConfig(headless=True))
    options = manager.build_options()
    args = options.arguments

    assert "--headless=new" in args
    assert "--incognito" in args
    assert "--disable-extensions" in args


def test_browser_manager_closes_driver(monkeypatch):
    fake_driver = Mock()
    manager = BrowserManager(AppConfig())
    monkeypatch.setattr(manager, "create_driver", lambda: fake_driver)

    driver = manager.get_driver()
    assert driver is fake_driver

    manager.close()

    fake_driver.quit.assert_called_once()


def test_browser_manager_context_creates_driver(monkeypatch):
    fake_driver = Mock()
    monkeypatch.setattr(browser_module.webdriver, "Chrome", lambda service, options: fake_driver)
    manager = BrowserManager(AppConfig(chromedriver_path="chromedriver.exe", page_load_timeout=20))

    with manager as driver:
        assert driver is fake_driver
        fake_driver.set_page_load_timeout.assert_called_once_with(20)

    fake_driver.quit.assert_called_once()
