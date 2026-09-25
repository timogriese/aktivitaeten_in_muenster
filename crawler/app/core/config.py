from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    backend_url: str = "http://localhost:8001"
    crawl_interval_minutes: int = 30

    model_config = {"env_prefix": "CRAWLER_"}


settings = Settings()
