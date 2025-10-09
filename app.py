from flask import Flask, render_template, jsonify, request, session
import os
from datetime import datetime, timedelta
import requests
import pandas as pd
import numpy as np
import io
import json
from werkzeug.utils import secure_filename
from monitor import MetricMonitor

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# API Keys
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434/api/generate')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY', '')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clean_dataframe(df):
    """Clean and preprocess dataframe"""
    # Remove completely empty rows and columns
    df = df.dropna(how='all', axis=0)
    df = df.dropna(how='all', axis=1)
    
    # Strip whitespace from string columns
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.strip() if df[col].dtype == 'object' else df[col]
    
    # Convert string representations of numbers to numeric
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col], errors='ignore')
        except:
            pass
    
    # Try to parse date columns
    for col in df.columns:
        if 'date' in col.lower() or 'time' in col.lower():
            try:
                df[col] = pd.to_datetime(df[col], errors='ignore')
            except:
                pass
    
    return df

def generate_data_summary(df):
    """Generate summary statistics for the dataframe"""
    summary = {
        'shape': df.shape,
        'columns': list(df.columns),
        'dtypes': df.dtypes.astype(str).to_dict(),
        'missing_values': df.isnull().sum().to_dict(),
        'numeric_columns': list(df.select_dtypes(include=[np.number]).columns),
        'categorical_columns': list(df.select_dtypes(include=['object']).columns),
    }
    
    # Add basic statistics for numeric columns
    if summary['numeric_columns']:
        summary['statistics'] = df[summary['numeric_columns']].describe().to_dict()
    
    return summary

async def analyze_with_llm(data_summary, user_query="Analyze this financial data"):
    """Async call to LLM for data analysis"""
    try:
        # Try Ollama first (local open-source LLM)
        prompt = f"""You are a financial data analyst. Analyze the following data summary and provide insights:
        
Data Summary:
{json.dumps(data_summary, indent=2)}

User Query: {user_query}

Provide actionable insights, trends, and recommendations."""
        
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": "llama2",  # Can be changed to other models
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get('response', 'No analysis generated')
        
        # Fallback to Perplexity API if available
        if PERPLEXITY_API_KEY:
            headers = {
                'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
                'Content-Type': 'application/json'
            }
            response = requests.post(
                'https://api.perplexity.ai/chat/completions',
                headers=headers,
                json={
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
        
        return "LLM analysis unavailable. Please configure Ollama or Perplexity API."
        
    except Exception as e:
        return f"Error during LLM analysis: {str(e)}"

@app.route('/')
def index():
    """Main dashboard page - PingPong"""
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

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload for Excel/CSV files"""
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Only CSV, XLS, and XLSX files are allowed.'
            }), 400
        
        # Secure filename
        filename = secure_filename(file.filename)
        
        # Read file into pandas dataframe
        try:
            file_ext = filename.rsplit('.', 1)[1].lower()
            
            if file_ext == 'csv':
                df = pd.read_csv(file, encoding='utf-8', encoding_errors='ignore')
            elif file_ext in ['xls', 'xlsx']:
                df = pd.read_excel(file, engine='openpyxl' if file_ext == 'xlsx' else 'xlrd')
            
            # Clean the dataframe
            df = clean_dataframe(df)
            
            # Generate data summary
            data_summary = generate_data_summary(df)
            
            # Save cleaned data to temporary file
            temp_filename = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
            df.to_csv(temp_filepath, index=False)
            
            # Store file path in session
            session['current_file'] = temp_filepath
            session['data_summary'] = data_summary
            
            return jsonify({
                'success': True,
                'message': 'File uploaded and processed successfully',
                'filename': filename,
                'summary': data_summary,
                'preview': df.head(10).to_dict(orient='records')
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error reading file: {str(e)}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Upload error: {str(e)}'
        }), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_data():
    """Analyze uploaded data with LLM"""
    try:
        # Check if data exists in session
        if 'data_summary' not in session:
            return jsonify({
                'success': False,
                'error': 'No data uploaded. Please upload a file first.'
            }), 400
        
        # Get user query from request
        data = request.get_json()
        user_query = data.get('query', 'Analyze this financial data and provide insights')
        
        # Get data summary from session
        data_summary = session['data_summary']
        
        # Call LLM for analysis
        import asyncio
        analysis = asyncio.run(analyze_with_llm(data_summary, user_query))
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Analysis error: {str(e)}'
        }), 500

@app.route('/api/visualize', methods=['POST'])
def visualize_data():
    """Generate visualization configurations for uploaded data"""
    try:
        # Check if data exists
        if 'current_file' not in session:
            return jsonify({
                'success': False,
                'error': 'No data uploaded'
            }), 400
        
        # Load data from temporary file
        df = pd.read_csv(session['current_file'])
        
        # Get request parameters
        data = request.get_json() or {}
        chart_type = data.get('chart_type', 'auto')
        
        charts = []
        
        # Get numeric and categorical columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
        
        # Generate visualizations based on data structure
        if chart_type == 'auto' or chart_type == 'line':
            # Time series chart if date column exists
            if date_cols and numeric_cols:
                for num_col in numeric_cols[:3]:  # Limit to first 3
                    charts.append({
                        'type': 'line',
                        'title': f'{num_col} Over Time',
                        'x_data': df[date_cols[0]].astype(str).tolist(),
                        'y_data': df[num_col].tolist(),
                        'x_label': date_cols[0],
                        'y_label': num_col
                    })
        
        if chart_type == 'auto' or chart_type == 'bar':
            # Bar chart for categorical data
            if categorical_cols and numeric_cols:
                cat_col = categorical_cols[0]
                num_col = numeric_cols[0]
                grouped = df.groupby(cat_col)[num_col].sum().reset_index()
                
                charts.append({
                    'type': 'bar',
                    'title': f'{num_col} by {cat_col}',
                    'x_data': grouped[cat_col].tolist(),
                    'y_data': grouped[num_col].tolist(),
                    'x_label': cat_col,
                    'y_label': num_col
                })
        
        if chart_type == 'auto' or chart_type == 'pie':
            # Pie chart for categorical distribution
            if categorical_cols:
                cat_col = categorical_cols[0]
                value_counts = df[cat_col].value_counts().head(10)
                
                charts.append({
                    'type': 'pie',
                    'title': f'Distribution of {cat_col}',
                    'labels': value_counts.index.tolist(),
                    'values': value_counts.values.tolist()
                })
        
        return jsonify({
            'success': True,
            'charts': charts
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Visualization error: {str(e)}'
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development')
