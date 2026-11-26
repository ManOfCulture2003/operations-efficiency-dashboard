import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import operations_efficiency_dashboard as app


class SnapshotTests(unittest.TestCase):
    def test_malformed_rows_are_rejected(self):
        for text in ['A,B\n1,2,3\n', 'A,B\n1\n', 'A,B\n"unfinished,2\n', 'A,A\n1,2\n']:
            with self.subTest(text=text), tempfile.TemporaryDirectory() as folder:
                source = Path(folder) / 'input.csv'
                source.write_text(text)
                with self.assertRaises(ValueError):
                    app.read_csv_snapshot(source)

    def test_parser_uses_snapshot_even_if_source_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'input.csv'
            source.write_text('Date,Machine,Operations,DelayedOperations,DelayMinutes,Notes\n2026-01-01,NA,10,1,2,"hello, world"\n', encoding='utf-8-sig')
            real_read = app.pd.read_csv
            def changed_source(buffer, **kwargs):
                source.write_text('invalid replacement')
                return real_read(buffer, **kwargs)
            with patch.object(app.pd, 'read_csv', side_effect=changed_source):
                result = app.read_csv_snapshot(source)
            self.assertEqual(result.loc[0, 'Machine'], 'NA')
            self.assertEqual(result.loc[0, 'Notes'], 'hello, world')


if __name__ == '__main__':
    unittest.main()
