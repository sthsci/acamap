import json
from argparse import Namespace
from pathlib import Path

from pipeline.cli import cmd_import_last30days
from pipeline.last30days_import import build_last30days_import


def _report(
    *,
    author_id: str | None = "author-1",
    date: str | None = "2026-07-20",
    count: int = 1,
):
    return {
        "topic": "Imperial Adaptive Systems Lab 博士体验",
        "range": {"from": "2026-07-01", "to": "2026-07-30"},
        "generated_at": "2026-07-30T10:00:00+00:00",
        "mode": "deep",
        "xiaohongshu": [
            {
                "id": f"XHS-{index:03d}",
                "title": f"A public workplace impression {index}",
                "desc": "Supportive collaboration and clear communication.",
                "url": f"https://www.xiaohongshu.com/explore/example-{index}",
                "author_name": "display-name-is-not-used",
                "author_id": (
                    f"{author_id}-{(index - 1) % 3}" if count > 1 and author_id else author_id
                ),
                "date": date,
                "date_confidence": "high",
                "engagement": {"likes": 12, "num_comments": 3},
            }
            for index in range(1, count + 1)
        ],
    }


def _write_manifest(tmp_path: Path, report: dict) -> Path:
    report_path = tmp_path / "export.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    manifest = {
        "version": 1,
        "exports": [
            {
                "input": "export.json",
                "lab_id": "imperial-adaptive-systems",
                "campus_id": "imperial-south-kensington",
                "expected_topic": "Imperial Adaptive Systems Lab 博士体验",
                "selected_item_ids": [item["id"] for item in report["xiaohongshu"]],
            }
        ],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def test_build_last30days_import_requires_human_mapping_and_complete_evidence(
    tmp_path, settings
):
    manifest = _write_manifest(tmp_path, _report())

    records, audit = build_last30days_import(manifest, settings)

    assert audit.ready
    assert audit.ready_items == 1
    assert records[0].institution_id == "imperial"
    assert records[0].lab_name == "Adaptive Systems Lab"
    assert records[0].author_id == "author-1"
    assert records[0].source_url


def test_build_last30days_import_rejects_missing_author_and_date(tmp_path, settings):
    manifest = _write_manifest(tmp_path, _report(author_id=None, date=None))

    records, audit = build_last30days_import(manifest, settings)

    assert records == []
    assert not audit.ready
    assert audit.issue_counts["missing_author_id"] == 1
    assert audit.issue_counts["missing_posted_at"] == 1
    assert audit.issue_counts["no_ready_items"] == 1


def test_import_last30days_audit_only_writes_nothing(
    tmp_path, settings, monkeypatch, capsys
):
    manifest = _write_manifest(tmp_path, _report())
    monkeypatch.setattr("pipeline.cli.get_settings", lambda: settings)
    output = settings.raw_dir / "normalised.json"
    args = Namespace(
        manifest=str(manifest),
        output=str(output),
        audit_only=True,
        confirm_lawful=False,
        run_pipeline=False,
        offline=True,
        model=None,
        force=False,
    )

    assert cmd_import_last30days(args) == 0
    assert "audit passed; nothing written" in capsys.readouterr().out
    assert not output.exists()


def test_import_last30days_runs_private_pipeline_and_labels_real_aggregates(
    tmp_path, settings, monkeypatch
):
    manifest = _write_manifest(tmp_path, _report(count=5))
    monkeypatch.setattr("pipeline.cli.get_settings", lambda: settings)
    output = settings.raw_dir / "normalised.json"
    args = Namespace(
        manifest=str(manifest),
        output=str(output),
        audit_only=False,
        confirm_lawful=True,
        run_pipeline=True,
        offline=True,
        model=None,
        force=False,
    )

    assert cmd_import_last30days(args) == 0
    assert output.exists()
    assert settings.anonymised_file.exists()
    meta = json.loads(
        (settings.web_public_dir / "meta.json").read_text(encoding="utf-8")
    )
    assert meta["dataset_kind"] == "lawfully_imported"
    assert meta["published_lab_count"] == 1
