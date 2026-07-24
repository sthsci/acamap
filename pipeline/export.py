"""Export sanitised, aggregated JSON to the website's public data directory.

This is the ONLY step that writes into ``web/public/data``. Every payload is
run through :func:`pipeline.privacy.assert_clean` before it is written, so a
leak fails the export loudly instead of shipping.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from . import privacy
from .catalog import load_regions
from .config import PROMPT_VERSION, Settings, get_settings
from .models import ExportMeta, PublicInstitution
from .summarize import load_dataset

DISCLAIMER = (
    "All summaries reflect unverified, user-reported perceptions aggregated from "
    "public social media, not verified facts. Selection bias, unverifiable "
    "identities and platform recommendation algorithms limit interpretation. No "
    "ranking of individual researchers is made or implied."
)


def _write_json(path: Path, payload: object) -> None:
    privacy.assert_clean(payload)  # defence in depth: never write a leak
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _build_meta(institutions: list[PublicInstitution], settings: Settings) -> ExportMeta:
    published = [lab for inst in institutions for lab in inst.labs if lab.has_summary]
    withheld = [
        lab
        for inst in institutions
        for lab in inst.labs
        if not lab.has_summary and lab.provenance and lab.provenance.source_item_count > 0
    ]
    models = Counter(
        lab.provenance.model for lab in published if lab.provenance and lab.provenance.model
    )
    model = models.most_common(1)[0][0] if models else settings.model
    return ExportMeta(
        generated_at=datetime.now(),
        model=model,
        prompt_version=PROMPT_VERSION,
        min_items=settings.min_items,
        min_authors=settings.min_authors,
        institution_count=len(institutions),
        published_lab_count=len(published),
        withheld_lab_count=len(withheld),
        total_source_items=sum(inst.source_item_count for inst in institutions),
        disclaimer=DISCLAIMER,
    )


def export(settings: Settings | None = None) -> dict[str, Path]:
    settings = settings or get_settings()
    institutions = load_dataset(settings)
    regions = load_regions(settings)
    meta = _build_meta(institutions, settings)

    out_dir = settings.web_public_dir
    paths = {
        "institutions": out_dir / "institutions.json",
        "regions": out_dir / "regions.json",
        "meta": out_dir / "meta.json",
    }

    _write_json(paths["institutions"], [i.model_dump(mode="json") for i in institutions])
    _write_json(paths["regions"], [r.model_dump(mode="json") for r in regions])
    _write_json(paths["meta"], meta.model_dump(mode="json"))
    return paths
