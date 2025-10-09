from flask import Flask, render_template, jsonify
import os
from datetime import datetime, timedelta
import requests
from monitor import MetricMonitor

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')  # Get from newsapi.org

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/fpa-metrics')
def get_fpa_metrics():
    """Get FP&A monitoring metrics and insights"""
    try:
        # Initialize monitor
        monitor = MetricMonitor()
        
        # Get data for last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Run analysis
        results = monitor.analyze_metrics(start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
