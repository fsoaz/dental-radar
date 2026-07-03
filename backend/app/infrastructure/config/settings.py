from urllib.parse import urlparse

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql://dental_radar:dental_radar@localhost:5432/dental_radar"
    jwt_secret: str = "change-me-in-production"
    google_places_api_key: str = ""
    places_max_pages: int = 3
    ai_provider: str = "gpt"
    ai_fallback_provider: str = ""
    ai_retry_max: int = 3
    ai_max_site_text_chars: int = 8000
    ai_timeout_seconds: float = 60.0
    openai_api_key: str = ""
    openai_base_url: str = DEFAULT_OPENAI_BASE_URL
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    crawler_timeout_seconds: float = 10.0
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    log_level: str = "INFO"
    log_json: bool = True
    app_env: str = "development"

    @field_validator("openai_base_url")
    @classmethod
    def validate_openai_base_url(cls, value: str) -> str:
        normalized = (value or "").strip().rstrip("/")
        if not normalized:
            return DEFAULT_OPENAI_BASE_URL
        if urlparse(normalized).scheme != "https":
            raise ValueError(
                f"OPENAI_BASE_URL must use https:// (got {value!r}); "
                "the API key is sent as a bearer token to this host"
            )
        return normalized


settings = Settings()
