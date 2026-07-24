# `data/raw/` — local only, never committed

Place **lawfully collected** public posts here as CSV or JSON matching the raw
input schema (see the project README, "Input-data format"). Everything in this
directory except this file and `.gitkeep` is git-ignored.

Rules:

- Only import data you are permitted to use. Do **not** bypass logins, CAPTCHAs,
  rate limits or any other access control to obtain it.
- Never commit raw posts, comments, usernames or source URLs.
- Treat `campus_name_raw` as private free text. Use a canonical `campus_id`
  where possible; unmatched or ambiguous wording must remain unspecified.
- The pipeline hashes identifiers and routes sensitive content to a private
  moderation queue before anything is aggregated or published.

To try the project immediately without any real data, use the synthetic sample:

```bash
uv run python -m pipeline ingest --input data/samples/synthetic_posts.csv
```
