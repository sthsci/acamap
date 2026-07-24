"""CSV importer for lawfully collected public posts."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pandas as pd

from ..models import RawPost
from .base import SourceAdapter


class CsvAdapter(SourceAdapter):
    name = "csv"
    extensions = frozenset({".csv"})

    def load(self, path: Path) -> Iterator[RawPost]:
        # keep_default_na=False so empty cells arrive as "" (handled by the
        # model's blank->None validators) rather than as float NaN.
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        for record in frame.to_dict(orient="records"):
            yield RawPost.model_validate(record)
