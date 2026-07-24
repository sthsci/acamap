"""Tests for the Ollama summariser using a mocked HTTP layer (no server needed)."""

import json

import httpx
import pytest

from pipeline import llm
from pipeline.aggregate import group_by_lab
from pipeline.llm import (
    OllamaSummariser,
    OllamaUnavailableError,
    SummarisationError,
    build_user_prompt,
    cache_signature,
)
from tests.conftest import make_item

VALID_SUMMARY = {
    "overview": "A neutral paragraph.",
    "positive_themes": [{"theme": "Support", "description": "d", "supporting_item_count": 2}],
    "challenge_themes": [],
    "neutral_observations": [],
    "confidence": "medium",
    "limitations": [],
    "withheld_item_count": 0,
}


class FakeResponse:
    def __init__(self, content: str):
        self._content = content

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return {"message": {"content": self._content}}


def _group():
    items = [make_item("supportive collaborative", f"a{i % 3}", f"i{i}") for i in range(6)]
    return group_by_lab(items)[0]


def test_summarise_parses_and_validates(monkeypatch):
    monkeypatch.setattr(
        llm.httpx, "post", lambda *a, **k: FakeResponse(json.dumps(VALID_SUMMARY))
    )
    summariser = OllamaSummariser(host="http://x", model="test-model")
    result = summariser.summarise(_group())
    assert result.confidence == "medium"
    assert result.positive_themes[0].theme == "Support"


def test_summarise_retries_on_bad_json_then_succeeds(monkeypatch):
    calls = {"n": 0}

    def flaky(*_a, **_k):
        calls["n"] += 1
        return FakeResponse("not json" if calls["n"] == 1 else json.dumps(VALID_SUMMARY))

    monkeypatch.setattr(llm.httpx, "post", flaky)
    summariser = OllamaSummariser(host="http://x", model="test-model", max_retries=3)
    assert summariser.summarise(_group()).confidence == "medium"
    assert calls["n"] == 2


def test_invalid_confidence_raises_after_retries(monkeypatch):
    bad = {**VALID_SUMMARY, "confidence": "green"}
    monkeypatch.setattr(llm.httpx, "post", lambda *a, **k: FakeResponse(json.dumps(bad)))
    summariser = OllamaSummariser(host="http://x", model="test-model", max_retries=2)
    with pytest.raises(SummarisationError):
        summariser.summarise(_group())


def test_connect_error_becomes_unavailable(monkeypatch):
    def boom(*_a, **_k):
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(llm.httpx, "post", boom)
    summariser = OllamaSummariser(host="http://x", model="test-model")
    with pytest.raises(OllamaUnavailableError):
        summariser.summarise(_group())


def test_prompt_and_cache_signature_are_stable():
    group = _group()
    assert "Return ONLY a JSON object" in build_user_prompt(group)
    sig = cache_signature(group, "test-model")
    assert sig[1] == "test-model"
    assert cache_signature(group, "test-model") == sig
