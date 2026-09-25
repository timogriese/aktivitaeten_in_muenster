from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# crawler/.env - gitignored, never committed. Copy crawler/.env.example and fill in real values.
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    # Spring Boot backend (backend/). The Python mock_backend runs on 8001 instead.
    backend_url: str = "http://localhost:8080"
    crawl_interval_minutes: int = 30

    # Tavily (search + page content in one call). Free tier: 1000 credits/month.
    tavily_api_key: str = ""
    tavily_api_url: str = "https://api.tavily.com"
    default_query: str = "activities and events in Münster"
    tavily_search_limit: int = 5
    # Bounds parallel LLM extraction calls per crawl cycle.
    extraction_concurrency: int = 3

    # MSHack AI gateway, OpenAI-compatible (used by QueryService to plan search queries).
    llm_api_key: str = ""
    llm_base_url: str = "https://mshack.items.services/v1"
    llm_model: str = "DeepSeek-V4-Flash"

    model_config = SettingsConfigDict(
        env_prefix="CRAWLER_", env_file=_ENV_FILE, env_file_encoding="utf-8"
    )


settings = Settings()
