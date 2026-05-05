"""Application configuration — loads all settings from the .env file."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file so the path is correct regardless of
# which directory the process is started from (e.g. backend/ vs project root).
_ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    """All runtime settings read from environment variables or .env file."""

    # Scraping
    scrapingbee_api_key: str
    apify_api_token: str

    # LLM
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"

    # Vector store
    chroma_persist_dir: str = "./chroma_db"

    # Apify actor ID for Amazon reviews
    apify_actor_id: str = "junglee/amazon-reviews-scraper"

    # Max reviews to collect per product
    max_reviews_per_product: int = 100

    # Sentence transformer model for embeddings
    embedding_model: str = "all-MiniLM-L6-v2"

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Single shared instance imported everywhere
settings = Settings()
