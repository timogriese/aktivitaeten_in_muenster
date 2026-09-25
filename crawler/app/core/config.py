from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# crawler/.env - gitignored, never committed. Copy crawler/.env.example and fill in real values.
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    backend_url: str = "http://localhost:8001"
    crawl_interval_minutes: int = 30

    # Firecrawl (search + schema-guided extraction).
    firecrawl_api_key: str = ""
    firecrawl_api_url: str = "https://api.firecrawl.dev"
    default_query: str = "activities and events in Münster"
    firecrawl_search_limit: int = 5
    # Account concurrency limit for parallel scrape/extract jobs (see `firecrawl --status`).
    firecrawl_concurrency: int = 2

    # Locally hosted LLM (used by QueryService to plan search queries).
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""

    model_config = SettingsConfigDict(
        env_prefix="CRAWLER_", env_file=_ENV_FILE, env_file_encoding="utf-8"
    )


settings = Settings()
