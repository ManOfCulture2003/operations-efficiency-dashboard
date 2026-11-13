"""Regression tests for CSV import limits and missing source files."""

import pytest

from operations_efficiency_dashboard import MAX_CSV_BYTES, build_report


@pytest.mark.parametrize("size", [MAX_CSV_BYTES + 1, MAX_CSV_BYTES + 4096])
def test_over_limit_csv_never_creates_output(tmp_path, size):
    source = tmp_path / "large.csv"
    with source.open("wb") as stream:
        stream.write(b"Date,Machine,Operations,DelayedOperations,DelayMinutes\\n")
        stream.truncate(size)
    destination = tmp_path / "report"
    with pytest.raises(ValueError, match="file-size limit"):
        build_report(input_path=source, output_dir=destination)
    assert not destination.exists()


def test_missing_csv_never_creates_output(tmp_path):
    destination = tmp_path / "report"
    with pytest.raises(FileNotFoundError):
        build_report(input_path=tmp_path / "missing.csv", output_dir=destination)
    assert not destination.exists()
