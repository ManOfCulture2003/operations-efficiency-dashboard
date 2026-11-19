"""Ambiguous columns must not silently select one set of business totals."""
from unittest.mock import patch

import pytest

from operations_efficiency_dashboard import build_report


@pytest.mark.parametrize('column,value', [('Operations', '900'), ('Machine', 'Other'), ('Date', '2026-02-01')])
def test_duplicate_headers_fail_before_reporting(tmp_path, column, value):
    source = tmp_path / 'input.csv'
    source.write_text('Date,Machine,Operations,DelayedOperations,DelayMinutes,' + column + '\n'
                      '2026-01-01,Machine_A,100,10,50,' + value + '\n', encoding='utf-8-sig')
    with patch('operations_efficiency_dashboard.summarize') as summarize:
        with pytest.raises(ValueError, match='[Dd]uplicate'):
            build_report(input_path=source, output_dir=tmp_path / 'report')
        summarize.assert_not_called()
    assert not (tmp_path / 'report').exists()


def test_quoted_unique_headers_and_extra_column_still_work(tmp_path):
    source = tmp_path / 'input.csv'
    source.write_text('\n"Date","Machine","Operations","DelayedOperations","DelayMinutes","Notes"\n'
                      '2026-01-01,Machine_A,100,10,50,"example, with comma"\n', encoding='utf-8-sig')
    paths = build_report(input_path=source, output_dir=tmp_path / 'report')
    assert paths['report.html'].is_file()
