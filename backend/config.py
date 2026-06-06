from __future__ import annotations

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    # LLM
    llm_provider: str = "anthropic"
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    claude_model: str = "claude-sonnet-4-5"
    openai_model: str = "gpt-4o"

    # Embedding
    embedding_provider: str = "openai"
    openai_embedding_model: str = "text-embedding-3-small"

    # Database (multiple aliases, comma-separated)
    db_aliases: str = "default"
    db_default_url: str = "sqlite+aiosqlite:///./speakql_dev.db"

    # Chroma
    chroma_mode: str = "local"  # "local" | "http"
    chroma_persist_dir: str = "./chroma_data"
    chroma_host: str = "localhost"
    chroma_port: int = 8001

    # Pipeline
    top_k_tables: int = 5
    max_rows: int = 1000
    query_timeout_seconds: int = 30

    def get_db_url(self, alias: str) -> str:
        import os
        # Check os.environ first (docker-compose environment: overrides .env)
        env_key = f"DB_{alias.upper()}_URL"
        value = os.environ.get(env_key)
        if not value:
            # Fall through to pydantic-parsed fields / model_extra
            attr_key = f"db_{alias}_url"
            value = getattr(self, attr_key, None)
            if value is None and hasattr(self, "model_extra"):
                value = (self.model_extra or {}).get(attr_key)
        if not value:
            raise ValueError(f"No DB URL configured for alias '{alias}'. Set {env_key} in .env")
        return value

    def get_db_aliases(self) -> list[str]:
        return [a.strip() for a in self.db_aliases.split(",")]


settings = Settings()
