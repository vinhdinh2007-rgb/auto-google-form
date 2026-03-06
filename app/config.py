from __future__ import annotations

import os
from dataclasses import dataclass, replace


def _to_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _to_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class AppConfig:
    headless: bool = True
    incognito: bool = True
    disable_extensions: bool = True
    disable_infobars: bool = True
    start_maximized: bool = True
    page_load_timeout: int = 30
    wait_timeout: int = 10
    max_workers: int = 1
    enable_profiling: bool = False
    profile_output_dir: str = "profiles"
    host: str = "127.0.0.1"
    port: int = 5000
    secret_key: str = "autogg-dev"
    chrome_binary_path: str | None = None
    chromedriver_path: str | None = None

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            headless=_to_bool(os.getenv("AUTOGG_HEADLESS"), True),
            incognito=_to_bool(os.getenv("AUTOGG_INCOGNITO"), True),
            disable_extensions=_to_bool(os.getenv("AUTOGG_DISABLE_EXTENSIONS"), True),
            disable_infobars=_to_bool(os.getenv("AUTOGG_DISABLE_INFOBARS"), True),
            start_maximized=_to_bool(os.getenv("AUTOGG_START_MAXIMIZED"), True),
            page_load_timeout=_to_int(os.getenv("AUTOGG_PAGE_LOAD_TIMEOUT"), 30),
            wait_timeout=_to_int(os.getenv("AUTOGG_WAIT_TIMEOUT"), 10),
            max_workers=max(1, _to_int(os.getenv("AUTOGG_MAX_WORKERS"), 1)),
            enable_profiling=_to_bool(os.getenv("AUTOGG_ENABLE_PROFILING"), False),
            profile_output_dir=os.getenv("AUTOGG_PROFILE_OUTPUT_DIR", "profiles"),
            host=os.getenv("AUTOGG_HOST", "127.0.0.1"),
            port=_to_int(os.getenv("AUTOGG_PORT"), 5000),
            secret_key=os.getenv("AUTOGG_SECRET_KEY", "autogg-dev"),
            chrome_binary_path=os.getenv("AUTOGG_CHROME_BINARY"),
            chromedriver_path=os.getenv("AUTOGG_CHROMEDRIVER"),
        )

    def with_overrides(self, **overrides: object) -> "AppConfig":
        return replace(self, **overrides)
