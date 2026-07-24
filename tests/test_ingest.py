import json

from pipeline.adapters import get_adapter
from pipeline.adapters.json_adapter import JsonAdapter
from pipeline.config import Settings
from pipeline.ingest import anonymise, ingest_file, merge_snapshots
from pipeline.models import RawPost


def _raw(post_id="p1", author="a1", collected="2026-02-01T12:00:00", **kw):
    return RawPost.model_validate(
        dict(
            source="rednote",
            post_id=post_id,
            author_id=author,
            text="the group is supportive",
            posted_at="2025-09-01T09:00:00",
            collected_at=collected,
            institution_id="imperial",
            likes_at_collection="10",
            comments_at_collection="1",
            source_url="https://example.invalid/user/123",
            researcher_name="Prof X",
            **kw,
        )
    )


def test_anonymise_hashes_ids_and_drops_source_url():
    item = anonymise(_raw(), "salt")
    assert item.post_hash and item.post_hash != "p1"
    assert item.author_hash and item.author_hash != "a1"
    # source_url must not survive anonymisation at all
    assert not hasattr(item, "source_url")
    # researcher_name is retained internally for entity resolution only
    assert item.researcher_name == "Prof X"
    assert item.text == "the group is supportive"


def test_anonymise_keeps_raw_campus_text_internal_only():
    item = anonymise(_raw(campus_name_raw="White City"), "salt")
    assert item.campus_name_raw == "White City"
    assert item.campus_assignment_method == "unspecified"


def test_merge_snapshots_collapses_same_item():
    a = anonymise(_raw(collected="2026-02-01T12:00:00"), "salt")
    b = anonymise(_raw(collected="2026-03-01T12:00:00"), "salt")
    merged = merge_snapshots([a, b])
    assert len(merged) == 1
    assert len(merged[0].engagement) == 2
    # engagement is sorted chronologically
    times = [s.collected_at for s in merged[0].engagement]
    assert times == sorted(times)


def test_distinct_items_are_kept_separate():
    a = anonymise(_raw(post_id="p1"), "salt")
    b = anonymise(_raw(post_id="p2"), "salt")
    assert len(merge_snapshots([a, b])) == 2


def test_csv_and_json_adapters_selected_by_extension(tmp_path):
    from pipeline.adapters.csv_adapter import CsvAdapter

    assert isinstance(get_adapter(tmp_path / "x.csv"), CsvAdapter)
    assert isinstance(get_adapter(tmp_path / "x.json"), JsonAdapter)


def test_json_adapter_reads_records_wrapper(tmp_path):
    path = tmp_path / "posts.json"
    record = {
        "source": "rednote",
        "post_id": "p9",
        "author_id": "a9",
        "text": "hi",
        "posted_at": "2025-09-01T09:00:00",
        "collected_at": "2026-02-01T12:00:00",
        "institution_id": "ucl",
        "likes_at_collection": 1,
        "comments_at_collection": 0,
    }
    path.write_text(json.dumps({"records": [record]}), encoding="utf-8")
    items = ingest_file(path, Settings(hash_salt="salt"))
    assert len(items) == 1
    assert items[0].institution_id == "ucl"
