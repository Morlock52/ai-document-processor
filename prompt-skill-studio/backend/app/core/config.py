from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Prompt & Skill Studio"
    api_prefix: str = "/api/v1"

    studio_passcode: str = Field(default="change-me")
    studio_master_key: str = Field(default="")
    session_secret: str = Field(default="dev-session-secret-change-me-please")
    session_cookie_name: str = "studio_session"
    session_max_age_seconds: int = 60 * 60 * 24 * 8

    database_url: str = Field(default="postgresql+psycopg://studio:studio@localhost:5432/studio")
    redis_url: str = Field(default="redis://localhost:6379/0")

    frontend_origin: str = "http://localhost:3000"
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    blob_dir: str = "./blobs"

    doc_sync_extra_sources: str = ""

    @property
    def cors_origin_list(self) -> List[str]:
        origins = list({*self.cors_origins, self.frontend_origin})
        return [o for o in origins if o]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
