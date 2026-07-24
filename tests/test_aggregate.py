from pipeline.aggregate import group_by_lab, publishable
from pipeline.config import Settings
from pipeline.models import ModerationRecord
from tests.conftest import make_item

CFG = Settings(min_items=5, min_authors=3)


def _items(n_items, n_authors, lab="Adaptive Systems Lab"):
    return [
        make_item(f"item {i} supportive", f"author-{i % n_authors}", f"id-{lab}-{i}", lab=lab)
        for i in range(n_items)
    ]


def test_grouping_by_lab():
    items = _items(3, 3, lab="Lab A") + _items(2, 2, lab="Lab B")
    groups = {g.lab_name: g for g in group_by_lab(items)}
    assert set(groups) == {"Lab A", "Lab B"}
    assert groups["Lab A"].item_count == 3
    assert groups["Lab B"].item_count == 2


def test_threshold_needs_both_items_and_authors():
    exactly = group_by_lab(_items(5, 3))[0]
    assert exactly.meets_threshold(CFG) is True

    too_few_items = group_by_lab(_items(4, 3))[0]
    assert too_few_items.meets_threshold(CFG) is False

    too_few_authors = group_by_lab(_items(6, 2))[0]
    assert too_few_authors.meets_threshold(CFG) is False


def test_unique_author_count():
    group = group_by_lab(_items(6, 2))[0]
    assert group.unique_author_count == 2


def test_date_range():
    items = [
        make_item("a", "a1", "1", posted="2025-09-01T00:00:00"),
        make_item("b", "a2", "2", posted="2025-10-15T00:00:00"),
    ]
    start, end = group_by_lab(items)[0].date_range
    assert str(start) == "2025-09-01"
    assert str(end) == "2025-10-15"


def test_withheld_counts_attached_to_group():
    items = _items(5, 3, lab="Lab A")
    withheld = [
        ModerationRecord(
            item_id="w1",
            institution_id="imperial",
            department="Computing",
            lab_name="Lab A",
            reasons=["serious_allegation"],
            text="withheld",
            posted_at="2025-09-01T00:00:00",
        )
    ]
    group = group_by_lab(items, withheld)[0]
    assert group.withheld_count == 1


def test_publishable_filters_groups():
    groups = group_by_lab(_items(5, 3, lab="Good") + _items(2, 2, lab="Sparse"))
    names = {g.lab_name for g in publishable(groups, CFG)}
    assert names == {"Good"}
