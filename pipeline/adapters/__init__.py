"""Adapter registry.

Register approved source adapters here. Selection is by file extension; extend
:func:`get_adapter` (or pass an explicit adapter) when a source needs a richer
signal than its extension.
"""

from __future__ import annotations

from pathlib import Path

from .base import SourceAdapter
from .csv_adapter import CsvAdapter
from .json_adapter import JsonAdapter

#: Ordered list of registered adapters.
ADAPTERS: list[SourceAdapter] = [CsvAdapter(), JsonAdapter()]


def get_adapter(path: Path) -> SourceAdapter:
    """Return the first registered adapter that can handle ``path``."""
    for adapter in ADAPTERS:
        if adapter.can_handle(path):
            return adapter
    raise ValueError(
        f"No adapter registered for '{path.suffix}'. "
        f"Supported: {sorted(ext for a in ADAPTERS for ext in a.extensions)}"
    )


__all__ = ["SourceAdapter", "CsvAdapter", "JsonAdapter", "ADAPTERS", "get_adapter"]
