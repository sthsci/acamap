from pipeline.aggregate import INSUFFICIENT_DATA_MESSAGE, group_by_lab
from pipeline.llm import HeuristicSummariser, build_user_prompt
from pipeline.summarize import build_dataset
from tests.conftest import make_item


def _mixed_items(n, lab="Adaptive Systems Lab", institution="imperial", department="Computing"):
    texts = [
        "The supervisor is supportive and the group is collaborative.",
        "The workload is heavy and there is deadline pressure.",
        "The group is international and interdisciplinary.",
        "导师很支持，资源充足。",
        "压力有点大，工作量比较多。",
    ]
    return [
        make_item(texts[i % len(texts)], f"a{i % 4}", f"{lab}-{i}",
                  lab=lab, institution=institution, department=department)
        for i in range(n)
    ]


def test_heuristic_returns_valid_summary():
    group = group_by_lab(_mixed_items(8))[0]
    summary = HeuristicSummariser().summarise(group)
    assert summary.confidence in {"low", "medium", "high"}
    assert summary.positive_themes  # supportive/collaborative present
    assert summary.challenge_themes  # workload/pressure present
    assert summary.neutral_observations
    assert all(t.supporting_item_count > 0 for t in summary.positive_themes)


def test_heuristic_is_deterministic():
    group = group_by_lab(_mixed_items(8))[0]
    s = HeuristicSummariser()
    assert s.summarise(group).model_dump() == s.summarise(group).model_dump()


def test_confidence_scales_with_evidence():
    low = HeuristicSummariser().summarise(group_by_lab(_mixed_items(5))[0])
    high = HeuristicSummariser().summarise(group_by_lab(_mixed_items(16))[0])
    order = {"low": 1, "medium": 2, "high": 3}
    assert order[high.confidence] >= order[low.confidence]


def test_prompt_includes_json_contract_and_items():
    group = group_by_lab(_mixed_items(5))[0]
    prompt = build_user_prompt(group)
    assert "JSON" in prompt
    assert "confidence" in prompt
    assert "1." in prompt  # numbered items


def test_build_dataset_publishes_and_holds(settings):
    items = _mixed_items(6, lab="Adaptive Systems Lab") + _mixed_items(
        2, lab="Visual Computing Group"
    )
    result = build_dataset(items, [], HeuristicSummariser(), settings)
    imperial = next(i for i in result.institutions if i.institution_id == "imperial")
    labs = {lab.lab_name: lab for lab in imperial.labs}

    published = labs["Adaptive Systems Lab"]
    assert published.has_summary is True
    assert published.summary is not None
    assert published.provenance.source_item_count == 6

    held = labs["Visual Computing Group"]
    assert held.has_summary is False
    assert held.message == INSUFFICIENT_DATA_MESSAGE

    # a catalogue lab with no data at all still appears, marked insufficient
    empty = labs["Neurotechnology Lab"]
    assert empty.has_summary is False


def test_institution_rollup_counts(settings):
    items = _mixed_items(6, lab="Adaptive Systems Lab")
    result = build_dataset(items, [], HeuristicSummariser(), settings)
    imperial = next(i for i in result.institutions if i.institution_id == "imperial")
    assert imperial.represented_lab_count == 1
    assert imperial.source_item_count == 6
    assert imperial.confidence in {"low", "medium", "high"}
    assert imperial.overall_themes
