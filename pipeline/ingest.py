"""Ingest: raw import -> hashed, anonymised items (longitudinal-ready).

Rows sharing a (post_id, comment_id) identity are merged into a single
:class:`AnonymisedItem` carrying multiple :class:`EngagementSnapshot` readings,
so engagement change over time can be studied later.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from .adapters import SourceAdapter, get_adapter
from .catalog import load_institutions, resolve_campus
from .config import Settings, get_settings
from .hashing import hash_id
from .models import AnonymisedItem, EngagementSnapshot, Institution, RawPost


def anonymise(
    raw: RawPost, salt: str, institutions: list[Institution] | None = None
) -> AnonymisedItem:
    post_hash = hash_id(raw.post_id, salt)
    comment_hash = hash_id(raw.comment_id, salt)
    author_hash = hash_id(raw.author_id, salt)
    assert post_hash and author_hash  # post_id/author_id are required, non-empty
    item_id = f"{post_hash}:{comment_hash}" if comment_hash else post_hash
    campus_id = raw.campus_id
    assignment_method = raw.campus_assignment_method
    assignment_confidence = raw.campus_assignment_confidence
    if institutions is not None:
        campus_id, assignment_method, assignment_confidence = resolve_campus(
            raw, institutions
        )
    return AnonymisedItem(
        source=raw.source,
        item_id=item_id,
        post_hash=post_hash,
        comment_hash=comment_hash,
        author_hash=author_hash,
        kind=raw.kind,
        text=raw.text,
        posted_at=raw.posted_at,
        institution_id=raw.institution_id,
        department=raw.department,
        lab_name=raw.lab_name,
        campus_id=campus_id,
        campus_name_raw=raw.campus_name_raw,
        campus_assignment_method=assignment_method,
        campus_assignment_confidence=assignment_confidence,
        researcher_name=raw.researcher_name,
        engagement=[
            EngagementSnapshot(
                collected_at=raw.collected_at,
                likes=raw.likes_at_collection,
                comments=raw.comments_at_collection,
            )
        ],
    )


def merge_snapshots(items: Iterable[AnonymisedItem]) -> list[AnonymisedItem]:
    """Collapse repeated readings of the same item into snapshot histories."""
    merged: dict[str, AnonymisedItem] = {}
    for item in items:
        existing = merged.get(item.item_id)
        if existing is None:
            merged[item.item_id] = item
            continue
        existing.engagement.extend(item.engagement)
        # Conflicting campus metadata across snapshots is ambiguous. Retain the
        # item once, but remove it from all campus-specific statistics.
        if existing.campus_id != item.campus_id:
            existing.campus_id = None
            existing.campus_assignment_method = "unspecified"
            existing.campus_assignment_confidence = None
    for item in merged.values():
        item.engagement.sort(key=lambda s: s.collected_at)
    return list(merged.values())


def ingest_file(
    path: Path,
    settings: Settings | None = None,
    adapter: SourceAdapter | None = None,
) -> list[AnonymisedItem]:
    settings = settings or get_settings()
    adapter = adapter or get_adapter(path)
    institutions = load_institutions(settings)
    anonymised = [
        anonymise(raw, settings.hash_salt, institutions) for raw in adapter.load(path)
    ]
    return merge_snapshots(anonymised)


def write_processed(items: list[AnonymisedItem], settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    out = settings.anonymised_file
    payload = [item.model_dump(mode="json") for item in items]
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def load_processed(settings: Settings | None = None) -> list[AnonymisedItem]:
    settings = settings or get_settings()
    path = settings.anonymised_file
    if not path.exists():
        raise FileNotFoundError(
            f"No ingested data at {path}. Run `labvibes ingest --input <file>` first."
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [AnonymisedItem.model_validate(record) for record in payload]
