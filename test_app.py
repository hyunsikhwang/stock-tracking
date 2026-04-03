import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd

from app import (
    build_pyecharts_html,
    build_chart,
    build_portfolio_chart,
    calculate_portfolio_weights,
    TargetConfigError,
    calculate_period_summary,
    fetch_stock_data,
    load_target_records,
    normalize_prices_for_chart,
)


class TestApp(unittest.TestCase):
    @patch("app.fdr.DataReader")
    def test_fetch_stock_data(self, mock_reader):
        mock_df = pd.DataFrame(
            {"Close": [100, 110]},
            index=pd.to_datetime(["2025-12-30", "2026-01-02"]),
        )
        mock_reader.return_value = mock_df

        target_stocks = [{"code": "005930", "name": "삼성전자", "quantity": 1}]
        result = fetch_stock_data(
            "KR Stocks",
            target_stocks,
            pd.Timestamp("2026-01-01").date(),
        )

        self.assertIn("삼성전자", result.columns)
        self.assertEqual(len(result), 2)
        self.assertEqual(result.iloc[0]["삼성전자"], 100)

    @patch("app.as_completed")
    @patch("app.fdr.DataReader")
    def test_fetch_stock_data_preserves_union_of_dates_regardless_of_completion_order(
        self, mock_reader, mock_as_completed
    ):
        def reader_side_effect(code, fetch_start):
            data_map = {
                "EARLY": pd.DataFrame(
                    {"Close": [100, 110, 120]},
                    index=pd.to_datetime(["2026-03-07", "2026-03-08", "2026-03-10"]),
                ),
                "LATE": pd.DataFrame(
                    {"Close": [50, 55]},
                    index=pd.to_datetime(["2026-03-10", "2026-03-11"]),
                ),
            }
            return data_map[code]

        def reversed_completion_order(futures):
            return list(futures.keys())[::-1]

        mock_reader.side_effect = reader_side_effect
        mock_as_completed.side_effect = reversed_completion_order

        result = fetch_stock_data(
            "ETFs",
            [
                {"code": "EARLY", "name": "선행 ETF", "quantity": 1},
                {"code": "LATE", "name": "후행 ETF", "quantity": 1},
            ],
            pd.Timestamp("2026-03-07").date(),
        )

        self.assertEqual(
            result.index.tolist(),
            pd.to_datetime(["2026-03-07", "2026-03-08", "2026-03-10", "2026-03-11"]).tolist(),
        )
        self.assertAlmostEqual(result.loc[pd.Timestamp("2026-03-07"), "선행 ETF"], 100.0)
        self.assertTrue(pd.isna(result.loc[pd.Timestamp("2026-03-07"), "후행 ETF"]))
        self.assertAlmostEqual(result.loc[pd.Timestamp("2026-03-10"), "후행 ETF"], 50.0)

    def test_load_target_records_supports_default_quantity_and_comments(self):
        with TemporaryDirectory() as tmp_dir:
            target_file = Path(tmp_dir) / "targets.txt"
            target_file.write_text(
                "# comment\n005930|삼성전자|3\n\nTSLA|Tesla|\n",
                encoding="utf-8",
            )

            records = load_target_records(target_file)

        self.assertEqual(
            records,
            [
                {"code": "005930", "name": "삼성전자", "quantity": 3},
                {"code": "TSLA", "name": "Tesla", "quantity": 1},
            ],
        )

    def test_load_target_records_raises_for_invalid_quantity(self):
        with TemporaryDirectory() as tmp_dir:
            target_file = Path(tmp_dir) / "targets.txt"
            target_file.write_text("005930|삼성전자|abc\n", encoding="utf-8")

            with self.assertRaises(TargetConfigError):
                load_target_records(target_file)

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
            prices_df,
            pd.Timestamp("2026-01-01"),
            pd.Timestamp("2026-01-04"),
            [
                {"code": "A", "name": "기존 ETF", "quantity": 2},
                {"code": "B", "name": "신규 ETF", "quantity": 5},
            ],
        )
        summary_by_name = {item["name"]: item for item in summary}

        self.assertEqual(summary_by_name["기존 ETF"]["base_date"], "2026-01-01")
        self.assertAlmostEqual(summary_by_name["기존 ETF"]["return"], 3.0)
        self.assertEqual(summary_by_name["기존 ETF"]["quantity"], 2)
        self.assertEqual(summary_by_name["신규 ETF"]["base_date"], "2026-01-03")
        self.assertEqual(summary_by_name["신규 ETF"]["date"], "2026-01-04")
        self.assertAlmostEqual(summary_by_name["신규 ETF"]["start_price"], 50.0)
        self.assertAlmostEqual(summary_by_name["신규 ETF"]["current_price"], 55.0)
        self.assertAlmostEqual(summary_by_name["신규 ETF"]["return"], 10.0)
        self.assertEqual(summary_by_name["신규 ETF"]["quantity"], 5)
        self.assertTrue(summary_by_name["신규 ETF"]["is_delayed_start"])

    def test_calculate_period_summary_does_not_mark_common_first_trading_day_as_delayed(self):
        dates = pd.to_datetime(["2026-01-02", "2026-01-03", "2026-01-04"])
        prices_df = pd.DataFrame(
            {
                "ETF A": [100, 110, 120],
                "ETF B": [200, 210, 220],
            },
            index=dates,
        )

        summary = calculate_period_summary(
            prices_df, pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-04")
        )
        summary_by_name = {item["name"]: item for item in summary}

        self.assertFalse(summary_by_name["ETF A"]["is_delayed_start"])
        self.assertFalse(summary_by_name["ETF B"]["is_delayed_start"])

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

    def test_calculate_portfolio_weights_uses_price_times_quantity(self):
        summary = [
            {"name": "삼성전자", "current_price": 100.0, "quantity": 2},
            {"name": "Tesla", "current_price": 300.0, "quantity": 1},
            {"name": "현금성", "current_price": 0.0, "quantity": 5},
        ]

        portfolio = calculate_portfolio_weights(summary)

        self.assertEqual([item["name"] for item in portfolio], ["Tesla", "삼성전자"])
        self.assertAlmostEqual(portfolio[0]["market_value"], 300.0)
        self.assertAlmostEqual(portfolio[0]["weight"], 60.0)
        self.assertAlmostEqual(portfolio[1]["market_value"], 200.0)
        self.assertAlmostEqual(portfolio[1]["weight"], 40.0)

    def test_calculate_portfolio_weights_respects_visible_names(self):
        summary = [
            {"name": "삼성전자", "current_price": 100.0, "quantity": 2},
            {"name": "Tesla", "current_price": 300.0, "quantity": 1},
        ]

        portfolio = calculate_portfolio_weights(summary, visible_names=["삼성전자"])

        self.assertEqual(len(portfolio), 1)
        self.assertEqual(portfolio[0]["name"], "삼성전자")
        self.assertAlmostEqual(portfolio[0]["weight"], 100.0)

    def test_calculate_period_summary_handles_duplicate_index(self):
        dates = pd.to_datetime(["2026-01-01", "2026-01-01", "2026-01-02", "2026-01-03"])
        prices_df = pd.DataFrame(
            {
                "ETF": [100, 101, 110, 120],
            },
            index=dates,
        )

        summary = calculate_period_summary(
            prices_df, pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-03")
        )

        self.assertEqual(summary[0]["base_date"], "2026-01-01")
        self.assertEqual(summary[0]["date"], "2026-01-03")
        self.assertAlmostEqual(summary[0]["start_price"], 100.0)
        self.assertAlmostEqual(summary[0]["current_price"], 120.0)
        self.assertAlmostEqual(summary[0]["return"], 20.0)

    def test_build_chart_keeps_expected_pyecharts_options(self):
        dates = pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"])
        norm_df = pd.DataFrame(
            {
                "ETF A": [100.0, 105.0, 110.0],
                "ETF B": [100.0, None, 98.5],
            },
            index=dates,
        )

        chart = build_chart(norm_df)

        self.assertEqual(len(chart.options["series"]), 2)
        self.assertEqual(chart.options["yAxis"][0]["name"], "Base 100")

    def test_build_portfolio_chart_keeps_expected_pyecharts_options(self):
        chart = build_portfolio_chart(
            [
                {"name": "ETF A", "weight": 60.0},
                {"name": "ETF B", "weight": 40.0},
            ]
        )

        self.assertEqual(len(chart.options["series"]), 2)
        self.assertEqual(chart.options["xAxis"][0]["max"], 100)

    @patch("app.get_local_echarts_script", return_value="window.__LOCAL_ECHARTS__ = true;")
    def test_build_pyecharts_html_inlines_local_echarts_script(self, _mock_script):
        dates = pd.to_datetime(["2026-01-01", "2026-01-02"])
        norm_df = pd.DataFrame({"ETF A": [100.0, 101.0]}, index=dates)

        html = build_pyecharts_html(build_chart(norm_df))

        self.assertIn("window.__LOCAL_ECHARTS__ = true;", html)
        self.assertNotIn('src="https://assets.pyecharts.org', html)
        self.assertNotIn("<html>", html)
        self.assertNotIn("<body>", html)


if __name__ == "__main__":
    unittest.main()
