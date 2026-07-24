from pipeline.moderation import classify, moderate
from tests.conftest import make_item


def test_clean_text_is_not_flagged():
    assert classify("The supervisor is supportive and the lab is well funded.") == []
    assert classify("组里氛围友好，导师很支持。") == []


def test_serious_allegation_detected_en_and_zh():
    assert "serious_allegation" in classify("There was harassment in the group.")
    assert "serious_allegation" in classify("某老师涉嫌学术造假。")


def test_medical_identifying_detected():
    assert "medical_identifying" in classify("I was diagnosed with depression.")
    assert "medical_identifying" in classify("有人自杀未遂。")


def test_targeted_insult_detected():
    assert "targeted_insult" in classify("The PI is an idiot.")
    assert "targeted_insult" in classify("他就是个废物。")


def test_moderate_splits_and_records_reasons():
    items = [
        make_item("supportive and collaborative group", "a1", "i1"),
        make_item("there were rumours of harassment", "a2", "i2"),
        make_item("组里氛围友好", "a3", "i3"),
    ]
    kept, withheld = moderate(items)
    assert {i.item_id for i in kept} == {"i1", "i3"}
    assert len(withheld) == 1
    assert withheld[0].item_id == "i2"
    assert "serious_allegation" in withheld[0].reasons


def test_normal_workplace_pressure_is_kept():
    # generic stress/pressure/workload are legitimate themes, not withheld
    assert classify("The workload is heavy and there is deadline pressure.") == []
