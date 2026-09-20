from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: Literal["demo", "test", "production"] = "production"
    database_url: str = "postgresql+psycopg://navigator:local-demo-only@localhost:55432/navigator"
    seed_demo: bool = False
    max_bot_token: str = ""
    max_webhook_secret: str = ""
    max_api_base: str = "https://platform-api2.max.ru"
    max_app_url: str = ""
    max_admin_ids: str = ""
    max_ca_bundle: str = ""
    public_origin: str = "http://localhost:8000"
    session_hours: int = 12
    source_fresh_days: int = 7
    static_dir: str = str(ROOT / "frontend" / "dist")

    @model_validator(mode="after")
    def production_guard(self):
        if self.app_env == "production":
            if self.seed_demo:
                raise ValueError("SEED_DEMO запрещён в production")
            if not self.public_origin.startswith("https://"):
                raise ValueError("Для production требуется HTTPS PUBLIC_ORIGIN")
        if self.session_hours < 1 or self.session_hours > 168:
            raise ValueError("SESSION_HOURS должен быть от 1 до 168")
        return self


@lru_cache
def settings() -> Settings:
    return Settings()
