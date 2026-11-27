from unittest.mock import patch
import pytest
import operations_efficiency_dashboard as app


@pytest.mark.parametrize('old,new', [('Machine_A','Machine_A\x00Other'), ('100,10','100\x00999,10'), ('Operations,','Operations\x00extra,')])
def test_null_bytes_cannot_silently_change_names_or_counts(tmp_path, old, new):
    source = tmp_path / 'source.csv'
    text = 'Date,Machine,Operations,DelayedOperations,DelayMinutes\n2026-01-01,Machine_A,100,10,50\n'
    source.write_bytes(text.replace(old,new).encode())
    with patch.object(app, 'summarize') as summarize:
        with pytest.raises(ValueError, match='null byte'):
            app.build_report(input_path=source, output_dir=tmp_path / 'out')
    summarize.assert_not_called()
    assert not (tmp_path / 'out').exists()
