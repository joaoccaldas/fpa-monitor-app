import unittest
from monitor import MetricMonitor
class AlignmentTests(unittest.TestCase):
    def test_sparse_rows_preserve_anomaly_date(self):
        m=MetricMonitor({'anomaly_threshold':1,'metrics':['revenue']})
        rows=[{'date':'missing'}, {'date':'a','revenue':0}, {'date':'b','revenue':0}, {'date':'actual-outlier','revenue':100}]
        result=m.detect_anomalies(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['date'], 'actual-outlier')
    def test_non_finite_rejected(self):
        m=MetricMonitor({'anomaly_threshold':1,'metrics':['revenue']})
        with self.assertRaises(ValueError): m.detect_anomalies([{'date':'a','revenue':float('nan')}])
    def test_default_requires_source(self):
        import os
        from unittest.mock import patch
        from datetime import datetime
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError): MetricMonitor().fetch_metrics(datetime.now(),datetime.now())
if __name__ == '__main__': unittest.main()
