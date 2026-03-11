import unittest
from unittest.mock import patch

import pandas as pd

from app import calculate_period_summary, fetch_stock_data, normalize_prices_for_chart


class TestApp(unittest.TestCase):
    @patch("app.fdr.DataReader")
    def test_fetch_stock_data(self, mock_reader):
        mock_df = pd.DataFrame(
            {"Close": [100, 110]},
            index=pd.to_datetime(["2025-12-30", "2026-01-02"]),
        )
        mock_reader.return_value = mock_df

        target_stocks = {"005930": "삼성전자"}
        result = fetch_stock_data(target_stocks, pd.Timestamp("2026-01-01").date())

        self.assertIn("삼성전자", result.columns)
        self.assertEqual(len(result), 2)
        self.assertEqual(result.iloc[0]["삼성전자"], 100)

    def test_calculate_period_summary_uses_first_valid_date_per_symbol(self):
        dates = pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"])
        prices_df = pd.DataFrame(
            {
                "기존 ETF": [100, 101, 102, 103],
                "신규 ETF": [None, None, 50, 55],
            },
            index=dates,
        )

        summary = calculate_period_summary(
            prices_df, pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-04")
        )
        summary_by_name = {item["name"]: item for item in summary}

        self.assertEqual(summary_by_name["기존 ETF"]["base_date"], "2026-01-01")
        self.assertAlmostEqual(summary_by_name["기존 ETF"]["return"], 3.0)
        self.assertEqual(summary_by_name["신규 ETF"]["base_date"], "2026-01-03")
        self.assertEqual(summary_by_name["신규 ETF"]["date"], "2026-01-04")
        self.assertAlmostEqual(summary_by_name["신규 ETF"]["start_price"], 50.0)
        self.assertAlmostEqual(summary_by_name["신규 ETF"]["current_price"], 55.0)
        self.assertAlmostEqual(summary_by_name["신규 ETF"]["return"], 10.0)
        self.assertTrue(summary_by_name["신규 ETF"]["is_delayed_start"])

    def test_calculate_period_summary_skips_all_nan_symbols(self):
        dates = pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"])
        prices_df = pd.DataFrame(
            {
                "정상 종목": [10, 11, 12],
                "빈 종목": [None, None, None],
            },
            index=dates,
        )

        summary = calculate_period_summary(
            prices_df, pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-03")
        )

        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["name"], "정상 종목")

    def test_normalize_prices_for_chart_preserves_leading_nan(self):
        dates = pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"])
        prices_df = pd.DataFrame(
            {
                "기존 ETF": [100, 110, 120, 130],
                "신규 ETF": [None, None, 50, 55],
            },
            index=dates,
        )

        norm_df = normalize_prices_for_chart(
            prices_df,
            ["기존 ETF", "신규 ETF"],
            pd.Timestamp("2026-01-01"),
            pd.Timestamp("2026-01-04"),
        )

        self.assertAlmostEqual(norm_df.loc[pd.Timestamp("2026-01-01"), "기존 ETF"], 100.0)
        self.assertTrue(pd.isna(norm_df.loc[pd.Timestamp("2026-01-01"), "신규 ETF"]))
        self.assertTrue(pd.isna(norm_df.loc[pd.Timestamp("2026-01-02"), "신규 ETF"]))
        self.assertAlmostEqual(norm_df.loc[pd.Timestamp("2026-01-03"), "신규 ETF"], 100.0)
        self.assertAlmostEqual(norm_df.loc[pd.Timestamp("2026-01-04"), "신규 ETF"], 110.0)

    def test_calculate_period_summary_uses_last_valid_date_within_period(self):
        dates = pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"])
        prices_df = pd.DataFrame(
            {
                "ETF": [100, 110, None, None],
            },
            index=dates,
        )

        summary = calculate_period_summary(
            prices_df, pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-04")
        )

        self.assertEqual(summary[0]["date"], "2026-01-02")
        self.assertAlmostEqual(summary[0]["current_price"], 110.0)
        self.assertAlmostEqual(summary[0]["return"], 10.0)


if __name__ == "__main__":
    unittest.main()
