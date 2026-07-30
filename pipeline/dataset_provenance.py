"""Private dataset provenance marker used to label the public export honestly."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from .config import Settings

DatasetKind = Literal["synthetic_demo", "lawfully_imported"]

DATASET_NOTES: dict[DatasetKind, str] = {
    "synthetic_demo": (
        "The workplace-perception summaries use synthetic demonstration records. "
        "Institution and location details come from the verified public catalogue."
    ),
    "lawfully_imported": (
        "Workplace-perception summaries are sanitised aggregates from lawfully imported "
        "public discussion; raw posts, authors and source links are not published."
    ),
}


class DatasetProvenance(BaseModel):
    """Local-only marker; no input paths or identifiers are stored."""

    kind: DatasetKind
    imported_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_format: str
    imported_item_count: int = Field(ge=0)


def write_dataset_provenance(
    provenance: DatasetProvenance, settings: Settings
) -> None:
    path = settings.dataset_provenance_file
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(provenance.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )


def load_dataset_provenance(settings: Settings) -> DatasetProvenance:
    """Load the marker, defaulting conservatively to the shipped demo label."""
    path = settings.dataset_provenance_file
    if not path.exists():
        return DatasetProvenance(
            kind="synthetic_demo",
            source_format="bundled-synthetic-sample",
            imported_item_count=0,
        )
    return DatasetProvenance.model_validate_json(path.read_text(encoding="utf-8"))
