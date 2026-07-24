# Data governance notice

This notice governs how data is collected, processed, stored and published in
the Lab Vibes London project. It is binding on anyone running the pipeline or
contributing to the repository. The software licence (see `LICENSE`) covers the
**code only** and grants no rights over any data.

## 1. Scope and purpose

The project aggregates **publicly posted** impressions of academic research
workplaces to surface recurring themes. It exists to give context, not verdicts.
It must never be used to target, rank, defame or identify individuals.

## 2. Lawful, import-first collection

- Data is **imported**, not scraped. Do not build or run anything that bypasses
  logins, CAPTCHAs, rate limits, anti-bot systems or any other access control.
- Only import material you are lawfully permitted to use, consistent with the
  source platform's terms and applicable law (including UK GDPR / Data
  Protection Act 2018 where personal data is involved).
- Prefer the least data necessary. Do not collect special-category data or
  attempt to infer protected characteristics.

## 3. Lawful basis, roles and rights

- If you process personal data, identify your lawful basis before collecting it
  and keep the private raw data and moderation queue strictly local.
- Treat authorship and affiliation as **unverifiable**. Do not attempt to
  re-identify pseudonymous authors.
- Support data-subject rights: because raw data stays local and unpublished, an
  erasure or objection request is honoured by deleting the relevant local raw
  records and re-running the export. Published output contains no identifiers to
  erase.

## 4. What is stored where

| Data | Location | Committed? |
| --- | --- | --- |
| Raw posts / comments | `data/raw/` | **Never** |
| Anonymised working items (contain text) | `data/processed/` | **Never** |
| Private moderation queue (withheld content) | `data/moderation/` | **Never** |
| Local LLM cache | `data/cache/` | **Never** |
| Environment / secrets | `.env` | **Never** |
| Institution catalogue | `data/institutions/` | Yes (public-safe) |
| Synthetic demo data | `data/samples/` | Yes (fictional) |
| Sanitised aggregates | `web/public/data/` | Yes (public-safe) |

`.gitignore` enforces the "Never" rows. Do not override it.

## 5. Processing safeguards (enforced in code, not just here)

- Post, comment and author identifiers are replaced with salted, non-reversible
  hashes; source URLs are discarded on import.
- Raw campus wording is retained only in the local processed artefact for
  assignment audit. It is treated as potentially identifying free text and is
  explicitly forbidden from public output.
- A moderation pass routes serious allegations, misconduct accusations,
  identifying medical information and personally targeted insults to the private
  queue **before** summarisation.
- A lab summary is published only with at least **5 items from 3 distinct
  authors**; otherwise the site shows an insufficient-data notice.
- The local LLM is instructed to treat all statements as unverified perceptions,
  to avoid identifying or accusing anyone, and to lower confidence when evidence
  is weak.
- The export step runs a privacy scan and refuses to write any forbidden field
  (usernames, author/profile identifiers, raw text, unredacted URLs). A test
  fails the build if such a field would ship.

## 6. Location data and ambiguity

An institution-wide point is insufficient for London universities with several
campuses, hospital sites and research buildings. The catalogue therefore
separates a display-only `map_center` from auditable physical campus records.
Official institutional pages verify names and relationships; coordinate
provenance is stored internally in the catalogue but omitted from public
summary JSON. The public interface uses **Locations** as the umbrella term,
shows **Campus** only for officially described campuses, and labels institutes
and other sites by their appropriate type. The internal `campus_id` schema is
retained for compatibility.

Campus assignment never defaults to a presumed main campus. A canonical id may
be provided, raw wording may match one catalogue entry, or a campus may be
inferred when—and only when—the relevant lab has exactly one known campus.
Every ambiguous item remains unassigned and is displayed as **Location
unspecified**. Such items may support a lab or institution summary, but are
excluded from location statistics and location-specific summaries.

Labs can be associated with several campuses. Institution totals deduplicate
labs, source items and authors across those associations. Location and
multi-location-lab summaries are generated only when the location-specific subset
independently reaches the same 5-item, 3-author threshold, so they can
legitimately differ from institution-wide summaries.

Oxford and Cambridge must later follow the same rule: record a display centre,
then verify each research-relevant campus or location and its provenance.
Collegiate or multi-site structures must not be represented as one physical
campus solely for interface convenience.

## 7. Local model boundary

Raw text is sent **only** to the local Ollama endpoint. It is never sent to a
cloud model, a CI runner or the browser. CI builds the site from committed
sanitised JSON only.

## 8. Publication and redress

- Summaries are presented as reported perceptions, never as verified facts, and
  never as rankings of individuals or "best/worst" lists.
- Maintainers may withhold any lab, raise thresholds, or remove items from the
  private queue at their discretion, especially on credible request from an
  affected party.

## 9. Retention

Keep raw and withheld data only as long as needed to regenerate summaries, then
delete it locally. There is no remote copy to retain.

---

By running the pipeline you accept responsibility for the lawfulness of the data
you import and for complying with this notice.
