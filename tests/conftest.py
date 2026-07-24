"""Shared pytest fixtures."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from pipeline.config import Settings
from pipeline.models import AnonymisedItem

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_INSTITUTIONS = REPO_ROOT / "data" / "institutions"
SAMPLE_CSV = REPO_ROOT / "data" / "samples" / "synthetic_posts.csv"
SAMPLE_JSON = REPO_ROOT / "data" / "samples" / "synthetic_posts.json"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """A Settings pointing entirely at an isolated temp tree.

    The real institution catalogue is copied in so aggregation/export work.
    """
    data_dir = tmp_path / "data"
    (data_dir / "institutions").mkdir(parents=True)
    shutil.copy(DATA_INSTITUTIONS / "institutions.json", data_dir / "institutions")
    shutil.copy(DATA_INSTITUTIONS / "regions.json", data_dir / "institutions")
    cfg = Settings(
        data_dir=data_dir,
        web_public_dir=tmp_path / "web" / "public" / "data",
        hash_salt="test-salt",
        min_items=5,
        min_authors=3,
    )
    cfg.ensure_dirs()
    return cfg


def make_item(
    text: str,
    author: str,
    item_id: str,
    *,
    institution: str = "imperial",
    department: str = "Computing",
    lab: str = "Adaptive Systems Lab",
    campus: str | None = "imperial-south-kensington",
    posted: str = "2025-09-01T09:00:00",
) -> AnonymisedItem:
    return AnonymisedItem(
        source="test",
        item_id=item_id,
        post_hash=item_id,
        comment_hash=None,
        author_hash=author,
        kind="post",
        text=text,
        posted_at=posted,
        institution_id=institution,
        department=department,
        lab_name=lab,
        campus_id=campus,
        campus_assignment_method="provided" if campus else "unspecified",
        campus_assignment_confidence="high" if campus else None,
        engagement=[],
    )


@pytest.fixture
def item_factory():
    return make_item


@pytest.fixture
def exported(settings: Settings):
    """Run the whole pipeline on the synthetic sample into the temp tree."""
    from pipeline.export import export
    from pipeline.ingest import ingest_file, write_processed
    from pipeline.llm import HeuristicSummariser
    from pipeline.summarize import run_summarise

    items = ingest_file(SAMPLE_CSV, settings)
    write_processed(items, settings)
    run_summarise(HeuristicSummariser(), settings)
    paths = export(settings)
    return paths, settings
