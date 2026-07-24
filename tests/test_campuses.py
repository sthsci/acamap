from copy import deepcopy

import pytest

from pipeline.catalog import load_institutions, resolve_campus, validate_catalogue
from pipeline.llm import HeuristicSummariser
from pipeline.models import RawPost
from pipeline.summarize import build_dataset
from tests.conftest import make_item


def _raw(**overrides):
    payload = {
        "source": "test",
        "post_id": "p1",
        "author_id": "a1",
        "text": "supportive group",
        "posted_at": "2025-09-01T09:00:00",
        "collected_at": "2026-02-01T09:00:00",
        "institution_id": "imperial",
        "department": "Computing",
        "lab_name": "Adaptive Systems Lab",
    }
    payload.update(overrides)
    return RawPost.model_validate(payload)


def test_catalogue_campus_references_are_valid(settings):
    institutions = load_institutions(settings)
    validate_catalogue(institutions)
    assert sum(len(inst.campuses) for inst in institutions) >= 20
    assert all(
        campus.provenance.official_source_url
        for inst in institutions
        for campus in inst.campuses
    )
    assert all(
        campus.provenance.coordinate_source_url
        for inst in institutions
        for campus in inst.campuses
    )


def test_reviewed_location_anchors_and_types(settings):
    institutions = {item.institution_id: item for item in load_institutions(settings)}
    locations = {
        campus.campus_id: campus
        for institution in institutions.values()
        for campus in institution.campuses
    }

    assert locations["ucl-bloomsbury"].provenance.coordinate_source_url.endswith(
        "/relation/11373735"
    )
    assert locations["ucl-east"].name == "UCL East"
    assert locations["ucl-east"].provenance.note and "Marshgate" in locations[
        "ucl-east"
    ].provenance.note
    assert locations["qmul-charterhouse-square"].provenance.coordinate_source_url.endswith(
        "/node/26816010"
    )
    assert locations["lshtm-keppel-street"].provenance.coordinate_source_url.endswith(
        "/way/413975405"
    )
    assert locations["kcl-denmark-hill"].address.endswith("SE5 8AF")

    assert locations["ucl-queen-square"].location_type == "research_institute"
    assert locations["ucl-ophthalmology"].location_type == "research_institute"
    assert locations["lshtm-keppel-street"].location_type == "research_location"
    assert locations["lshtm-tavistock-place"].location_type == "research_location"


def test_catalogue_rejects_dangling_lab_campus(settings):
    institutions = deepcopy(load_institutions(settings))
    institutions[0].labs[0].campus_ids.append("not-a-campus")
    with pytest.raises(ValueError, match="unknown campus"):
        validate_catalogue(institutions)


def test_catalogue_rejects_duplicate_physical_markers(settings):
    institutions = deepcopy(load_institutions(settings))
    first = institutions[0].campuses[0]
    second = institutions[1].campuses[0]
    second.latitude = first.latitude
    second.longitude = first.longitude
    with pytest.raises(ValueError, match="duplicate physical marker"):
        validate_catalogue(institutions)


def test_campus_assignment_methods(settings):
    institutions = load_institutions(settings)
    assert resolve_campus(
        _raw(campus_id="imperial-white-city"), institutions
    ) == ("imperial-white-city", "provided", "high")
    assert resolve_campus(
        _raw(campus_name_raw="White City"), institutions
    ) == ("imperial-white-city", "catalogue_match", "high")
    assert resolve_campus(
        _raw(lab_name="Visual Computing Group"), institutions
    ) == ("imperial-white-city", "inferred_from_lab", "medium")


def test_ambiguous_multi_campus_lab_stays_unspecified(settings):
    institutions = load_institutions(settings)
    assert resolve_campus(_raw(), institutions) == (None, "unspecified", None)
    assert resolve_campus(
        _raw(lab_name="Visual Computing Group", campus_name_raw="unknown annex"),
        institutions,
    ) == (None, "unspecified", None)


def test_multi_campus_lab_is_not_duplicated_in_institution_totals(settings):
    items = [
        make_item(
            "supportive collaborative group",
            f"author-{i % 3}",
            f"item-{i}",
            campus=(
                "imperial-south-kensington"
                if i < 3
                else "imperial-white-city"
            ),
        )
        for i in range(6)
    ]
    result = build_dataset(items, [], HeuristicSummariser(), settings)
    imperial = next(inst for inst in result.institutions if inst.institution_id == "imperial")
    assert imperial.represented_lab_count == 1
    assert imperial.source_item_count == 6
    assert imperial.unique_author_count == 3
    by_campus = {campus.campus_id: campus for campus in imperial.campuses}
    assert by_campus["imperial-south-kensington"].source_item_count == 3
    assert by_campus["imperial-white-city"].source_item_count == 3


def test_institution_authors_are_deduplicated_across_labs(settings):
    items = [
        make_item(
            "supportive group",
            "same-author",
            "one",
            lab="Adaptive Systems Lab",
            campus="imperial-south-kensington",
        ),
        make_item(
            "helpful group",
            "same-author",
            "two",
            lab="Visual Computing Group",
            campus="imperial-white-city",
        ),
    ]
    result = build_dataset(items, [], HeuristicSummariser(), settings)
    imperial = next(inst for inst in result.institutions if inst.institution_id == "imperial")
    assert imperial.unique_author_count == 1
    assert imperial.source_item_count == 2


def test_unspecified_items_do_not_enter_campus_statistics(settings):
    items = [
        make_item("supportive", "author-a", "one", campus=None),
        make_item("helpful", "author-b", "two", campus="imperial-white-city"),
    ]
    result = build_dataset(items, [], HeuristicSummariser(), settings)
    imperial = next(inst for inst in result.institutions if inst.institution_id == "imperial")
    white_city = next(
        campus for campus in imperial.campuses if campus.campus_id == "imperial-white-city"
    )
    assert white_city.source_item_count == 1
    assert imperial.campus_unspecified.source_item_count == 1


def test_multi_campus_lab_gets_separate_summary_only_at_threshold(settings):
    items = [
        make_item(
            "supportive collaborative group",
            f"author-{i % 3}",
            f"south-{i}",
            campus="imperial-south-kensington",
        )
        for i in range(5)
    ] + [
        make_item(
            "heavy workload but helpful mentor",
            f"other-author-{i % 2}",
            f"white-{i}",
            campus="imperial-white-city",
        )
        for i in range(5)
    ]
    result = build_dataset(items, [], HeuristicSummariser(), settings)
    imperial = next(inst for inst in result.institutions if inst.institution_id == "imperial")
    lab = next(item for item in imperial.labs if item.lab_name == "Adaptive Systems Lab")
    assert [summary.campus_id for summary in lab.campus_summaries] == [
        "imperial-south-kensington"
    ]
