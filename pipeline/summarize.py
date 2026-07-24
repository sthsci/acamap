"""Moderate, aggregate and summarise campus-aware public data.

Lab summaries remain the primary output. Canonical campus assignments also
support campus statistics, campus-wide summaries, and (only when thresholds
are independently met) campus-specific summaries for multi-campus labs.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime

from .aggregate import INSUFFICIENT_DATA_MESSAGE, LabGroup, group_by_lab
from .cache import SummaryCache
from .catalog import load_institutions
from .config import Settings, get_settings
from .ingest import load_processed
from .llm import Summariser, cache_signature
from .models import (
    AnonymisedItem,
    Campus,
    Confidence,
    Institution,
    Lab,
    LlmSummary,
    ModerationRecord,
    Provenance,
    PublicCampus,
    PublicCampusEvidence,
    PublicCampusLabSummary,
    PublicInstitution,
    PublicLab,
)
from .moderation import moderate, write_queue

_CONFIDENCE_RANK: dict[Confidence, int] = {"low": 1, "medium": 2, "high": 3}
_RANK_CONFIDENCE: dict[int, Confidence] = {1: "low", 2: "medium", 3: "high"}


@dataclass
class LabPlan:
    institution_id: str
    department: str
    lab_name: str
    item_count: int
    unique_author_count: int
    withheld_count: int
    publishable: bool
    cached: bool


@dataclass
class SummariseResult:
    institutions: list[PublicInstitution] = field(default_factory=list)
    plans: list[LabPlan] = field(default_factory=list)
    withheld: list[ModerationRecord] = field(default_factory=list)


def _lab_catalog(inst: Institution) -> dict[tuple[str, str], Lab]:
    return {(lab.department, lab.name): lab for lab in inst.labs}


def _summarise_group(
    group: LabGroup,
    summariser: Summariser,
    cache: SummaryCache,
    force: bool,
) -> tuple[LlmSummary, bool]:
    key = cache.key_for(cache_signature(group, summariser.name))
    if not force:
        cached = cache.get(key)
        if cached is not None:
            return cached, True
    summary = summariser.summarise(group)
    cache.set(key, summary)
    return summary, False


def _provenance(
    group: LabGroup, summariser: Summariser
) -> Provenance:
    start, end = group.date_range
    return Provenance(
        source_item_count=group.item_count,
        unique_author_count=group.unique_author_count,
        withheld_item_count=group.withheld_count,
        date_range_start=start,
        date_range_end=end,
        generated_at=date.today(),
        model=summariser.name,
    )


def _group_subset(
    group: LabGroup,
    items: list[AnonymisedItem],
    withheld_count: int = 0,
) -> LabGroup:
    return LabGroup(
        institution_id=group.institution_id,
        department=group.department,
        lab_name=group.lab_name,
        items=items,
        withheld_count=withheld_count,
    )


def _evidence(
    campus_id: str | None, label: str, items: list[AnonymisedItem]
) -> PublicCampusEvidence:
    dates = [item.posted_at.date() for item in items]
    return PublicCampusEvidence(
        campus_id=campus_id,
        campus_label=label,
        source_item_count=len({item.item_id for item in items}),
        unique_author_count=len({item.author_hash for item in items}),
        date_range_start=min(dates) if dates else None,
        date_range_end=max(dates) if dates else None,
    )


def _public_lab_from_group(
    group: LabGroup,
    catalog_lab: Lab | None,
    campuses: dict[str, Campus],
    campus_withheld: dict[str, int],
    settings: Settings,
    summariser: Summariser,
    cache: SummaryCache,
    force: bool,
    dry_run: bool,
) -> tuple[PublicLab, LabPlan]:
    lab_id = catalog_lab.lab_id if catalog_lab else _slug(group.institution_id, group.lab_name)
    research_areas = catalog_lab.research_areas if catalog_lab else []
    campus_ids = catalog_lab.campus_ids if catalog_lab else sorted(
        {item.campus_id for item in group.items if item.campus_id}
    )
    provenance = _provenance(group, summariser)
    is_publishable = group.meets_threshold(settings)

    evidence: list[PublicCampusEvidence] = []
    for campus_id in campus_ids:
        campus_items = [item for item in group.items if item.campus_id == campus_id]
        if campus_items:
            label = campuses.get(campus_id).short_name if campus_id in campuses else campus_id
            evidence.append(_evidence(campus_id, label, campus_items))
    unspecified = [item for item in group.items if item.campus_id is None]
    if unspecified:
        evidence.append(_evidence(None, "Location unspecified", unspecified))

    campus_summaries: list[PublicCampusLabSummary] = []
    if catalog_lab and len(catalog_lab.campus_ids) > 1:
        for campus_id in catalog_lab.campus_ids:
            campus_items = [item for item in group.items if item.campus_id == campus_id]
            campus_group = _group_subset(
                group, campus_items, campus_withheld.get(campus_id, 0)
            )
            if not campus_group.meets_threshold(settings) or dry_run:
                continue
            summary, _ = _summarise_group(
                campus_group, summariser, cache, force
            )
            campus_summaries.append(
                PublicCampusLabSummary(
                    campus_id=campus_id,
                    confidence=summary.confidence,
                    provenance=_provenance(campus_group, summariser),
                    summary=summary,
                )
            )

    cache_key = cache.key_for(cache_signature(group, summariser.name))
    cached_available = cache.get(cache_key) is not None
    if is_publishable and not dry_run:
        summary, _ = _summarise_group(group, summariser, cache, force)
        confidence = summary.confidence
    else:
        summary = None
        confidence = None

    plan = LabPlan(
        group.institution_id,
        group.department,
        group.lab_name,
        group.item_count,
        group.unique_author_count,
        group.withheld_count,
        publishable=is_publishable,
        cached=cached_available and not force,
    )
    return (
        PublicLab(
            lab_id=lab_id,
            lab_name=group.lab_name,
            department=group.department,
            campus_ids=campus_ids,
            campus_evidence=evidence,
            campus_summaries=campus_summaries,
            research_areas=research_areas,
            has_summary=is_publishable and not dry_run,
            message=(
                None
                if is_publishable and not dry_run
                else (
                    "Pending summarisation (dry run)."
                    if is_publishable
                    else INSUFFICIENT_DATA_MESSAGE
                )
            ),
            confidence=confidence,
            provenance=provenance,
            summary=summary,
        ),
        plan,
    )


def _slug(*parts: str) -> str:
    joined = "-".join(p.lower() for p in parts if p)
    return "".join(c if c.isalnum() or c == "-" else "-" for c in joined).strip("-")


def _rollup(
    labs: list[PublicLab], items: list[AnonymisedItem]
) -> dict[str, object]:
    published = [lab for lab in labs if lab.has_summary and lab.summary]
    item_by_id = {item.item_id: item for item in items}
    unique_items = list(item_by_id.values())
    dates = [item.posted_at.date() for item in unique_items]

    theme_counter: Counter[str] = Counter()
    for lab in published:
        assert lab.summary
        for theme in [*lab.summary.positive_themes, *lab.summary.challenge_themes]:
            theme_counter[theme.theme] += 1

    confidence: Confidence | None = None
    if published:
        avg = round(
            sum(_CONFIDENCE_RANK[lab.summary.confidence] for lab in published if lab.summary)
            / len(published)
        )
        confidence = _RANK_CONFIDENCE[min(3, max(1, avg))]

    return {
        "represented_lab_count": len(
            {
                (item.department or "Unspecified", item.lab_name or "Unspecified")
                for item in unique_items
            }
        ),
        "source_item_count": len(unique_items),
        "unique_author_count": len({item.author_hash for item in unique_items}),
        "date_range_start": min(dates) if dates else None,
        "date_range_end": max(dates) if dates else None,
        "overall_themes": [name for name, _ in theme_counter.most_common(6)],
        "confidence": confidence,
        "last_updated": date.today() if published else None,
        "research_areas": sorted({area for lab in labs for area in lab.research_areas}),
    }


def _public_campus(
    campus: Campus,
    items: list[AnonymisedItem],
    withheld_count: int,
    settings: Settings,
    summariser: Summariser,
    cache: SummaryCache,
    force: bool,
    dry_run: bool,
) -> PublicCampus:
    group = LabGroup(
        institution_id=items[0].institution_id if items else campus.campus_id.split("-")[0],
        department="All departments",
        lab_name=campus.name,
        items=items,
        withheld_count=withheld_count,
    )
    meets = group.meets_threshold(settings)
    summary: LlmSummary | None = None
    if meets and not dry_run:
        summary, _ = _summarise_group(group, summariser, cache, force)
    status = (
        "summary_available"
        if summary is not None
        else ("below_threshold" if items else "no_assigned_evidence")
    )
    represented_labs = {
        (item.department or "Unspecified", item.lab_name or "Unspecified")
        for item in items
    }
    return PublicCampus(
        campus_id=campus.campus_id,
        name=campus.name,
        short_name=campus.short_name,
        latitude=campus.latitude,
        longitude=campus.longitude,
        address=campus.address,
        location_type=campus.location_type,
        represented_lab_count=len(represented_labs),
        source_item_count=len({item.item_id for item in items}),
        unique_author_count=len({item.author_hash for item in items}),
        evidence_status=status,
        confidence=summary.confidence if summary else None,
        provenance=_provenance(group, summariser) if items else None,
        summary=summary,
    )


def build_dataset(
    items: list[AnonymisedItem],
    withheld: list[ModerationRecord],
    summariser: Summariser,
    settings: Settings,
    force: bool = False,
    dry_run: bool = False,
) -> SummariseResult:
    cache = SummaryCache(settings)
    groups = group_by_lab(items, withheld)
    groups_by_inst: dict[str, list[LabGroup]] = defaultdict(list)
    items_by_inst: dict[str, list[AnonymisedItem]] = defaultdict(list)
    for group in groups:
        groups_by_inst[group.institution_id].append(group)
    for item in items:
        items_by_inst[item.institution_id].append(item)

    withheld_by_scope: Counter[tuple[str, str, str, str | None]] = Counter()
    for record in withheld:
        withheld_by_scope[
            (
                record.institution_id,
                record.department or "Unspecified",
                record.lab_name or "Unspecified",
                record.campus_id,
            )
        ] += 1

    result = SummariseResult(withheld=withheld)
    for institution in load_institutions(settings):
        catalog = _lab_catalog(institution)
        campus_catalog = {campus.campus_id: campus for campus in institution.campuses}
        seen: set[tuple[str, str]] = set()
        public_labs: list[PublicLab] = []

        for group in groups_by_inst.get(institution.institution_id, []):
            catalog_lab = catalog.get((group.department, group.lab_name))
            campus_withheld = {
                campus_id: withheld_by_scope[
                    (
                        group.institution_id,
                        group.department,
                        group.lab_name,
                        campus_id,
                    )
                ]
                for campus_id in campus_catalog
            }
            lab, plan = _public_lab_from_group(
                group,
                catalog_lab,
                campus_catalog,
                campus_withheld,
                settings,
                summariser,
                cache,
                force,
                dry_run,
            )
            public_labs.append(lab)
            result.plans.append(plan)
            seen.add((group.department, group.lab_name))

        for (department, name), catalog_lab in catalog.items():
            if (department, name) in seen:
                continue
            public_labs.append(
                PublicLab(
                    lab_id=catalog_lab.lab_id,
                    lab_name=name,
                    department=department,
                    campus_ids=catalog_lab.campus_ids,
                    research_areas=catalog_lab.research_areas,
                    has_summary=False,
                    message=INSUFFICIENT_DATA_MESSAGE,
                )
            )

        public_labs.sort(key=lambda lab: (not lab.has_summary, lab.department, lab.lab_name))
        institution_items = items_by_inst.get(institution.institution_id, [])
        public_campuses = [
            _public_campus(
                campus,
                [item for item in institution_items if item.campus_id == campus.campus_id],
                sum(
                    count
                    for (inst_id, _dept, _lab, campus_id), count in withheld_by_scope.items()
                    if inst_id == institution.institution_id and campus_id == campus.campus_id
                ),
                settings,
                summariser,
                cache,
                force,
                dry_run,
            )
            for campus in institution.campuses
        ]
        unspecified_items = [item for item in institution_items if item.campus_id is None]
        result.institutions.append(
            PublicInstitution(
                institution_id=institution.institution_id,
                name=institution.name,
                short_name=institution.short_name,
                region=institution.region,
                map_center=institution.map_center,
                website=institution.website,
                campuses=public_campuses,
                campus_unspecified=_evidence(
                    None, "Location unspecified", unspecified_items
                ),
                departments=[department.name for department in institution.departments],
                labs=public_labs,
                **_rollup(public_labs, institution_items),
            )
        )
    return result


def run_summarise(
    summariser: Summariser,
    settings: Settings | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> SummariseResult:
    settings = settings or get_settings()
    items = load_processed(settings)
    kept, withheld = moderate(items)
    if not dry_run:
        write_queue(withheld, settings)
    result = build_dataset(kept, withheld, summariser, settings, force, dry_run)
    if not dry_run:
        write_dataset(result.institutions, settings)
    return result


def write_dataset(
    institutions: list[PublicInstitution], settings: Settings | None = None
) -> str:
    settings = settings or get_settings()
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    out = settings.processed_dir / "public_dataset.json"
    payload = [inst.model_dump(mode="json") for inst in institutions]
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(out)


def load_dataset(settings: Settings | None = None) -> list[PublicInstitution]:
    settings = settings or get_settings()
    path = settings.processed_dir / "public_dataset.json"
    if not path.exists():
        raise FileNotFoundError(
            f"No summarised dataset at {path}. Run `labvibes summarize` first."
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [PublicInstitution.model_validate(record) for record in payload]


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")
