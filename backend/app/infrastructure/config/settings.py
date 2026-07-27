from urllib.parse import urlparse

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql://dental_radar:dental_radar@localhost:5432/dental_radar"
    jwt_secret: str = "change-me-in-production"
    api_key: str = ""
    # Escape hatch for local/test only. When False (default), an empty API_KEY
    # rejects mutating routes with 503 — auth fails closed even if APP_ENV is
    # left at its development default.
    allow_unauthenticated: bool = False
    rate_limit_per_minute: int = 30
    # Comma-separated proxy IPs/CIDRs whose X-Forwarded-For may be trusted for
    # rate-limit client identification. Empty means trust none (use peer IP).
    rate_limit_trusted_proxies: str = ""
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

    @model_validator(mode="after")
    def _normalize_openai_base_url(self) -> "Settings":
        normalized = (self.openai_base_url or "").strip().rstrip("/")
        if not normalized:
            self.openai_base_url = DEFAULT_OPENAI_BASE_URL
            return self
        uses_gpt = "gpt" in {
            self.ai_provider.lower().strip(),
            self.ai_fallback_provider.lower().strip(),
        }
        if uses_gpt and urlparse(normalized).scheme != "https":
            raise ValueError(
                f"OPENAI_BASE_URL must use https:// (got {self.openai_base_url!r}); "
                "the API key is sent as a bearer token to this host"
            )
        self.openai_base_url = normalized
        return self


settings = Settings()
