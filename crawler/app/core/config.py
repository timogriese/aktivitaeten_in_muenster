from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    backend_url: str = "http://localhost:8001"
    crawl_interval_minutes: int = 30

    # Firecrawl (search + schema-guided extraction). The API key is resolved from
    # CRAWLER_FIRECRAWL_API_KEY, falling back to the apicode.txt in the project root.
    firecrawl_api_key: str = ""
    firecrawl_api_url: str = "https://api.firecrawl.dev"
    default_query: str = "activities and events in Münster"
    firecrawl_search_limit: int = 5
    # Account concurrency limit for parallel scrape/extract jobs (see `firecrawl --status`).
    firecrawl_concurrency: int = 2

    model_config = {"env_prefix": "CRAWLER_"}


settings = Settings()
