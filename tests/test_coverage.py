import pandas as pd
from operations_efficiency_dashboard import build_report, filter_dates, summarize, validate_data


def records():
    return pd.DataFrame([
        ['2026-01-01', 'A', 100, 10, 20],
        ['2026-01-03', 'A', 100, 10, 20],
        ['2026-01-03', 'B', 100, 0, 0],
    ], columns=['Date', 'Machine', 'Operations', 'DelayedOperations', 'DelayMinutes'])


def test_coverage_does_not_fill_missing_days_with_zeroes():
    result = summarize(validate_data(records())).set_index('Machine')
    assert result.loc['A', 'RecordedDays'] == 2
    assert result.loc['B', 'RecordedDays'] == 1
    assert result['CalendarDays'].tolist() == [3, 3]
    assert result['UnrecordedDays'].tolist() == [1, 2]
    assert result.loc['A', 'Operations'] == 200
    assert result.loc['A', 'DelayIncidencePct'] == 10


def test_coverage_tracks_filtered_data():
    selected = filter_dates(validate_data(records()), start='2026-01-03')
    result = summarize(selected)
    assert result['RecordedDays'].tolist() == [1, 1]
    assert result['UnrecordedDays'].tolist() == [0, 0]


def test_csv_and_html_expose_coverage(tmp_path):
    source = tmp_path / 'source.csv'
    records().to_csv(source, index=False)
    paths = build_report(input_path=source, output_dir=tmp_path / 'out')
    exported = pd.read_csv(paths['machine_kpis.csv'])
    assert exported['UnrecordedDays'].tolist() == [1, 2]
    html = paths['report.html'].read_text(encoding='utf-8')
    assert 'Recorded days' in html
    assert 'Unrecorded days' in html
    assert 'not proof of downtime' in html
