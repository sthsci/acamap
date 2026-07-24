"""Aggregate kept items into lab groups and apply publication thresholds.

Grouping key is (institution_id, department, lab_name). A group is publishable
only when it has at least ``min_items`` items from at least ``min_authors``
distinct authors. The public app never ranks or scores researchers, so
``researcher_name`` is used here solely to keep counts sane, never as a key.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from pydantic import BaseModel, Field

from .config import Settings, get_settings
from .models import AnonymisedItem, ModerationRecord

INSUFFICIENT_DATA_MESSAGE = "Insufficient public data for a reliable summary."


class LabGroup(BaseModel):
    institution_id: str
    department: str
    lab_name: str
    items: list[AnonymisedItem] = Field(default_factory=list)
    withheld_count: int = 0

    @property
    def item_count(self) -> int:
        return len(self.items)

    @property
    def unique_author_count(self) -> int:
        return len({item.author_hash for item in self.items})

    @property
    def date_range(self) -> tuple[date | None, date | None]:
        if not self.items:
            return (None, None)
        dates = [item.posted_at.date() for item in self.items]
        return (min(dates), max(dates))

    def meets_threshold(self, settings: Settings) -> bool:
        return (
            self.item_count >= settings.min_items
            and self.unique_author_count >= settings.min_authors
        )

    def texts(self) -> list[str]:
        return [item.text for item in self.items]


def _group_key(item: AnonymisedItem) -> tuple[str, str, str]:
    return (
        item.institution_id,
        (item.department or "Unspecified"),
        (item.lab_name or "Unspecified"),
    )


def group_by_lab(
    items: list[AnonymisedItem],
    withheld: list[ModerationRecord] | None = None,
) -> list[LabGroup]:
    """Group kept items by lab; attach per-lab withheld counts."""
    buckets: dict[tuple[str, str, str], list[AnonymisedItem]] = defaultdict(list)
    for item in items:
        buckets[_group_key(item)].append(item)

    withheld_counts: dict[tuple[str, str, str], int] = defaultdict(int)
    for record in withheld or []:
        key = (
            record.institution_id,
            (record.department or "Unspecified"),
            (record.lab_name or "Unspecified"),
        )
        withheld_counts[key] += 1

    groups: list[LabGroup] = []
    # Union of keys so labs with only-withheld content still surface a group.
    for key in sorted(set(buckets) | set(withheld_counts)):
        institution_id, department, lab_name = key
        groups.append(
            LabGroup(
                institution_id=institution_id,
                department=department,
                lab_name=lab_name,
                items=buckets.get(key, []),
                withheld_count=withheld_counts.get(key, 0),
            )
        )
    return groups


def publishable(groups: list[LabGroup], settings: Settings | None = None) -> list[LabGroup]:
    settings = settings or get_settings()
    return [g for g in groups if g.meets_threshold(settings)]
