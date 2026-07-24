"""JSON importer for lawfully collected public posts.

Accepts either a top-level list of record objects or an object with a
``records`` / ``posts`` key holding that list.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

from ..models import RawPost
from .base import SourceAdapter


class JsonAdapter(SourceAdapter):
    name = "json"
    extensions = frozenset({".json"})

    def load(self, path: Path) -> Iterator[RawPost]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            for key in ("records", "posts", "items", "data"):
                if key in payload:
                    payload = payload[key]
                    break
        if not isinstance(payload, list):
            raise ValueError(
                f"{path}: expected a list of records or an object containing one"
            )
        for record in payload:
            yield RawPost.model_validate(record)
