"""Privacy scanner: detect forbidden fields/values in would-be-public data.

Used both as a hard guard in the export step and by the privacy-leak tests.
It fails on:
  * forbidden KEYS (usernames, author/post/comment identifiers or hashes,
    profile/source URLs, raw text, engagement rows, timestamps of items, ...)
  * suspicious URL VALUES that look user-identifying (profile/user links).

Key matching is by a normalised form (lowercased, punctuation removed) compared
exactly against the forbidden set, so legitimate keys such as ``name``,
``institution_id`` or ``unique_author_count`` never trip it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Normalised (lowercase, alnum-only) forbidden key names.
FORBIDDEN_KEYS: frozenset[str] = frozenset(
    {
        "username", "userid", "user", "handle", "nickname",
        "authorid", "authorname", "authorhash", "author",
        "realname", "researchername", "email",
        "postid", "posthash", "commentid", "commenthash",
        "profileurl", "profile", "sourceurl", "avatar",
        "text", "rawtext", "body", "content", "comment", "comments",
        "postedat", "collectedat",
        "campusnameraw", "campusassignmentmethod", "campusassignmentconfidence",
    }
)

# Fragments that indicate a user-identifying URL rather than an org homepage.
_SUSPICIOUS_URL_FRAGMENTS = (
    "xiaohongshu", "xhslink", "rednote", "/user/", "/profile", "/u/", "@",
)
_URL_RE = re.compile(r"https?://", re.IGNORECASE)


@dataclass(frozen=True)
class Finding:
    path: str
    kind: str
    detail: str


def _normalise_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.lower())


def _is_suspicious_url(value: str) -> bool:
    if not _URL_RE.search(value):
        return False
    lowered = value.lower()
    return any(fragment in lowered for fragment in _SUSPICIOUS_URL_FRAGMENTS)


def scan(data: object, path: str = "$") -> list[Finding]:
    """Recursively scan ``data`` for privacy violations."""
    findings: list[Finding] = []

    if isinstance(data, dict):
        for key, value in data.items():
            here = f"{path}.{key}"
            if _normalise_key(str(key)) in FORBIDDEN_KEYS:
                findings.append(
                    Finding(here, "forbidden_key", f"forbidden field name '{key}'")
                )
            findings.extend(scan(value, here))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            findings.extend(scan(value, f"{path}[{index}]"))
    elif isinstance(data, str):
        if _is_suspicious_url(data):
            findings.append(
                Finding(path, "suspicious_url", "user-identifying URL in value")
            )

    return findings


def assert_clean(data: object) -> None:
    """Raise if ``data`` contains any privacy violation."""
    findings = scan(data)
    if findings:
        lines = "\n".join(f"  - {f.path}: {f.detail}" for f in findings)
        raise ValueError(f"Privacy violation(s) in public data:\n{lines}")
