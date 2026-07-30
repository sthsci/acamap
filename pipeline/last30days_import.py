"""Strict importer for local ``last30days --emit json`` report files.

This module never fetches data. It converts already-obtained JSON exports into
the canonical private RawPost schema after checking that publication-critical
fields are present and that a human explicitly selected each relevant note.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from .catalog import load_institutions
from .config import Settings
from .models import RawPost


class Last30DaysMapping(BaseModel):
    """Human-reviewed assignment of selected notes to one catalogue lab."""

    model_config = ConfigDict(extra="forbid")

    input: str
    lab_id: str
    selected_item_ids: list[str] = Field(min_length=1)
    campus_id: str | None = None
    expected_topic: str | None = None


class Last30DaysManifest(BaseModel):
    """Manifest kept under data/raw/ alongside private source exports."""

    model_config = ConfigDict(extra="forbid")

    version: int = 1
    exports: list[Last30DaysMapping] = Field(min_length=1)


class ImportAudit(BaseModel):
    input_files: int = 0
    candidate_items: int = 0
    selected_items: int = 0
    ready_items: int = 0
    duplicate_items: int = 0
    issue_counts: dict[str, int] = Field(default_factory=dict)
    messages: list[str] = Field(default_factory=list)

    @property
    def ready(self) -> bool:
        return self.ready_items > 0 and not self.issue_counts


def _read_report(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a last30days JSON report object")
    return payload


def _normalise_datetime(value: object, *, china_date: bool = False) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    if len(raw) == 10:
        suffix = "T12:00:00+08:00" if china_date else "T12:00:00+00:00"
        raw = f"{raw}{suffix}"
    try:
        datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return raw


def _catalogue_labs(settings: Settings) -> dict[str, tuple[str, object]]:
    labs: dict[str, tuple[str, object]] = {}
    for institution in load_institutions(settings):
        for lab in institution.labs:
            if lab.lab_id in labs:
                raise ValueError(f"duplicate lab_id in catalogue: {lab.lab_id}")
            labs[lab.lab_id] = (institution.institution_id, lab)
    return labs


def _record_from_item(
    item: dict[str, object],
    *,
    institution_id: str,
    department: str,
    lab_name: str,
    campus_id: str | None,
    collected_at: str | None,
    issues: Counter[str],
) -> RawPost | None:
    post_id = str(item.get("id") or "").strip()
    author_id = str(item.get("author_id") or "").strip()
    posted_at = _normalise_datetime(item.get("date"), china_date=True)
    title = str(item.get("title") or "").strip()
    description = str(item.get("desc") or "").strip()
    text = "\n\n".join(part for part in (title, description) if part)

    missing = False
    for key, value in (
        ("missing_post_id", post_id),
        ("missing_author_id", author_id),
        ("missing_posted_at", posted_at),
        ("missing_text", text),
        ("missing_collected_at", collected_at),
    ):
        if not value:
            issues[key] += 1
            missing = True
    if missing:
        return None

    engagement = item.get("engagement")
    if not isinstance(engagement, dict):
        engagement = {}
    likes = engagement.get("likes", 0)
    comments = engagement.get("num_comments", engagement.get("replies", 0))

    return RawPost(
        source="rednote",
        post_id=post_id,
        author_id=author_id,
        text=text,
        posted_at=posted_at,
        collected_at=collected_at,
        institution_id=institution_id,
        department=department,
        lab_name=lab_name,
        campus_id=campus_id,
        campus_assignment_method="provided" if campus_id else "unspecified",
        source_url=str(item.get("url") or "").strip() or None,
        likes_at_collection=likes or 0,
        comments_at_collection=comments or 0,
    )


def build_last30days_import(
    manifest_path: Path, settings: Settings
) -> tuple[list[RawPost], ImportAudit]:
    """Validate a manifest and return canonical private records plus an audit."""
    manifest = Last30DaysManifest.model_validate_json(
        manifest_path.read_text(encoding="utf-8")
    )
    if manifest.version != 1:
        raise ValueError(f"{manifest_path}: unsupported manifest version")

    labs = _catalogue_labs(settings)
    issues: Counter[str] = Counter()
    messages: list[str] = []
    records: list[RawPost] = []
    assignments: dict[str, str] = {}
    duplicate_items = 0
    candidate_items = 0
    selected_items = 0

    for mapping in manifest.exports:
        report_path = Path(mapping.input).expanduser()
        if not report_path.is_absolute():
            report_path = manifest_path.parent / report_path
        report_path = report_path.resolve()
        if not report_path.exists():
            issues["missing_input_file"] += 1
            messages.append(f"{mapping.input}: input file not found")
            continue

        lab_entry = labs.get(mapping.lab_id)
        if lab_entry is None:
            issues["unknown_lab_id"] += 1
            messages.append(f"{mapping.input}: unknown lab_id {mapping.lab_id}")
            continue
        institution_id, lab = lab_entry
        if mapping.campus_id and mapping.campus_id not in lab.campus_ids:
            issues["invalid_campus_for_lab"] += 1
            messages.append(
                f"{mapping.input}: campus_id is not assigned to {mapping.lab_id}"
            )
            continue

        report = _read_report(report_path)
        if mapping.expected_topic and report.get("topic") != mapping.expected_topic:
            issues["topic_mismatch"] += 1
            messages.append(f"{mapping.input}: report topic does not match manifest")
            continue

        items = report.get("xiaohongshu")
        if not isinstance(items, list):
            issues["missing_xiaohongshu_items"] += 1
            messages.append(f"{mapping.input}: no xiaohongshu item list")
            continue
        candidate_items += len(items)

        item_index: dict[str, dict[str, object]] = {}
        for item in items:
            if not isinstance(item, dict):
                issues["invalid_item"] += 1
                continue
            item_id = str(item.get("id") or "").strip()
            if item_id:
                item_index[item_id] = item

        selected = set(mapping.selected_item_ids)
        selected_items += len(selected)
        missing_selection_count = len(selected - item_index.keys())
        if missing_selection_count:
            issues["selected_item_not_found"] += missing_selection_count
            messages.append(
                f"{mapping.input}: {missing_selection_count} selected item(s) not found"
            )

        collected_at = _normalise_datetime(report.get("generated_at"))
        for item_id in sorted(selected & item_index.keys()):
            previous_lab = assignments.get(item_id)
            if previous_lab:
                duplicate_items += 1
                if previous_lab != mapping.lab_id:
                    issues["conflicting_lab_assignment"] += 1
                continue
            assignments[item_id] = mapping.lab_id

            record = _record_from_item(
                item_index[item_id],
                institution_id=institution_id,
                department=lab.department,
                lab_name=lab.name,
                campus_id=mapping.campus_id,
                collected_at=collected_at,
                issues=issues,
            )
            if record is not None:
                records.append(record)

    if not records:
        issues["no_ready_items"] += 1

    audit = ImportAudit(
        input_files=len(manifest.exports),
        candidate_items=candidate_items,
        selected_items=selected_items,
        ready_items=len(records),
        duplicate_items=duplicate_items,
        issue_counts=dict(sorted(issues.items())),
        messages=messages,
    )
    return records, audit


def write_raw_import(records: list[RawPost], path: Path) -> Path:
    """Write canonical records to a private, git-ignored path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"records": [record.model_dump(mode="json") for record in records]}
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path

