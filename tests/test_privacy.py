"""Privacy-leak tests — the build MUST NOT expose raw or identifying data."""

import json

from pipeline import privacy


def test_scan_flags_forbidden_keys():
    assert privacy.scan({"username": "bob"})
    assert privacy.scan({"author_id": "a1"})
    assert privacy.scan({"profile_url": "https://x/y"})
    assert privacy.scan({"text": "raw comment body"})
    assert privacy.scan({"author_hash": "deadbeef"})
    assert privacy.scan({"researcher_name": "Prof X"})
    assert privacy.scan({"campus_name_raw": "a uniquely identifying building description"})
    assert privacy.scan({"campus_assignment_method": "provided"})


def test_scan_flags_suspicious_url_values():
    assert privacy.scan({"link": "https://www.xiaohongshu.com/user/123"})
    assert privacy.scan({"link": "https://example.com/profile/abc"})


def test_scan_allows_clean_public_shape():
    clean = {
        "institution_id": "imperial",
        "name": "Imperial College London",
        "unique_author_count": 5,
        "source_item_count": 9,
        "website": "https://www.imperial.ac.uk",
        "labs": [{"lab_id": "x", "lab_name": "Y", "confidence": "medium"}],
    }
    assert privacy.scan(clean) == []


def test_scan_is_recursive():
    nested = {"labs": [{"provenance": {"author_id": "leak"}}]}
    findings = privacy.scan(nested)
    assert findings and "author_id" in findings[0].detail


# --- the end-to-end guarantee -------------------------------------------------
FORBIDDEN_KEY_SUBSTRINGS = ["username", "author_id", "profile_url", "source_url"]
# fictional identifiers / withheld content that exist in the synthetic input
LEAKY_VALUES = [
    "auth-imp", "auth-ucl", "Group Lead", "example.invalid",
    "harassment", "idiot", "造假", "diagnosed with depression",
]


def test_public_build_has_no_privacy_leaks(exported):
    paths, _ = exported
    for path in paths.values():
        data = json.loads(path.read_text(encoding="utf-8"))
        findings = privacy.scan(data)
        assert findings == [], f"{path.name} leaked: {findings}"


def test_public_build_contains_no_raw_identifiers_or_withheld_text(exported):
    paths, _ = exported
    blob = "".join(p.read_text(encoding="utf-8") for p in paths.values())
    for needle in FORBIDDEN_KEY_SUBSTRINGS:
        assert needle not in blob, f"forbidden field name present: {needle}"
    for needle in LEAKY_VALUES:
        assert needle not in blob, f"raw/withheld value leaked: {needle}"
