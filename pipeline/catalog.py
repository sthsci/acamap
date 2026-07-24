"""Load the committed institution catalogue and region configuration."""

from __future__ import annotations

import json
import re

from .config import Settings, get_settings
from .models import (
    CampusAssignmentMethod,
    Confidence,
    Institution,
    RawPost,
    Region,
)


def load_institutions(settings: Settings | None = None) -> list[Institution]:
    settings = settings or get_settings()
    payload = json.loads(settings.institutions_file.read_text(encoding="utf-8"))
    institutions = [Institution.model_validate(record) for record in payload]
    validate_catalogue(institutions)
    return institutions


def load_regions(settings: Settings | None = None) -> list[Region]:
    settings = settings or get_settings()
    payload = json.loads(settings.regions_file.read_text(encoding="utf-8"))
    return [Region.model_validate(record) for record in payload]


def validate_catalogue(institutions: list[Institution]) -> None:
    """Fail fast on duplicate or dangling campus references."""
    institution_ids: set[str] = set()
    all_campus_ids: set[str] = set()
    coordinate_owners: dict[tuple[float, float], str] = {}
    for institution in institutions:
        if institution.institution_id in institution_ids:
            raise ValueError(f"Duplicate institution id: {institution.institution_id}")
        institution_ids.add(institution.institution_id)

        campus_ids = [campus.campus_id for campus in institution.campuses]
        if len(campus_ids) != len(set(campus_ids)):
            raise ValueError(f"{institution.institution_id}: duplicate campus id")
        duplicate_global_ids = set(campus_ids) & all_campus_ids
        if duplicate_global_ids:
            raise ValueError(f"Duplicate campus ids: {sorted(duplicate_global_ids)}")
        all_campus_ids.update(campus_ids)
        for campus in institution.campuses:
            coordinate = (campus.latitude, campus.longitude)
            if coordinate in coordinate_owners:
                raise ValueError(
                    f"{campus.campus_id}: duplicate physical marker with "
                    f"{coordinate_owners[coordinate]}"
                )
            coordinate_owners[coordinate] = campus.campus_id
        known = set(campus_ids)
        for department in institution.departments:
            unknown = set(department.campus_ids) - known
            if unknown:
                raise ValueError(
                    f"{institution.institution_id}/{department.name}: "
                    f"unknown campus ids {sorted(unknown)}"
                )
        for lab in institution.labs:
            unknown = set(lab.campus_ids) - known
            if unknown:
                raise ValueError(
                    f"{institution.institution_id}/{lab.name}: "
                    f"unknown campus ids {sorted(unknown)}"
                )


def _normalise_campus_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def resolve_campus(
    raw: RawPost, institutions: list[Institution]
) -> tuple[str | None, CampusAssignmentMethod, Confidence | None]:
    """Resolve a raw campus without ever defaulting to a main campus."""
    institution = next(
        (item for item in institutions if item.institution_id == raw.institution_id),
        None,
    )
    if institution is None:
        return (None, "unspecified", None)

    by_id = {campus.campus_id: campus for campus in institution.campuses}
    if raw.campus_id:
        if raw.campus_id not in by_id:
            raise ValueError(
                f"{raw.institution_id}: unknown provided campus_id '{raw.campus_id}'"
            )
        return (raw.campus_id, "provided", raw.campus_assignment_confidence or "high")

    if raw.campus_name_raw:
        needle = _normalise_campus_name(raw.campus_name_raw)
        matches = [
            campus
            for campus in institution.campuses
            if needle
            in {
                _normalise_campus_name(campus.campus_id),
                _normalise_campus_name(campus.name),
                _normalise_campus_name(campus.short_name),
            }
        ]
        if len(matches) == 1:
            return (matches[0].campus_id, "catalogue_match", "high")
        # Raw wording was present but was unknown or ambiguous. Do not discard
        # that signal and then infer a different campus from the lab.
        return (None, "unspecified", None)

    matching_labs = [
        lab
        for lab in institution.labs
        if lab.name == raw.lab_name
        and (raw.department is None or lab.department == raw.department)
    ]
    if len(matching_labs) == 1 and len(matching_labs[0].campus_ids) == 1:
        return (matching_labs[0].campus_ids[0], "inferred_from_lab", "medium")

    return (None, "unspecified", None)
