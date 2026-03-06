from __future__ import annotations

from pathlib import Path

from flask import Flask

from .config import AppConfig
from .routes import ui


def create_app(config: AppConfig | None = None) -> Flask:
    base_dir = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        template_folder=str(base_dir / "templates"),
        static_folder=str(base_dir / "static"),
    )
    settings = config or AppConfig.from_env()
    app.config["APP_SETTINGS"] = settings
    app.secret_key = settings.secret_key
    app.register_blueprint(ui)
    return app
