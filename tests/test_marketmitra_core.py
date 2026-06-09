import unittest
from pathlib import Path

from src.analytics.market_pressure import compute_market_pressure
from src.analytics.price_trends import compare_markets, latest_market_summary
from src.config import RAW_DATA_DIR
from src.forecasting.prophet_model import forecast_summary, run_price_forecast
from src.ingestion.data_loader import filter_market_data, load_market_data
from src.recommendations.strategy_engine import generate_selling_recommendation


class MarketMitraCoreTest(unittest.TestCase):
    def test_end_to_end_demo_path(self):
        if not list(Path(RAW_DATA_DIR).glob("*.csv")):
            self.skipTest("Original dataset CSV not present in data/raw.")

        df = load_market_data(force_rebuild=True)
        group_cols = ["commodity", "state", "district", "market"]
        commodity, state, district, market = df.groupby(group_cols).size().sort_values(ascending=False).index[0]
        series = filter_market_data(df, commodity=commodity, state=state, district=district, market=market)

        self.assertGreater(len(df), 1000)
        self.assertGreater(len(series), 0)

        summary = latest_market_summary(series)
        pressure = compute_market_pressure(summary)
        forecast_df, _, _ = run_price_forecast(series, periods=7)
        forecast = forecast_summary(forecast_df, days_ahead=7)
        if not forecast.get("available"):
            forecast["forecast_price"] = summary["current_price"]
            forecast["forecast_trend"] = "Insufficient history"
        comparison = compare_markets(df, commodity, state)

        recommendation = generate_selling_recommendation(
            commodity=commodity,
            local_market=market,
            summary=summary,
            forecast=forecast,
            market_pressure=pressure,
            market_comparison=comparison,
            transport_cost_per_quintal=80,
            storage_cost_per_quintal_per_day=4,
            hold_days=7,
        )

        self.assertGreater(summary["current_price"], 0)
        self.assertIn("pressure", pressure)
        self.assertGreater(forecast["forecast_price"], 0)
        self.assertTrue(recommendation.action)
        self.assertGreaterEqual(recommendation.confidence_score, 0)


if __name__ == "__main__":
    unittest.main()
