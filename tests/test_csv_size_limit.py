"""Regression coverage for bounded user CSV imports."""
import pytest
from operations_efficiency_dashboard import build_report, MAX_CSV_BYTES


def test_oversized_csv_is_rejected_before_parsing(tmp_path):
    source = tmp_path / "huge.csv"
    with source.open("wb") as stream:
        stream.write(b"Date,Machine,Operations,DelayedOperations,DelayMinutes\n")
        stream.truncate(MAX_CSV_BYTES + 1)
    with pytest.raises(ValueError, match="file-size limit"):
        build_report(input_path=source, output_dir=tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_small_csv_still_generates_report(tmp_path):
    source = tmp_path / "input.csv"
    source.write_text("Date,Machine,Operations,DelayedOperations,DelayMinutes\n2026-01-01,A,10,1,3\n", encoding="utf-8")
    result = build_report(input_path=source, output_dir=tmp_path / "output")
    assert result["report.html"].exists()
