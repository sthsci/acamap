"""Local-LLM summarisation via Ollama, plus an offline heuristic fallback.

Raw text is ONLY ever sent to the local Ollama endpoint. It is never sent to a
cloud model, a GitHub Action or the browser. The offline summariser sends
nothing anywhere: it derives neutral themes locally and is used for tests, for
``--dry-run`` previews and for environments without Ollama installed.
"""

from __future__ import annotations

import json
import re
from typing import Protocol, runtime_checkable

import httpx

from .aggregate import LabGroup
from .config import PROMPT_VERSION
from .models import LlmSummary, Theme

SYSTEM_PROMPT = (
    "You are summarising anonymised public social-media discussions about "
    "academic research workplaces. Describe only patterns supported by the "
    "supplied material. Treat every statement as an unverified user-reported "
    "perception. Do not identify, diagnose, praise or accuse individual people. "
    "Do not repeat serious allegations, insults, medical information or uniquely "
    "identifying details. Separate recurring positive themes, recurring "
    "challenges and neutral observations. Do not infer absence of a problem from "
    "absence of comments. If evidence is sparse, contradictory or dominated by "
    "one author, reduce the confidence level. Return valid JSON only."
)

_JSON_CONTRACT = """Return ONLY a JSON object with exactly this shape:
{
  "overview": "A concise, neutral paragraph.",
  "positive_themes": [{"theme": "", "description": "", "supporting_item_count": 0}],
  "challenge_themes": [{"theme": "", "description": "", "supporting_item_count": 0}],
  "neutral_observations": [],
  "confidence": "low",
  "limitations": [],
  "withheld_item_count": 0
}
"confidence" must be one of "low", "medium", "high"."""


class OllamaUnavailableError(RuntimeError):
    """Raised when the local Ollama endpoint cannot be reached."""


class SummarisationError(RuntimeError):
    """Raised when a valid summary could not be produced after retries."""


@runtime_checkable
class Summariser(Protocol):
    name: str

    def summarise(self, group: LabGroup) -> LlmSummary: ...


def build_user_prompt(group: LabGroup) -> str:
    """Assemble the user message for a lab group (numbered, anonymised items)."""
    lines = [
        f"Context: {group.item_count} anonymised items from "
        f"{group.unique_author_count} distinct authors discussing a research "
        f"group in the '{group.department}' department.",
        "",
        "Items (each is one user-reported perception, unverified):",
    ]
    for i, text in enumerate(group.texts(), start=1):
        collapsed = " ".join(text.split())
        lines.append(f"{i}. {collapsed}")
    lines += ["", _JSON_CONTRACT]
    return "\n".join(lines)


def cache_signature(group: LabGroup, model: str) -> tuple[str, ...]:
    """Stable parts identifying this summarisation request for caching."""
    return (PROMPT_VERSION, model, *sorted(group.texts()))


# ---------------------------------------------------------------------------
# Ollama (default)
# ---------------------------------------------------------------------------
class OllamaSummariser:
    """Calls a locally running Ollama model and validates its JSON output."""

    def __init__(
        self,
        host: str,
        model: str,
        temperature: float = 0.0,
        seed: int = 7,
        timeout: float = 120.0,
        max_retries: int = 3,
    ) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.seed = seed
        self.timeout = timeout
        self.max_retries = max_retries

    @property
    def name(self) -> str:
        return self.model

    def _call(self, group: LabGroup) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(group)},
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": self.temperature,
                "seed": self.seed,
            },
        }
        try:
            response = httpx.post(
                f"{self.host}/api/chat", json=payload, timeout=self.timeout
            )
            response.raise_for_status()
        except httpx.ConnectError as exc:  # Ollama not running
            raise OllamaUnavailableError(
                f"Could not reach Ollama at {self.host}. Is `ollama serve` running "
                f"and `{self.model}` pulled? Use --offline for a local heuristic."
            ) from exc
        return response.json()["message"]["content"]

    def summarise(self, group: LabGroup) -> LlmSummary:
        last_error: Exception | None = None
        for _ in range(self.max_retries):
            try:
                raw = self._call(group)
                data = json.loads(raw)
                return LlmSummary.model_validate(data)
            except OllamaUnavailableError:
                raise
            except (json.JSONDecodeError, ValueError, KeyError) as exc:
                last_error = exc  # malformed JSON or failed validation -> retry
        raise SummarisationError(
            f"Model '{self.model}' did not return valid summary JSON after "
            f"{self.max_retries} attempts: {last_error}"
        )


