import unittest
import numpy as np
import pandas as pd
from operations_efficiency_dashboard import generate_data, summarize

class DashboardTests(unittest.TestCase):
    def test_repeatability(self):
        pd.testing.assert_frame_equal(generate_data(),generate_data())
    def test_metric_units(self):
        df=pd.DataFrame({"Date":["2025-01-01"],"Machine":["A"],"Operations":[200],"DelayMinutes":[20]})
        self.assertEqual(summarize(df).iloc[0]["delay_minutes_per_100_operations"],10)
    def test_invalid_data(self):
        df=generate_data(days=1); df.loc[0,"Operations"]=0
        with self.assertRaises(ValueError): summarize(df)

    def test_missing_required_values_are_rejected(self):
        for column in ("Date", "Machine", "Operations", "DelayMinutes"):
            with self.subTest(column=column):
                df = generate_data(days=1)
                df[column] = df[column].astype(object)
                df.loc[0, column] = None
                with self.assertRaises(ValueError):
                    summarize(df)

    def test_nonfinite_metrics_are_rejected(self):
        for column in ("Operations", "DelayMinutes"):
            for value in (np.nan, np.inf, -np.inf, "inf", ""):
                with self.subTest(column=column, value=value):
                    df = generate_data(days=1)
                    df[column] = df[column].astype(object)
                    df.loc[0, column] = value
                    with self.assertRaises(ValueError):
                        summarize(df)

    def test_blank_machine_is_rejected(self):
        for value in ("", "  ", "\t"):
            with self.subTest(value=value):
                df = generate_data(days=1)
                df.loc[0, "Machine"] = value
                with self.assertRaises(ValueError):
                    summarize(df)

    def test_missing_date_strings_are_rejected(self):
        for value in ("", "NaT"):
            with self.subTest(value=value):
                df = generate_data(days=1)
                df["Date"] = df["Date"].astype(object)
                df.loc[0, "Date"] = value
                with self.assertRaises(ValueError):
                    summarize(df)

    def test_numeric_strings_and_zero_delay_are_valid(self):
        df = pd.DataFrame({"Date": ["2025-01-01"], "Machine": ["A"],
                           "Operations": ["200"], "DelayMinutes": ["0"]})
        original = df.copy(deep=True)
        result = summarize(df)
        self.assertEqual(result.iloc[0]["delay_minutes_per_100_operations"], 0)
        pd.testing.assert_frame_equal(df, original)

if __name__=="__main__": unittest.main()
