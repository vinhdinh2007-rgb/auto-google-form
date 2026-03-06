from __future__ import annotations

from app.config import AppConfig


def test_config_reads_environment_values(monkeypatch):
    monkeypatch.setenv("AUTOGG_HEADLESS", "false")
    monkeypatch.setenv("AUTOGG_INCOGNITO", "true")
    monkeypatch.setenv("AUTOGG_DISABLE_EXTENSIONS", "false")
    monkeypatch.setenv("AUTOGG_DISABLE_INFOBARS", "true")
    monkeypatch.setenv("AUTOGG_START_MAXIMIZED", "false")
    monkeypatch.setenv("AUTOGG_PAGE_LOAD_TIMEOUT", "45")
    monkeypatch.setenv("AUTOGG_WAIT_TIMEOUT", "12")
    monkeypatch.setenv("AUTOGG_MAX_WORKERS", "3")
    monkeypatch.setenv("AUTOGG_ENABLE_PROFILING", "true")
    monkeypatch.setenv("AUTOGG_PROFILE_OUTPUT_DIR", "profiles-out")
    monkeypatch.setenv("AUTOGG_HOST", "0.0.0.0")
    monkeypatch.setenv("AUTOGG_PORT", "8080")
    monkeypatch.setenv("AUTOGG_SECRET_KEY", "secret")
    monkeypatch.setenv("AUTOGG_CHROME_BINARY", "chrome.exe")
    monkeypatch.setenv("AUTOGG_CHROMEDRIVER", "chromedriver.exe")

    config = AppConfig.from_env()

    assert config.headless is False
    assert config.incognito is True
    assert config.disable_extensions is False
    assert config.disable_infobars is True
    assert config.start_maximized is False
    assert config.page_load_timeout == 45
    assert config.wait_timeout == 12
    assert config.max_workers == 3
    assert config.enable_profiling is True
    assert config.profile_output_dir == "profiles-out"
    assert config.host == "0.0.0.0"
    assert config.port == 8080
    assert config.secret_key == "secret"
    assert config.chrome_binary_path == "chrome.exe"
    assert config.chromedriver_path == "chromedriver.exe"


def test_config_with_overrides_returns_new_instance():
    config = AppConfig()

    updated = config.with_overrides(headless=False, max_workers=4)

    assert config.headless is True
    assert updated.headless is False
    assert updated.max_workers == 4
