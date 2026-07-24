"""Command-line interface: ingest, moderate, summarize, export, review."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import get_settings
from .export import export as run_export
from .ingest import ingest_file, load_processed, write_processed
from .llm import HeuristicSummariser, OllamaSummariser, OllamaUnavailableError, Summariser
from .moderation import moderate, write_queue
from .summarize import run_summarise


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate private input without writing processed or public artefacts."""
    settings = get_settings()
    total = 0
    for raw_path in args.input:
        path = Path(raw_path)
        if not path.exists():
            print(f"error: input not found: {path}", file=sys.stderr)
            return 2
        try:
            batch = ingest_file(path, settings)
        except (OSError, ValueError) as exc:
            print(f"error: {path}: {exc}", file=sys.stderr)
            return 2
        total += len(batch)
        print(f"valid: {path} ({len(batch)} unique item(s))")
    print(f"→ {total} unique item(s) validated; nothing written")
    return 0


def _build_summariser(args: argparse.Namespace) -> Summariser:
    settings = get_settings()
    if getattr(args, "offline", False):
        return HeuristicSummariser()
    model = getattr(args, "model", None) or settings.model
    return OllamaSummariser(
        host=settings.ollama_host,
        model=model,
        temperature=settings.temperature,
        seed=settings.seed,
        timeout=settings.request_timeout,
        max_retries=settings.max_retries,
    )


def cmd_ingest(args: argparse.Namespace) -> int:
    settings = get_settings()
    settings.ensure_dirs()
    items = []
    seen_ids: set[str] = set()
    for raw_path in args.input:
        path = Path(raw_path)
        if not path.exists():
            print(f"error: input not found: {path}", file=sys.stderr)
            return 2
        batch = ingest_file(path, settings)
        # merge across files by item_id (later engagement snapshots may repeat)
        for item in batch:
            if item.item_id in seen_ids:
                continue
            seen_ids.add(item.item_id)
            items.append(item)
        print(f"ingested {len(batch):>4} item(s) from {path}")
    out = write_processed(items, settings)
    print(f"→ {len(items)} anonymised item(s) written to {out}")
    return 0


def cmd_moderate(args: argparse.Namespace) -> int:
    settings = get_settings()
    items = load_processed(settings)
    kept, withheld = moderate(items)
    out = write_queue(withheld, settings)
    print(f"kept {len(kept)} item(s); withheld {len(withheld)} to private queue → {out}")
    return 0


def cmd_summarize(args: argparse.Namespace) -> int:
    settings = get_settings()
    settings.ensure_dirs()
    summariser = _build_summariser(args)
    try:
        result = run_summarise(
            summariser, settings, force=args.force, dry_run=args.dry_run
        )
    except OllamaUnavailableError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3

    published = [p for p in result.plans if p.publishable]
    insufficient = [p for p in result.plans if not p.publishable]
    print(f"summariser: {summariser.name}")
    print(f"withheld to moderation queue: {len(result.withheld)} item(s)")
    print(f"labs meeting threshold: {len(published)}")
    print(f"labs below threshold:   {len(insufficient)}")
    if args.dry_run:
        print("\n-- dry run (no model calls, nothing written) --")
        for plan in sorted(result.plans, key=lambda p: (not p.publishable, p.institution_id)):
            status = "PUBLISH" if plan.publishable else "hold   "
            cached = " [cached]" if plan.cached else ""
            print(
                f"  {status} {plan.institution_id} / {plan.department} / {plan.lab_name}"
                f" — {plan.item_count} items, {plan.unique_author_count} authors,"
                f" {plan.withheld_count} withheld{cached}"
            )
    else:
        print("→ dataset written to data/processed/public_dataset.json")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    settings = get_settings()
    settings.ensure_dirs()
    paths = run_export(settings)
    for name, path in paths.items():
        print(f"→ {name}: {path}")
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    settings = get_settings()
    path = settings.moderation_queue_file
    if not path.exists():
        print(f"No moderation queue at {path}. Run `labvibes summarize` first.")
        return 0
    import json

    records = json.loads(path.read_text(encoding="utf-8"))
    print(f"Private moderation queue: {len(records)} withheld item(s) — LOCAL ONLY\n")
    from collections import Counter

    reasons = Counter(r for rec in records for r in rec["reasons"])
    for reason, count in reasons.most_common():
        print(f"  {count:>4}  {reason}")
    if args.full:
        print("\n-- items (local review only; never publish) --")
        for rec in records:
            print(f"\n[{rec['item_id']}] {rec['institution_id']} / {rec.get('lab_name')}")
            print(f"  reasons: {', '.join(rec['reasons'])}")
            print(f"  text: {rec['text']}")
    else:
        print("\nRun with --full to print withheld text for local human review.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="labvibes",
        description="Lab Vibes London — local processing & summarisation pipeline.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser(
        "validate", help="validate private input without writing artefacts"
    )
    p_validate.add_argument(
        "--input", nargs="+", required=True, help="one or more CSV/JSON files"
    )
    p_validate.set_defaults(func=cmd_validate)

    p_ingest = sub.add_parser("ingest", help="import raw posts and anonymise them")
    p_ingest.add_argument(
        "--input", nargs="+", required=True, help="one or more CSV/JSON files"
    )
    p_ingest.set_defaults(func=cmd_ingest)

    p_mod = sub.add_parser("moderate", help="run the moderation pass only")
    p_mod.set_defaults(func=cmd_moderate)

    p_sum = sub.add_parser("summarize", help="moderate, aggregate and summarise")
    p_sum.add_argument("--force", action="store_true", help="ignore the summary cache")
    p_sum.add_argument("--dry-run", action="store_true", help="plan only; no model calls")
    p_sum.add_argument("--offline", action="store_true", help="use the offline heuristic")
    p_sum.add_argument("--model", help="override the Ollama model for this run")
    p_sum.set_defaults(func=cmd_summarize)

    p_exp = sub.add_parser("export", help="write sanitised JSON to web/public/data")
    p_exp.set_defaults(func=cmd_export)

    p_rev = sub.add_parser("review", help="inspect the private moderation queue")
    p_rev.add_argument("--full", action="store_true", help="print withheld text (local)")
    p_rev.set_defaults(func=cmd_review)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
