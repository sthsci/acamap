"""Automated moderation pass (runs BEFORE summarisation).

A conservative first filter that routes potentially harmful content to a
PRIVATE, git-ignored queue for human review and keeps it out of the model
input and the public build. It errs toward withholding. Categories excluded:

  * serious allegations / accusations of misconduct
  * identifying medical information
  * personally targeted insults

This is heuristic and bilingual (English + Chinese). It is a safety net, not a
substitute for the human review of ``data/moderation/moderation_queue.json``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .config import Settings, get_settings
from .models import AnonymisedItem, ModerationRecord

# Each pattern is compiled case-insensitively. Chinese terms need no word
# boundaries; English terms use them to avoid over-matching substrings.
_CATEGORY_TERMS: dict[str, list[str]] = {
    "serious_allegation": [
        r"\bharass(?:ed|ment|ing)?\b",
        r"\bassault(?:ed|ing)?\b",
        r"\babuse(?:d|s|ive)?\b",
        r"\bbull(?:y|ied|ies|ying)\b",
        r"\bdiscriminat(?:e|ed|ion|ory)\b",
        r"\bracis(?:t|m)\b",
        r"\bsexis(?:t|m)\b",
        r"\bmisconduct\b",
        r"\bfraud(?:ulent)?\b",
        r"\bplagiaris(?:e|ed|m)\b",
        r"\bfalsif(?:y|ied|ication)\b",
        r"\bfabricat(?:e|ed|ion)\b",
        r"\bretaliat(?:e|ed|ion|ory)\b",
        r"\bpredator(?:y)?\b",
        r"\bsexual(?:ly)?\b",
        r"\bstole\b",
        r"\bstealing\b",
        "性骚扰", "骚扰", "霸凌", "欺凌", "歧视", "造假", "抄袭",
        "剽窃", "学术不端", "虐待", "报复", "性侵", "诈骗",
    ],
    "medical_identifying": [
        r"\bsuicid(?:e|al)\b",
        r"\bself[-\s]?harm\b",
        r"\bdiagnos(?:e|ed|is)\b",
        r"\bdepression\b",
        r"\bbipolar\b",
        r"\bpsychiatric\b",
        r"\bhospitalis?(?:e|ed|ation)\b",
        r"\bmedication\b",
        r"\bantidepressant(?:s)?\b",
        r"\bbreakdown\b",
        "自杀", "自残", "抑郁症", "确诊", "精神病", "住院", "服药", "崩溃",
    ],
    "targeted_insult": [
        r"\bidiot(?:s)?\b",
        r"\bstupid\b",
        r"\bmoron(?:s)?\b",
        r"\bincompetent\b",
        r"\buseless\b",
        r"\bscum\b",
        r"\basshole(?:s)?\b",
        r"\bbastard(?:s)?\b",
        r"\bshit(?:ty)?\b",
        r"\bfuck(?:ing|ed)?\b",
        "傻逼", "白痴", "废物", "垃圾", "蠢货", "无能", "混蛋", "贱",
    ],
}

_COMPILED: dict[str, list[re.Pattern[str]]] = {
    category: [re.compile(term, re.IGNORECASE) for term in terms]
    for category, terms in _CATEGORY_TERMS.items()
}


def classify(text: str) -> list[str]:
    """Return the list of moderation categories ``text`` triggers (may be empty)."""
    reasons: list[str] = []
    for category, patterns in _COMPILED.items():
        if any(p.search(text) for p in patterns):
            reasons.append(category)
    return reasons


def moderate(
    items: list[AnonymisedItem],
) -> tuple[list[AnonymisedItem], list[ModerationRecord]]:
    """Split ``items`` into (kept, withheld). Withheld items get a record."""
    kept: list[AnonymisedItem] = []
    withheld: list[ModerationRecord] = []
    for item in items:
        reasons = classify(item.text)
        if reasons:
            withheld.append(
                ModerationRecord(
                    item_id=item.item_id,
                    institution_id=item.institution_id,
                    department=item.department,
                    lab_name=item.lab_name,
                    campus_id=item.campus_id,
                    reasons=reasons,
                    text=item.text,
                    posted_at=item.posted_at,
                )
            )
        else:
            kept.append(item)
    return kept, withheld


def write_queue(records: list[ModerationRecord], settings: Settings | None = None) -> Path:
    """Persist the withheld records to the PRIVATE moderation queue."""
    settings = settings or get_settings()
    settings.moderation_dir.mkdir(parents=True, exist_ok=True)
    out = settings.moderation_queue_file
    payload = [r.model_dump(mode="json") for r in records]
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
