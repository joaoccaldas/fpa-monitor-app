#!/usr/bin/env python3
"""
FP&A Metric Monitoring Application
Monitors financial metrics, detects anomalies, and provides automated insights
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fpa_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class MetricMonitor:
    """Monitor financial metrics and detect anomalies"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the metric monitor
        
        Args:
            config: Configuration dictionary with thresholds and settings
        """
        self.config = config or self._load_default_config()
        self.metrics_history = []
        logger.info("MetricMonitor initialized with config: %s", self.config)
    
    def _load_default_config(self) -> Dict:
        """Load default configuration"""
        return {
            'anomaly_threshold': float(os.getenv('ANOMALY_THRESHOLD', '2.5')),
            'lookback_days': int(os.getenv('LOOKBACK_DAYS', '30')),
            'alert_email': os.getenv('ALERT_EMAIL', ''),
            'metrics': [
                'revenue',
                'expenses',
                'profit_margin',
                'cash_flow',
                'ar_days',
                'ap_days'
            ]
        }
    
    def fetch_metrics(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch metrics from data source
        
        Args:
            start_date: Start date for metric retrieval
            end_date: End date for metric retrieval
            
        Returns:
            List of metric dictionaries
        """
        # TODO: Implement actual data source integration
        # This is a placeholder that generates sample data
        logger.info(f"Fetching metrics from {start_date} to {end_date}")
        
        metrics = []
        current_date = start_date
        
        while current_date <= end_date:
            daily_metrics = {
                'date': current_date.isoformat(),
                'revenue': np.random.normal(100000, 10000),
                'expenses': np.random.normal(70000, 7000),
                'profit_margin': np.random.normal(30, 3),
                'cash_flow': np.random.normal(25000, 5000),
                'ar_days': np.random.normal(45, 5),
                'ap_days': np.random.normal(30, 3)
            }
            metrics.append(daily_metrics)
            current_date += timedelta(days=1)
        
        self.metrics_history.extend(metrics)
        return metrics
    
    def detect_anomalies(self, metrics: List[Dict]) -> List[Dict]:
        """Detect anomalies in metrics using statistical methods
        
        Args:
            metrics: List of metric dictionaries
            
        Returns:
            List of anomaly dictionaries
        """
        anomalies = []
        threshold = self.config['anomaly_threshold']
        
        for metric_name in self.config['metrics']:
            values = [m[metric_name] for m in metrics if metric_name in m]
            
            if len(values) < 3:
                continue
            
            mean = np.mean(values)
            std = np.std(values)
            
            for i, (metric_dict, value) in enumerate(zip(metrics, values)):
                z_score = abs((value - mean) / std) if std > 0 else 0
                
                if z_score > threshold:
                    anomaly = {
                        'date': metric_dict['date'],
                        'metric': metric_name,
                        'value': value,
                        'expected_mean': mean,
                        'std_dev': std,
                        'z_score': z_score,
                        'severity': self._calculate_severity(z_score)
                    }
                    anomalies.append(anomaly)
                    logger.warning(f"Anomaly detected: {anomaly}")
        
        return anomalies
    
    def _calculate_severity(self, z_score: float) -> str:
        """Calculate severity level based on z-score
        
        Args:
            z_score: Statistical z-score
            
        Returns:
            Severity level string
        """
        if z_score > 4:
            return 'CRITICAL'
        elif z_score > 3:
            return 'HIGH'
        elif z_score > 2.5:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def generate_insights(self, metrics: List[Dict], anomalies: List[Dict]) -> Dict:
        """Generate automated insights from metrics and anomalies
        
        Args:
            metrics: List of metric dictionaries
            anomalies: List of detected anomalies
            
        Returns:
            Dictionary containing insights
        """
        insights = {
            'timestamp': datetime.now().isoformat(),
            'period': {
                'start': metrics[0]['date'] if metrics else None,
                'end': metrics[-1]['date'] if metrics else None
            },
            'summary': {},
            'anomalies': anomalies,
            'recommendations': []
        }
        
        # Calculate summary statistics
        for metric_name in self.config['metrics']:
            values = [m[metric_name] for m in metrics if metric_name in m]
            if values:
                insights['summary'][metric_name] = {
                    'mean': float(np.mean(values)),
                    'median': float(np.median(values)),
                    'std': float(np.std(values)),
                    'min': float(np.min(values)),
                    'max': float(np.max(values)),
                    'trend': self._calculate_trend(values)
                }
        
        # Generate recommendations
        insights['recommendations'] = self._generate_recommendations(insights['summary'], anomalies)
        
        logger.info(f"Generated insights for {len(metrics)} metrics with {len(anomalies)} anomalies")
        return insights
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction
        
        Args:
            values: List of numeric values
            
        Returns:
            Trend direction string
        """
        if len(values) < 2:
            return 'INSUFFICIENT_DATA'
        
        # Simple linear regression slope
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        if abs(slope) < 0.01:
            return 'STABLE'
        elif slope > 0:
            return 'INCREASING'
        else:
            return 'DECREASING'
    
    def _generate_recommendations(self, summary: Dict, anomalies: List[Dict]) -> List[str]:
        """Generate actionable recommendations
        
        Args:
            summary: Summary statistics dictionary
            anomalies: List of detected anomalies
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Revenue recommendations
        if 'revenue' in summary:
            if summary['revenue']['trend'] == 'DECREASING':
                recommendations.append("Revenue is declining. Review sales pipeline and pricing strategy.")
            elif any(a['metric'] == 'revenue' and a['severity'] in ['HIGH', 'CRITICAL'] for a in anomalies):
                recommendations.append("Significant revenue anomaly detected. Investigate unusual transactions.")
        
        # Expense recommendations
        if 'expenses' in summary:
            if summary['expenses']['trend'] == 'INCREASING':
                recommendations.append("Expenses are rising. Review cost optimization opportunities.")
        
        # Profit margin recommendations
        if 'profit_margin' in summary:
            if summary['profit_margin']['mean'] < 20:
                recommendations.append("Profit margin below target. Consider price increases or cost reductions.")
        
        # Cash flow recommendations
        if 'cash_flow' in summary:
            if summary['cash_flow']['trend'] == 'DECREASING':
                recommendations.append("Cash flow is declining. Review AR/AP and working capital management.")
        
        # AR/AP recommendations
        if 'ar_days' in summary and summary['ar_days']['mean'] > 45:
            recommendations.append("Accounts receivable days above target. Implement stricter collection policies.")
        
        if 'ap_days' in summary and summary['ap_days']['mean'] < 30:
            recommendations.append("Accounts payable days below average. Review payment terms with vendors.")
        
        if not recommendations:
            recommendations.append("All metrics are within normal ranges. Continue monitoring.")
        
        return recommendations
    
    def run_analysis(self, days: Optional[int] = None) -> Dict:
        """Run complete analysis for specified period
        
        Args:
            days: Number of days to analyze (default from config)
            
        Returns:
            Analysis results dictionary
        """
        days = days or self.config['lookback_days']
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        logger.info(f"Starting analysis for {days} days")
        
        # Fetch metrics
        metrics = self.fetch_metrics(start_date, end_date)
        
        # Detect anomalies
        anomalies = self.detect_anomalies(metrics)
        
        # Generate insights
        insights = self.generate_insights(metrics, anomalies)
        
        return insights
    
    def export_results(self, insights: Dict, output_file: str = 'fpa_insights.json'):
        """Export insights to JSON file
        
        Args:
            insights: Insights dictionary
            output_file: Output file path
        """
        try:
            with open(output_file, 'w') as f:
                json.dump(insights, f, indent=2)
            logger.info(f"Results exported to {output_file}")
        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            raise


