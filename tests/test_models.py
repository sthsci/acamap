import pytest
from pydantic import ValidationError

from pipeline.models import EngagementSnapshot, LlmSummary, RawPost, Theme


def _raw(**overrides):
    base = dict(
        source="rednote",
        post_id="p1",
        comment_id="",
        author_id="a1",
        text="hello",
        posted_at="2025-09-01T09:00:00",
        collected_at="2026-02-01T12:00:00",
        institution_id="imperial",
        department="",
        lab_name="",
        researcher_name="",
        source_url="",
        likes_at_collection="10",
        comments_at_collection="2",
    )
    base.update(overrides)
    return RawPost.model_validate(base)


def test_blank_optionals_become_none():
    raw = _raw()
    assert raw.comment_id is None
    assert raw.department is None
    assert raw.lab_name is None
    assert raw.researcher_name is None
    assert raw.source_url is None


def test_counts_are_coerced_to_int():
    raw = _raw(likes_at_collection="15", comments_at_collection="")
    assert raw.likes_at_collection == 15
    assert raw.comments_at_collection == 0


def test_kind_is_comment_when_comment_id_present():
    assert _raw().kind == "post"
    assert _raw(comment_id="c1").kind == "comment"


def test_dedupe_key_distinguishes_post_and_comment():
    assert _raw().dedupe_key() == ("p1", "")
    assert _raw(comment_id="c1").dedupe_key() == ("p1", "c1")


def test_engagement_snapshot_coerces_counts():
    snap = EngagementSnapshot(collected_at="2026-02-01T12:00:00", likes="7", comments="")
    assert snap.likes == 7
    assert snap.comments == 0


def test_llm_summary_rejects_invalid_confidence():
    with pytest.raises(ValidationError):
        LlmSummary(overview="x", confidence="green")


def test_llm_summary_accepts_valid_confidence():
    for level in ("low", "medium", "high"):
        assert LlmSummary(overview="x", confidence=level).confidence == level


def test_theme_rejects_negative_count():
    with pytest.raises(ValidationError):
        Theme(theme="t", description="d", supporting_item_count=-1)
