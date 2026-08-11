from pathlib import Path
import sys
import unittest

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

from credit_risk.metrics import calculate_metrics
from credit_risk.parser import FinancialStatements
from credit_risk.scoring import load_config, score_company


def sample_statements() -> FinancialStatements:
    values = {
        "1200": {2023: 950.0, 2024: 900.0},
        "1210": {2023: 120.0, 2024: 100.0},
        "1240": {2023: 40.0, 2024: 30.0},
        "1250": {2023: 80.0, 2024: 50.0},
        "1300": {2023: 380.0, 2024: 350.0},
        "1370": {2023: 70.0, 2024: 60.0},
        "1400": {2023: 200.0, 2024: 220.0},
        "1500": {2023: 820.0, 2024: 850.0},
        "1520": {2023: 600.0, 2024: 720.0},
        "1600": {2023: 1_400.0, 2024: 1_420.0},
        "1700": {2023: 1_400.0, 2024: 1_420.0},
        "2110": {2023: 1_100.0, 2024: 760.0},
        "2200": {2023: 45.0, 2024: 20.0},
        "2400": {2023: 20.0, 2024: 5.0},
    }
    return FinancialStatements(
        company="Test Company",
        source_file="synthetic.xlsx",
        periods=[2023, 2024],
        values=values,
        source_rows={},
        warnings=[],
    )


class CoreTests(unittest.TestCase):
    def test_metrics_are_consistent(self):
        metrics = calculate_metrics(sample_statements())
        self.assertAlmostEqual(metrics["balance_difference"], 0.0)
        self.assertLess(metrics["revenue_growth"], -0.30)
        self.assertLess(metrics["working_capital"], 100.0)

    def test_score_is_bounded_and_explainable(self):
        metrics = calculate_metrics(sample_statements())
        config = load_config(PROJECT_DIR / "config" / "scoring_config.json")
        result = score_company(metrics, config)
        self.assertGreaterEqual(result["score"], 0.0)
        self.assertLessEqual(result["score"], 100.0)
        self.assertEqual(result["confidence"], 100.0)
        self.assertEqual(len(result["scorecard"]), len(config["indicators"]))


if __name__ == "__main__":
    unittest.main()
