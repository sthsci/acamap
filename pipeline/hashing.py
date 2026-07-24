"""Deterministic, salted pseudonymisation of identifiers.

Post, comment and author identifiers are hashed with an HMAC keyed by a local
secret salt. The mapping is stable within a salt (so the same author is
recognisable across engagement snapshots for entity resolution) but the salt
never leaves the local machine, so hashes cannot be reversed from the public
build.
"""

from __future__ import annotations

import hashlib
import hmac


def hash_id(value: str | None, salt: str) -> str | None:
    """Return a stable, non-reversible 16-hex-char pseudonym for ``value``.

    ``None`` and empty strings map to ``None`` so absent identifiers stay absent.
    """
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    digest = hmac.new(salt.encode("utf-8"), value.encode("utf-8"), hashlib.sha256)
    return digest.hexdigest()[:16]


def content_hash(*parts: str) -> str:
    """Stable content hash used for caching LLM summaries.

    Not salted: it identifies *content*, not a person, and must match across
    machines so a shared cache can be reasoned about.
    """
    joined = "␟".join(parts)  # unit-separator glyph, unlikely to collide
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()
