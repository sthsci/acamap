"""Source-adapter interface.

An adapter turns some *lawfully collected* external file into a stream of
``RawPost`` records. Adapters MUST NOT bypass logins, CAPTCHAs, rate limits or
any other access control: they read files a human has already exported by
permitted means. To add an approved source later, subclass ``SourceAdapter``,
implement :meth:`load`, and register it in ``adapters/__init__.py``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path

from ..models import RawPost


class SourceAdapter(ABC):
    """Read a permitted export file and yield validated raw records."""

    #: Short identifier, e.g. ``"csv"`` or ``"rednote-manual-export"``.
    name: str = "base"

    #: File extensions this adapter can handle, e.g. ``{".csv"}``.
    extensions: frozenset[str] = frozenset()

    @abstractmethod
    def load(self, path: Path) -> Iterator[RawPost]:
        """Yield :class:`RawPost` records parsed from ``path``.

        Implementations should validate each record (constructing ``RawPost``
        does this) and skip or raise on malformed rows as appropriate.
        """
        raise NotImplementedError

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in self.extensions
