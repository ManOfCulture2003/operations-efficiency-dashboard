from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

from operations_efficiency_dashboard import build_report, filter_dates, generate_data, summarize, validate_data


def fixture_rows():
    return pd.DataFrame([
        {"Date": "2026-01-01", "Machine": "Machine_A", "Operations": 100, "DelayedOperations": 10, "DelayMinutes": 50},
        {"Date": "2026-01-02", "Machine": "Machine_A", "Operations": 300, "DelayedOperations": 0, "DelayMinutes": 0},
        {"Date": "2026-01-01", "Machine": "Machine_B", "Operations": 100, "DelayedOperations": 20, "DelayMinutes": 100},
    ])


def test_generation_is_deterministic_and_synthetic():
    assert generate_data(seed=7, days=3).equals(generate_data(seed=7, days=3))
    assert not generate_data(seed=7, days=3).equals(generate_data(seed=8, days=3))
    assert len(validate_data(generate_data(days=3))) == 9


def test_weighted_incidence_not_mean_of_daily_percentages():
    summary = summarize(validate_data(fixture_rows())).set_index("Machine")
    assert summary.loc["Machine_A", "Operations"] == 400
    assert summary.loc["Machine_A", "DelayIncidencePct"] == 2.5
    assert summary.loc["Machine_A", "DelayMinutesPerOperation"] == 0.125
    assert summary.loc["Machine_A", "MinutesPerDelayedOperation"] == 5.0
    assert summary.loc["Machine_B", "DelayIncidencePct"] == 20.0


def test_zero_delays_has_no_fake_average():
    data = fixture_rows().iloc[[1]].copy()
    summary = summarize(validate_data(data))
    assert pd.isna(summary.loc[0, "MinutesPerDelayedOperation"])
    assert summary.loc[0, "DelayIncidencePct"] == 0


@pytest.mark.parametrize('column', ['Operations', 'DelayedOperations', 'DelayMinutes'])
@pytest.mark.parametrize('mixed', [False, True])
def test_boolean_counts_rejected(column, mixed):
    data = fixture_rows().assign(Operations=10, DelayedOperations=1, DelayMinutes=1)
    data[column] = [True, 1, 1] if mixed else True
    with pytest.raises(ValueError, match=column):
        validate_data(data)


@pytest.mark.parametrize("mutator", [
    lambda d: d.drop(columns=["DelayedOperations"]),
    lambda d: d.assign(Machine="=SUM(1,1)"),
    lambda d: d.assign(Operations=0),
    lambda d: d.assign(Operations=2.5),
    lambda d: d.assign(DelayedOperations=101),
    lambda d: d.assign(DelayedOperations=0, DelayMinutes=5),
    lambda d: d.assign(Date="2026-02-30"),
    lambda d: pd.concat([d, d.iloc[[0]]], ignore_index=True),
    lambda d: d.assign(DelayMinutes=-1),
    lambda d: d.assign(DelayMinutes="nan"),
])
def test_invalid_inputs_fail_closed(mutator):
    with pytest.raises(ValueError):
        validate_data(mutator(fixture_rows()))


def test_date_filter_inclusive_and_empty_rejected():
    data = validate_data(fixture_rows())
    selected = filter_dates(data, start="2026-01-02", end="2026-01-02")
    assert len(selected) == 1
    with pytest.raises(ValueError, match="No records"):
        filter_dates(data, start="2027-01-01")
    with pytest.raises(ValueError, match="later"):
        filter_dates(data, start="2026-01-02", end="2026-01-01")


def test_local_report_contains_expected_files_and_truthful_label(tmp_path):
    paths = build_report(input_path=None, output_dir=tmp_path, days=2)
    assert len(paths) == 6
    assert all(path.exists() and path.stat().st_size > 100 for path in paths.values())
    html = paths["report.html"].read_text()
    assert "SYNTHETIC DEMONSTRATION DATA" in html
    assert "Delay incidence" in html
    assert len(pd.read_csv(paths["records.csv"])) == 6


def test_user_csv_and_date_filters(tmp_path):
    input_path = tmp_path / "input.csv"
    fixture_rows().to_csv(input_path, index=False)
    paths = build_report(input_path=input_path, output_dir=tmp_path / "out", start="2026-01-02")
    assert len(pd.read_csv(paths["records.csv"])) == 1
    assert "USER-SUPPLIED LOCAL DATA" in paths["report.html"].read_text()


def test_cli_smoke(tmp_path):
    script = Path(__file__).resolve().parents[1] / "operations_efficiency_dashboard.py"
    result = subprocess.run([sys.executable, str(script), "--days", "2", "--output-dir", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "report.html").exists()


@pytest.mark.parametrize("name", ["records.csv", "machine_kpis.csv", "daily_kpis.csv"])
def test_report_cannot_overwrite_source_csv(tmp_path, name):
    source = tmp_path / name
    fixture_rows().to_csv(source, index=False)
    original = source.read_bytes()
    with pytest.raises(ValueError, match="overwrite.*input"):
        build_report(input_path=source, output_dir=tmp_path, start="2026-01-02")
    assert source.read_bytes() == original
    assert sorted(path.name for path in tmp_path.iterdir()) == [name]
