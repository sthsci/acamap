"""Content-hash cache for LLM summaries.

Keyed by a hash of (prompt version, model, sorted item texts) so identical
inputs are never re-summarised unless ``--force`` is passed. The cache lives in
``data/cache`` and is git-ignored (it is derived from raw text).
"""

from __future__ import annotations

from pathlib import Path

from .config import Settings, get_settings
from .hashing import content_hash
from .models import LlmSummary


class SummaryCache:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.dir = self.settings.cache_dir
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.dir / f"{key}.json"

    @staticmethod
    def key_for(signature_parts: tuple[str, ...]) -> str:
        return content_hash(*signature_parts)

    def get(self, key: str) -> LlmSummary | None:
        path = self._path(key)
        if not path.exists():
            return None
        try:
            return LlmSummary.model_validate_json(path.read_text(encoding="utf-8"))
        except ValueError:
            return None  # corrupt/stale cache entry -> treat as a miss

    def set(self, key: str, summary: LlmSummary) -> None:
        self._path(key).write_text(
            summary.model_dump_json(indent=2), encoding="utf-8"
        )
