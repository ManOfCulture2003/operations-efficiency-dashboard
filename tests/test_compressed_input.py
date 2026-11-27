import gzip
from unittest.mock import patch

import pytest
import operations_efficiency_dashboard as app


def test_compressed_csv_does_not_bypass_byte_limit(tmp_path):
    source = tmp_path / 'input.csv.gz'
    source.write_bytes(gzip.compress(app.generate_data(days=1).to_csv(index=False).encode()))
    with patch.object(app, 'MAX_CSV_BYTES', source.stat().st_size), patch.object(app, 'summarize') as summarize:
        with pytest.raises(ValueError, match='plain.*CSV'):
            app.build_report(input_path=source, output_dir=tmp_path / 'out')
    summarize.assert_not_called()
    assert not (tmp_path / 'out').exists()


def test_plain_csv_exactly_at_limit_is_accepted(tmp_path):
    source = tmp_path / 'input.csv'
    app.generate_data(days=1).to_csv(source, index=False)
    with patch.object(app, 'MAX_CSV_BYTES', source.stat().st_size):
        paths = app.build_report(input_path=source, output_dir=tmp_path / 'out')
    assert paths['report.html'].is_file()


def test_growing_file_cannot_bypass_stat_check(tmp_path):
    source = tmp_path / 'input.csv'
    source.write_bytes(b'x' * 101)
    with patch.object(app, 'MAX_CSV_BYTES', 100), patch.object(app.Path, 'stat') as stat:
        stat.return_value.st_size = 50
        with pytest.raises(ValueError, match='limit'):
            app.build_report(input_path=source, output_dir=tmp_path / 'out')