# ---------------------------------------------------------------------------
# Offline heuristic (no network; deterministic)
# ---------------------------------------------------------------------------
_POSITIVE_THEMES: list[tuple[str, str, list[str]]] = [
    (
        "Supportive supervision",
        "Several items describe supervisors or mentors as approachable and helpful.",
        ["support", "mentor", "helpful", "approachable", "kind", "支持", "导师", "友好"],
    ),
    (
        "Collaborative atmosphere",
        "Items mention collaboration and a friendly group culture.",
        ["collaborat", "friendly", "welcoming", "team", "atmosphere", "合作", "氛围"],
    ),
    (
        "Resources and facilities",
        "Items note access to funding, equipment or facilities.",
        ["funding", "equipment", "resource", "facilit", "well-funded", "资源", "经费", "设备"],
    ),
    (
        "Research freedom",
        "Items describe autonomy in choosing research directions.",
        ["freedom", "autonom", "flexible", "independent", "自由", "灵活"],
    ),
]

_CHALLENGE_THEMES: list[tuple[str, str, list[str]]] = [
    (
        "Workload and hours",
        "Items report long hours or a heavy workload.",
        ["hours", "workload", "overtime", "long day", "加班", "工作量"],
    ),
    (
        "Pressure and expectations",
        "Items describe pressure from deadlines or high expectations.",
        ["pressure", "stress", "deadline", "expectation", "competitive", "压力", "竞争"],
    ),
    (
        "Communication and clarity",
        "Items mention unclear communication or expectations.",
        ["communication", "unclear", "confusing", "disorganis", "沟通", "混乱"],
    ),
    (
        "Administrative burden",
        "Items note administrative or bureaucratic overhead.",
        ["admin", "bureaucra", "paperwork", "slow process", "行政", "手续"],
    ),
]

_NEUTRAL_THEMES: list[tuple[str, list[str]]] = [
    (
        "Items reference an international or diverse membership.",
        ["international", "diverse", "国际", "多元"],
    ),
    (
        "Items mention the group's size or structure.",
        ["large group", "small group", "group size", "团队规模"],
    ),
    (
        "Items reference interdisciplinary or cross-department work.",
        ["interdisciplinary", "cross-", "跨学科"],
    ),
]


def _count_matches(texts: list[str], keywords: list[str]) -> int:
    count = 0
    for text in texts:
        lowered = text.lower()
        if any(re.search(re.escape(kw.lower()), lowered) for kw in keywords):
            count += 1
    return count


class HeuristicSummariser:
    """Deterministic, network-free summariser for demos, tests and dry runs."""

    name = "offline-heuristic"

    def summarise(self, group: LabGroup) -> LlmSummary:
        texts = group.texts()
        positive = [
            Theme(theme=name, description=desc, supporting_item_count=n)
            for name, desc, kws in _POSITIVE_THEMES
            if (n := _count_matches(texts, kws)) > 0
        ]
        challenges = [
            Theme(theme=name, description=desc, supporting_item_count=n)
            for name, desc, kws in _CHALLENGE_THEMES
            if (n := _count_matches(texts, kws)) > 0
        ]
        neutral = [
            desc for desc, kws in _NEUTRAL_THEMES if _count_matches(texts, kws) > 0
        ]

        items, authors = group.item_count, group.unique_author_count
        if items >= 12 and authors >= 6:
            confidence = "high"
        elif items >= 8 and authors >= 4:
            confidence = "medium"
        else:
            confidence = "low"

        overview = (
            f"Across {items} anonymised, user-reported items from {authors} distinct "
            f"authors, recurring perceptions cluster into "
            f"{len(positive)} positive theme(s) and {len(challenges)} challenge "
            f"theme(s). All statements are unverified impressions, not established facts."
        )
        limitations = [
            "Statements are self-selected and unverified.",
            "Volume is limited and may not represent the wider group.",
        ]
        if authors < 4:
            limitations.append("Perceptions are dominated by a small number of authors.")

        return LlmSummary(
            overview=overview,
            positive_themes=positive,
            challenge_themes=challenges,
            neutral_observations=neutral,
            confidence=confidence,
            limitations=limitations,
            withheld_item_count=group.withheld_count,
        )