def main():
    """Main entry point for the application"""
    import argparse
    
    parser = argparse.ArgumentParser(description='FP&A Metric Monitor')
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days to analyze (default: 30)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='fpa_insights.json',
        help='Output file path (default: fpa_insights.json)'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    
    args = parser.parse_args()
    
    # Load config if provided
    config = None
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {args.config}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            sys.exit(1)
    
    # Initialize monitor
    monitor = MetricMonitor(config)
    
    # Run analysis
    try:
        insights = monitor.run_analysis(days=args.days)
        
        # Print summary
        print("\n" + "="*60)
        print("FP&A MONITORING REPORT")
        print("="*60)
        print(f"\nPeriod: {insights['period']['start']} to {insights['period']['end']}")
        print(f"\nAnomalies Detected: {len(insights['anomalies'])}")
        
        if insights['anomalies']:
            print("\nTop Anomalies:")
            for anomaly in sorted(insights['anomalies'], key=lambda x: x['z_score'], reverse=True)[:5]:
                print(f"  - {anomaly['date']}: {anomaly['metric']} = {anomaly['value']:.2f} "
                      f"(Z-score: {anomaly['z_score']:.2f}, Severity: {anomaly['severity']})")
        
        print("\nRecommendations:")
        for i, rec in enumerate(insights['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        print("\n" + "="*60 + "\n")
        
        # Export results
        monitor.export_results(insights, args.output)
        print(f"Detailed results saved to {args.output}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
