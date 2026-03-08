from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from .config import AppConfig


class BrowserManager:
    def __init__(self, config: AppConfig):
        self.config = config
        self._driver = None

    def __enter__(self):
        return self.get_driver()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def build_options(self) -> Options:
        options = Options()
        
        # Performance & Docker optimization flags
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        if self.config.headless:
            options.add_argument("--headless=new")
        if self.config.incognito:
            options.add_argument("--incognito")
        if self.config.disable_extensions:
            options.add_argument("--disable-extensions")
        if self.config.disable_infobars:
            options.add_argument("--disable-infobars")
        if self.config.start_maximized:
            options.add_argument("--start-maximized")
        if self.config.chrome_binary_path:
            options.binary_location = self.config.chrome_binary_path
        return options

    def create_driver(self):
        service = (
            Service(executable_path=self.config.chromedriver_path)
            if self.config.chromedriver_path
            else Service()
        )
        driver = webdriver.Chrome(service=service, options=self.build_options())
        driver.set_page_load_timeout(self.config.page_load_timeout)
        return driver

    def get_driver(self):
        if self._driver is None:
            self._driver = self.create_driver()
        return self._driver

    def close(self) -> None:
        if self._driver is not None:
            self._driver.quit()
            self._driver = None
