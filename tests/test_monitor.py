import unittest

from monitor import MetricMonitor


class StatisticalMetricMonitorContractTests(unittest.TestCase):
    def setUp(self):
        self.monitor = MetricMonitor(
            {
                "anomaly_threshold": 2.5,
                "lookback_days": 30,
                "alert_email": "",
                "metrics": ["revenue"],
            }
        )

    def test_severity_boundaries_are_explicit(self):
        self.assertEqual("LOW", self.monitor._calculate_severity(2.5))
        self.assertEqual("MEDIUM", self.monitor._calculate_severity(2.6))
        self.assertEqual("MEDIUM", self.monitor._calculate_severity(3.0))
        self.assertEqual("HIGH", self.monitor._calculate_severity(3.1))
        self.assertEqual("HIGH", self.monitor._calculate_severity(4.0))
        self.assertEqual("CRITICAL", self.monitor._calculate_severity(4.1))

    def test_constant_series_produces_no_anomaly(self):
        rows = [
            {"date": f"2026-01-0{i}", "revenue": 100.0}
            for i in range(1, 7)
        ]
        self.assertEqual([], self.monitor.detect_anomalies(rows))

    def test_insight_contract_contains_period_summary_and_recommendations(self):
        rows = [
            {"date": "2026-01-01", "revenue": 100.0},
            {"date": "2026-01-02", "revenue": 110.0},
            {"date": "2026-01-03", "revenue": 120.0},
        ]
        result = self.monitor.generate_insights(rows, [])
        self.assertEqual("2026-01-01", result["period"]["start"])
        self.assertEqual("2026-01-03", result["period"]["end"])
        self.assertIn("revenue", result["summary"])
        self.assertEqual("INCREASING", result["summary"]["revenue"]["trend"])
        self.assertIsInstance(result["recommendations"], list)


if __name__ == "__main__":
    unittest.main()
