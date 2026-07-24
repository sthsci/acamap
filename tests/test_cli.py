from argparse import Namespace

from pipeline.cli import cmd_validate


def test_validate_checks_input_without_writing(settings, monkeypatch, capsys):
    sample = settings.data_dir / "private.csv"
    sample.write_text("placeholder", encoding="utf-8")
    monkeypatch.setattr("pipeline.cli.get_settings", lambda: settings)
    monkeypatch.setattr("pipeline.cli.ingest_file", lambda path, config: [object(), object()])

    assert cmd_validate(Namespace(input=[str(sample)])) == 0
    assert "2 unique item(s) validated; nothing written" in capsys.readouterr().out
    assert not settings.anonymised_file.exists()
