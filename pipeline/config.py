"""Runtime configuration, loaded from environment / .env.

All tunables live here so the rest of the pipeline stays free of magic values.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Prompt version participates in the cache key: bump it whenever the system
# prompt or required output schema changes so stale summaries are regenerated.
PROMPT_VERSION = "2026-07-01"


class Settings(BaseSettings):
    """Process-wide settings.

    Field aliases map to the variable names documented in ``.env.example``.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # Local LLM (Ollama). Raw text is only ever sent here.
    ollama_host: str = Field(default="http://localhost:11434", alias="OLLAMA_HOST")
    model: str = Field(default="qwen2.5:7b-instruct", alias="LABVIBES_MODEL")

    # Anonymisation
    hash_salt: str = Field(default="labvibes-local-dev-salt", alias="LABVIBES_HASH_SALT")

    # Publication thresholds
    min_items: int = Field(default=5, alias="LABVIBES_MIN_ITEMS")
    min_authors: int = Field(default=3, alias="LABVIBES_MIN_AUTHORS")

    # Paths (relative to the repository root by default)
    data_dir: Path = Field(default=Path("data"), alias="LABVIBES_DATA_DIR")
    web_public_dir: Path = Field(default=Path("web/public/data"), alias="LABVIBES_WEB_PUBLIC_DIR")

    # LLM inference tuning
    temperature: float = Field(default=0.0, alias="LABVIBES_TEMPERATURE")
    seed: int = Field(default=7, alias="LABVIBES_SEED")
    max_retries: int = Field(default=3, alias="LABVIBES_MAX_RETRIES")
    request_timeout: float = Field(default=120.0, alias="LABVIBES_REQUEST_TIMEOUT")

    # --- Derived paths ------------------------------------------------------
    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def moderation_dir(self) -> Path:
        return self.data_dir / "moderation"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"

    @property
    def institutions_file(self) -> Path:
        return self.data_dir / "institutions" / "institutions.json"

    @property
    def regions_file(self) -> Path:
        return self.data_dir / "institutions" / "regions.json"

    @property
    def anonymised_file(self) -> Path:
        return self.processed_dir / "anonymised_items.json"

    @property
    def moderation_queue_file(self) -> Path:
        return self.moderation_dir / "moderation_queue.json"

    def ensure_dirs(self) -> None:
        for path in (
            self.raw_dir,
            self.processed_dir,
            self.moderation_dir,
            self.cache_dir,
            self.web_public_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
