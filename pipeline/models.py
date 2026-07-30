"""Pydantic models: raw input, anonymised items, institutions, summaries, export.

Field-level notes on privacy:
  * ``RawPost`` is the ONLY model that carries user identifiers and source URLs.
    It exists briefly in memory during ingest and is never serialised to a
    committed location.
  * ``AnonymisedItem`` carries hashed identifiers plus ``text`` and
    ``researcher_name`` which are INTERNAL ONLY. It is written to
    ``data/processed`` (git-ignored) and never exported to the website.
  * The ``Public*`` models are the only ones written to ``web/public/data``.
    They contain no free text, no identifiers and no URLs.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Confidence = Literal["low", "medium", "high"]
DatasetKind = Literal["synthetic_demo", "lawfully_imported"]
ItemKind = Literal["post", "comment"]
CampusAssignmentMethod = Literal[
    "provided", "catalogue_match", "inferred_from_lab", "unspecified"
]
CampusLocationType = Literal[
    "university_campus",
    "medical_research_campus",
    "research_institute",
    "research_location",
]
EvidenceStatus = Literal["summary_available", "below_threshold", "no_assigned_evidence"]


def _blank_to_none(value: object) -> object:
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


# ---------------------------------------------------------------------------
# Raw input (local only) + longitudinal engagement
# ---------------------------------------------------------------------------
class EngagementSnapshot(BaseModel):
    """A single point-in-time engagement reading for a post/comment."""

    collected_at: datetime
    likes: int = 0
    comments: int = 0

    @field_validator("likes", "comments", mode="before")
    @classmethod
    def _coerce_int(cls, v: object) -> int:
        if v is None or v == "":
            return 0
        return int(float(v))


class RawPost(BaseModel):
    """A lawfully collected public post or comment, exactly as imported.

    Multiple rows may share ``post_id``/``comment_id`` with different
    ``collected_at`` values; ingest merges those into engagement snapshots.
    """

    model_config = ConfigDict(extra="ignore")

    source: str
    post_id: str
    comment_id: str | None = None
    author_id: str
    text: str
    posted_at: datetime
    collected_at: datetime
    institution_id: str
    department: str | None = None
    lab_name: str | None = None
    campus_id: str | None = None
    campus_name_raw: str | None = None
    campus_assignment_method: CampusAssignmentMethod = "unspecified"
    campus_assignment_confidence: Confidence | None = None
    researcher_name: str | None = None
    source_url: str | None = None
    likes_at_collection: int = 0
    comments_at_collection: int = 0

    @field_validator(
        "comment_id",
        "department",
        "lab_name",
        "campus_id",
        "campus_name_raw",
        "campus_assignment_confidence",
        "researcher_name",
        "source_url",
        mode="before",
    )
    @classmethod
    def _optional_blank(cls, v: object) -> object:
        return _blank_to_none(v)

    @field_validator("likes_at_collection", "comments_at_collection", mode="before")
    @classmethod
    def _coerce_counts(cls, v: object) -> int:
        if v is None or v == "":
            return 0
        return int(float(v))

    @field_validator("campus_assignment_method", mode="before")
    @classmethod
    def _blank_assignment_method(cls, v: object) -> object:
        return "unspecified" if v is None or v == "" else v

    @property
    def kind(self) -> ItemKind:
        return "comment" if self.comment_id else "post"

    def dedupe_key(self) -> tuple[str, str]:
        """Identity of the underlying item across engagement snapshots."""
        return (self.post_id, self.comment_id or "")


# ---------------------------------------------------------------------------
# Anonymised item (internal processed artefact — git-ignored)
# ---------------------------------------------------------------------------
class AnonymisedItem(BaseModel):
    """A raw item with identifiers hashed. ``text``/``researcher_name`` remain
    for local moderation, aggregation and entity resolution ONLY."""

    source: str
    item_id: str
    post_hash: str
    comment_hash: str | None = None
    author_hash: str
    kind: ItemKind
    text: str
    posted_at: datetime
    institution_id: str
    department: str | None = None
    lab_name: str | None = None
    campus_id: str | None = None
    campus_name_raw: str | None = None
    campus_assignment_method: CampusAssignmentMethod = "unspecified"
    campus_assignment_confidence: Confidence | None = None
    researcher_name: str | None = None
    engagement: list[EngagementSnapshot] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Moderation
# ---------------------------------------------------------------------------
class ModerationRecord(BaseModel):
    """A withheld item plus why it was withheld. Private queue only."""

    item_id: str
    institution_id: str
    department: str | None = None
    lab_name: str | None = None
    campus_id: str | None = None
    reasons: list[str]
    text: str  # retained locally for human review; never exported
    posted_at: datetime


# ---------------------------------------------------------------------------
# Institution catalogue (committed, public-safe)
# ---------------------------------------------------------------------------
class Lab(BaseModel):
    lab_id: str
    name: str
    department: str
    campus_ids: list[str] = Field(default_factory=list)
    research_areas: list[str] = Field(default_factory=list)


class Department(BaseModel):
    name: str
    campus_ids: list[str] = Field(default_factory=list)


class MapCenter(BaseModel):
    latitude: float
    longitude: float


class CampusProvenance(BaseModel):
    official_source_url: str
    coordinate_source_url: str
    verified_at: date
    note: str | None = None


class Campus(BaseModel):
    campus_id: str
    name: str
    short_name: str
    latitude: float
    longitude: float
    address: str
    location_type: CampusLocationType
    provenance: CampusProvenance


class Institution(BaseModel):
    institution_id: str
    name: str
    short_name: str
    region: str
    map_center: MapCenter
    campuses: list[Campus] = Field(default_factory=list)
    website: str | None = None
    established: int | None = None
    departments: list[Department] = Field(default_factory=list)
    labs: list[Lab] = Field(default_factory=list)


class Region(BaseModel):
    id: str
    name: str
    status: Literal["active", "coming_soon"]
    center: list[float]  # [lat, lon]
    zoom: int


# ---------------------------------------------------------------------------
# LLM output (validated) — matches the required JSON contract exactly
# ---------------------------------------------------------------------------
class Theme(BaseModel):
    model_config = ConfigDict(extra="ignore")
    theme: str
    description: str
    supporting_item_count: int = Field(default=0, ge=0)


class LlmSummary(BaseModel):
    """The structured object the local model must return."""

    model_config = ConfigDict(extra="ignore")

    overview: str
    positive_themes: list[Theme] = Field(default_factory=list)
    challenge_themes: list[Theme] = Field(default_factory=list)
    neutral_observations: list[str] = Field(default_factory=list)
    confidence: Confidence
    limitations: list[str] = Field(default_factory=list)
    withheld_item_count: int = Field(default=0, ge=0)


# ---------------------------------------------------------------------------
# Public export (the ONLY thing written to web/public/data)
# ---------------------------------------------------------------------------
class Provenance(BaseModel):
    """Evidence provenance attached to every published summary."""

    source_item_count: int
    unique_author_count: int
    withheld_item_count: int
    date_range_start: date | None = None
    date_range_end: date | None = None
    generated_at: date
    model: str


class PublicCampusEvidence(BaseModel):
    campus_id: str | None
    campus_label: str
    source_item_count: int
    unique_author_count: int
    date_range_start: date | None = None
    date_range_end: date | None = None


class PublicCampusLabSummary(BaseModel):
    campus_id: str
    confidence: Confidence
    provenance: Provenance
    summary: LlmSummary


class PublicLab(BaseModel):
    lab_id: str
    lab_name: str
    department: str
    campus_ids: list[str] = Field(default_factory=list)
    campus_evidence: list[PublicCampusEvidence] = Field(default_factory=list)
    campus_summaries: list[PublicCampusLabSummary] = Field(default_factory=list)
    research_areas: list[str] = Field(default_factory=list)
    has_summary: bool
    message: str | None = None  # e.g. the insufficient-data notice
    confidence: Confidence | None = None
    provenance: Provenance | None = None
    summary: LlmSummary | None = None


class PublicCampus(BaseModel):
    campus_id: str
    name: str
    short_name: str
    latitude: float
    longitude: float
    address: str
    location_type: CampusLocationType
    represented_lab_count: int
    source_item_count: int
    unique_author_count: int
    evidence_status: EvidenceStatus
    confidence: Confidence | None = None
    provenance: Provenance | None = None
    summary: LlmSummary | None = None


class PublicInstitution(BaseModel):
    institution_id: str
    name: str
    short_name: str
    region: str
    map_center: MapCenter
    website: str | None = None
    campuses: list[PublicCampus] = Field(default_factory=list)
    campus_unspecified: PublicCampusEvidence
    represented_lab_count: int
    source_item_count: int
    unique_author_count: int
    date_range_start: date | None = None
    date_range_end: date | None = None
    overall_themes: list[str] = Field(default_factory=list)
    confidence: Confidence | None = None
    last_updated: date | None = None
    departments: list[str] = Field(default_factory=list)
    research_areas: list[str] = Field(default_factory=list)
    labs: list[PublicLab] = Field(default_factory=list)


class ExportMeta(BaseModel):
    generated_at: datetime
    model: str
    prompt_version: str
    min_items: int
    min_authors: int
    institution_count: int
    published_lab_count: int
    withheld_lab_count: int
    total_source_items: int
    dataset_kind: DatasetKind
    dataset_note: str
    disclaimer: str
