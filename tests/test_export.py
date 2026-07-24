import json

from pipeline.cache import SummaryCache
from pipeline.llm import HeuristicSummariser, cache_signature
from pipeline.summarize import build_dataset
from tests.conftest import make_item


def test_export_writes_all_files(exported):
    paths, _ = exported
    for key in ("institutions", "regions", "meta"):
        assert paths[key].exists()


def test_exported_institutions_shape(exported):
    paths, _ = exported
    data = json.loads(paths["institutions"].read_text(encoding="utf-8"))
    assert len(data) == 6  # all catalogue institutions appear as map markers
    imperial = next(i for i in data if i["institution_id"] == "imperial")
    assert imperial["region"] == "london"
    assert imperial["represented_lab_count"] >= 1
    assert any(lab["has_summary"] for lab in imperial["labs"])
    assert any(not lab["has_summary"] for lab in imperial["labs"])


def test_exported_meta_counts(exported):
    paths, _ = exported
    meta = json.loads(paths["meta"].read_text(encoding="utf-8"))
    assert meta["institution_count"] == 6
    assert meta["published_lab_count"] == 7
    assert meta["min_items"] == 5 and meta["min_authors"] == 3
    assert "unverified" in meta["disclaimer"].lower()


def test_regions_include_active_and_coming_soon(exported):
    paths, _ = exported
    regions = json.loads(paths["regions"].read_text(encoding="utf-8"))
    by_id = {r["id"]: r for r in regions}
    assert by_id["london"]["status"] == "active"
    assert by_id["oxford"]["status"] == "coming_soon"
    assert by_id["cambridge"]["status"] == "coming_soon"


def test_summary_cache_roundtrip(settings):
    items = [
        make_item("supportive collaborative group", f"a{i % 3}", f"id-{i}")
        for i in range(6)
    ]
    from pipeline.aggregate import group_by_lab

    group = group_by_lab(items)[0]
    cache = SummaryCache(settings)
    key = cache.key_for(cache_signature(group, "offline-heuristic"))
    assert cache.get(key) is None

    summary = HeuristicSummariser().summarise(group)
    cache.set(key, summary)
    assert cache.get(key) is not None
    assert cache.get(key).model_dump() == summary.model_dump()


def test_dry_run_writes_nothing(settings):
    items = [
        make_item("supportive collaborative group", f"a{i % 3}", f"id-{i}")
        for i in range(6)
    ]
    result = build_dataset(items, [], HeuristicSummariser(), settings, dry_run=True)
    # nothing summarised, but the plan is populated
    assert any(p.publishable for p in result.plans)
    published = [
        lab
        for inst in result.institutions
        for lab in inst.labs
        if lab.has_summary
    ]
    assert published == []
