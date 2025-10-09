from flask import Flask, render_template, jsonify, request
import os
from datetime import datetime, timedelta
import requests
import pandas as pd
import io
from monitor import MetricMonitor

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')  # Get from newsapi.org

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        
        # Run analysis - FIXED: using the correct method name 'run_analysis'
        results = monitor.run_analysis(start_date, end_date)
        
        # Convert results to JSON-serializable format
        serialized_results = {
            'metrics': results.get('metrics', {}),
            'insights': results.get('insights', []),
            'anomalies': results.get('anomalies', []),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': serialized_results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/exchange-rates')
def get_exchange_rates():
    """Get current exchange rates"""
    try:
        # Using exchangerate-api.com (free tier available)
        base_url = 'https://api.exchangerate-api.com/v4/latest/USD'
        
        response = requests.get(base_url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Filter to commonly used currencies for FP&A
        common_currencies = ['EUR', 'GBP', 'JPY', 'CNY', 'CAD', 'AUD', 'CHF', 'INR', 'BRL', 'MXN']
        rates = {curr: data['rates'].get(curr, 0) for curr in common_currencies if curr in data.get('rates', {})}
        
        return jsonify({
            'success': True,
            'base': 'USD',
            'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'rates': rates
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/news')
def get_news():
    """Get financial news relevant to FP&A"""
    try:
        if not NEWS_API_KEY:
            # Return mock data if no API key
            return jsonify({
                'success': True,
                'articles': [
                    {
                        'title': 'Financial Planning & Analysis Trends 2025',
                        'description': 'Latest trends in FP&A automation and AI integration',
                        'url': '#',
                        'publishedAt': datetime.now().isoformat(),
                        'source': {'name': 'Demo News'}
                    }
                ]
            })
        
        # Query NewsAPI for financial planning and business intelligence news
        url = 'https://newsapi.org/v2/everything'
        params = {
            'apiKey': NEWS_API_KEY,
            'q': 'financial planning OR FP&A OR business intelligence',
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 10
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        return jsonify({
            'success': True,
            'articles': data.get('articles', [])
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/upload-data', methods=['POST'])
def upload_data():
    """Upload and process Excel/CSV files for analysis"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Only CSV, XLS, and XLSX files are allowed'
            }), 400
        
        # Read file into pandas dataframe
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        
        # Data cleaning and processing
        # Remove completely empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Basic data profiling
        profile = {
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': df.columns.tolist(),
            'data_types': df.dtypes.astype(str).to_dict(),
            'missing_values': df.isnull().sum().to_dict(),
            'sample_data': df.head(10).to_dict('records')
        }
        
        # Try to identify numeric columns for visualization
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        # Generate basic statistics for numeric columns
        stats = {}
        if numeric_cols:
            stats = df[numeric_cols].describe().to_dict()
        
        # Store processed data in session or database (for now, return it)
        return jsonify({
            'success': True,
            'profile': profile,
            'statistics': stats,
            'numeric_columns': numeric_cols,
            'message': f'Successfully processed {len(df)} rows and {len(df.columns)} columns'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error processing file: {str(e)}'
        }), 500

@app.route('/api/visualize-data', methods=['POST'])
def visualize_data():
    """Generate visualizations from uploaded data"""
    try:
        data = request.get_json()
        
        if not data or 'sample_data' not in data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Convert data to DataFrame
        df = pd.DataFrame(data['sample_data'])
        
        # Prepare data for Plotly visualizations
        charts = []
        
        # Get numeric columns
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        # Create chart configurations for the frontend
        if numeric_cols:
            # Time series or line chart if there's a date column
            date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
            
            if date_cols and numeric_cols:
                charts.append({
                    'type': 'line',
                    'title': f'{numeric_cols[0]} Over Time',
                    'x_data': df[date_cols[0]].astype(str).tolist(),
                    'y_data': df[numeric_cols[0]].tolist(),
                    'x_label': date_cols[0],
                    'y_label': numeric_cols[0]
                })
            
            # Bar chart for categorical data
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            if categorical_cols and numeric_cols:
                grouped = df.groupby(categorical_cols[0])[numeric_cols[0]].sum().reset_index()
                charts.append({
                    'type': 'bar',
                    'title': f'{numeric_cols[0]} by {categorical_cols[0]}',
                    'x_data': grouped[categorical_cols[0]].tolist(),
                    'y_data': grouped[numeric_cols[0]].tolist(),
                    'x_label': categorical_cols[0],
                    'y_label': numeric_cols[0]
                })
        
        return jsonify({
            'success': True,
            'charts': charts
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error generating visualizations: {str(e)}'
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development')
