import unittest
from unittest.mock import patch
import pandas as pd
import numpy as np
from app import fetch_stock_data, calculate_ytd_summary

class TestApp(unittest.TestCase):

    @patch('FinanceDataReader.DataReader')
    def test_fetch_stock_data(self, mock_reader):
        # Mocking individual stock data
        mock_df = pd.DataFrame({'Close': [100, 110]}, index=pd.to_datetime(['2025-12-30', '2026-01-02']))
        mock_reader.return_value = mock_df

        target_stocks = {"005930": "삼성전자"}
        result = fetch_stock_data(target_stocks)

        self.assertIn("삼성전자", result.columns)
        self.assertEqual(len(result), 2)
        self.assertEqual(result.iloc[0]["삼성전자"], 100)

    def test_calculate_ytd_summary(self):
        # Prepare mock daily prices DataFrame
        dates = pd.to_datetime(['2025-12-30', '2026-01-02', '2026-01-03'])
        prices_df = pd.DataFrame({
            "삼성전자": [100, 110, 120]
        }, index=dates)

        summary = calculate_ytd_summary(prices_df)

        self.assertEqual(len(summary), 1)
        self.assertEqual(summary.iloc[0]["종목명"], "삼성전자")
        self.assertEqual(summary.iloc[0]["2025년 말 가격"], "100원") # 2025-12-30 price
        self.assertEqual(summary.iloc[0]["현재 가격"], "120원") # 2026-01-03 price
        self.assertEqual(summary.iloc[0]["YTD 수익률"], "20.00%") # ((120-100)/100)*100

    def test_calculate_ytd_summary_empty(self):
        # Index must be DatetimeIndex for the comparison in the function
        prices_df = pd.DataFrame(index=pd.to_datetime([]))
        summary = calculate_ytd_summary(prices_df)
        self.assertTrue(summary.empty)

if __name__ == '__main__':
    unittest.main()
