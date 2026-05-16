from __future__ import annotations

import json
from pathlib import Path

from acb_large_print import cli


def test_pdf_inspect_command_json_output(monkeypatch, tmp_path, capsys):
    sample = tmp_path / "sample.pdf"
    sample.write_bytes(b"%PDF-1.4\n% test\n")

    monkeypatch.setattr(
        cli,
        "inspect_pdf_form",
        lambda _path: {
            "file_path": str(sample),
            "classification": {
                "class": "acroform_supported",
                "round_trip_support": "yes",
                "supported": True,
                "reason": "ok",
            },
            "warnings": [],
            "fields": [],
            "summary": {"total_fields": 0, "field_type_counts": {}, "low_confidence_fields": 0},
        },
    )

    code = cli.main(["pdf-inspect", str(sample), "--format", "json"], force_cli=True)
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["classification"]["class"] == "acroform_supported"


def test_pdf_inspect_command_rejects_non_pdf(tmp_path):
    sample = tmp_path / "sample.txt"
    sample.write_text("not pdf", encoding="utf-8")
    code = cli.main(["pdf-inspect", str(sample)], force_cli=True)
    assert code == 1

