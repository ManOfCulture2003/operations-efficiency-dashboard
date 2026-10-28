import unittest
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

if __name__=="__main__": unittest.main()
