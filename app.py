import os
import io
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd
import requests
from flask import Flask, render_template, jsonify, request, session, send_from_directory
from werkzeug.utils import secure_filename

from monitor import MetricMonitor

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# API Keys / URLs (never log these)
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434/api/generate')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY', '')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx'}


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and preprocess dataframe for analysis/visualization."""
    # Remove empty rows/cols
    df = df.dropna(how='all', axis=0)
    df = df.dropna(how='all', axis=1)

    # Normalize column names
    df.columns = [str(c).strip() for c in df.columns]

    # Strip strings
    for col in df.select_dtypes(include=['object']).columns:
        try:
            df[col] = df[col].astype(str).str.strip()
        except Exception:
            pass

    # Convert numeric-like strings
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col], errors='ignore')
        except Exception:
            pass

    # Parse dates heuristically
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                parsed = pd.to_datetime(df[col], errors='raise', infer_datetime_format=True)
                # consider date if at least half are valid
                mask_valid = ~parsed.isna()
                if mask_valid.mean() >= 0.5:
                    df[col] = parsed
            except Exception:
                continue

    return df


def read_any_table(file_storage) -> pd.DataFrame:
    """Read CSV or Excel into DataFrame safely."""
    filename = secure_filename(file_storage.filename)
    ext = filename.rsplit('.', 1)[1].lower()

    contents = file_storage.read()
    # rewind buffer for future reads if needed
    buf = io.BytesIO(contents)

    if ext == 'csv':
        # try common encodings
        for enc in ['utf-8', 'utf-8-sig', 'latin-1']:
            try:
                buf.seek(0)
                return pd.read_csv(buf, encoding=enc)
            except Exception:
                continue
        raise ValueError('Failed to read CSV with common encodings.')
    elif ext in {'xls', 'xlsx'}:
        buf.seek(0)
        return pd.read_excel(buf)
    else:
        raise ValueError('Unsupported file type')


@app.before_request
def set_secure_session():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(hours=12)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', app_name='PingPong')


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'app': 'PingPong'
    })


@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file part'}), 400
        f = request.files['file']
        if f.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'}), 400
        if not allowed_file(f.filename):
            return jsonify({'success': False, 'error': 'Unsupported file type'}), 400

        # Read into DataFrame and clean
        df = read_any_table(f)
        df = clean_dataframe(df)

        # Store in session (truncate to avoid huge payloads)
        preview = df.head(1000)  # cap preview
        session['data_preview'] = preview.to_json(orient='split', date_format='iso')
        session['columns'] = list(preview.columns)

        return jsonify({
            'success': True,
            'rows': int(preview.shape[0]),
            'cols': int(preview.shape[1]),
            'columns': session['columns']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'Upload error: {str(e)}'}), 500


@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        payload = request.get_json(silent=True) or {}
        question = str(payload.get('question', 'Provide a concise FP&A analysis of this dataset.'))

        if 'data_preview' not in session:
            return jsonify({'success': False, 'error': 'No data in session. Upload first.'}), 400

        # Prepare prompt context from data preview
        df = pd.read_json(session['data_preview'], orient='split')
        sample_text = df.head(30).to_markdown(index=False)
        prompt = (
            "You are a senior FP&A analyst. Analyze the dataset sample below, "
            "highlight trends, anomalies, and 3-5 suggested visuals with fields. "
            "Provide concise, bullet recommendations.\n\n"
            f"User question: {question}\n\nSample (first 30 rows as table):\n{sample_text}"
        )

        # Prefer local open-source model via Ollama if available
        analysis = None
        try:
            resp = requests.post(
                OLLAMA_API_URL,
                json={
                    'model': payload.get('model', 'llama3.1:8b'),
                    'prompt': prompt,
                    'stream': False,
                },
                timeout=60,
            )
            if resp.ok:
                data = resp.json()
                analysis = data.get('response') or data.get('text')
        except Exception:
            analysis = None

        # Fallback to Perplexity API if configured
        if not analysis and PERPLEXITY_API_KEY:
            try:
                headers = {"Authorization": f"Bearer {PERPLEXITY_API_KEY}", "Content-Type": "application/json"}
                px = requests.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers=headers,
                    json={
                        "model": payload.get('perplexity_model', "sonar-small-online"),
                        "messages": [
                            {"role": "system", "content": "You are a helpful FP&A data analyst."},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.2,
                        "stream": False,
                    },
                    timeout=60,
                )
                if px.ok:
                    j = px.json()
                    choices = j.get('choices') or []
                    if choices:
                        analysis = choices[0].get('message', {}).get('content')
            except Exception:
                analysis = None

        if not analysis:
            analysis = "No LLM available. Please configure OLLAMA_API_URL or PERPLEXITY_API_KEY."

        return jsonify({'success': True, 'analysis': analysis})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Analyze error: {str(e)}'}), 500


@app.route('/visualize', methods=['POST'])
def visualize():
    try:
        if 'data_preview' not in session:
            return jsonify({'success': False, 'error': 'No data in session. Upload first.'}), 400

        params = request.get_json(silent=True) or {}
        chart_type = params.get('chart', 'auto')

        df = pd.read_json(session['data_preview'], orient='split')

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]']).columns.tolist()
        categorical_cols = [c for c in df.columns if c not in numeric_cols + date_cols]

        charts: List[Dict[str, Any]] = []

        if chart_type in ('auto', 'line'):
            if date_cols and numeric_cols:
                for num_col in numeric_cols[:3]:  # up to 3 lines
                    charts.append({
                        'type': 'line',
                        'title': f'{num_col} Over Time',
                        'x_data': df[date_cols[0]].astype(str).tolist(),
                        'y_data': df[num_col].tolist(),
                        'x_label': date_cols[0],
                        'y_label': num_col,
                    })

        if chart_type in ('auto', 'bar'):
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
                    'y_label': num_col,
                })

        if chart_type in ('auto', 'pie'):
            if categorical_cols:
                cat_col = categorical_cols[0]
                value_counts = df[cat_col].value_counts().head(10)
                charts.append({
                    'type': 'pie',
                    'title': f'Distribution of {cat_col}',
                    'labels': value_counts.index.tolist(),
                    'values': value_counts.values.tolist(),
                })

        if not charts:
            return jsonify({'success': False, 'error': 'No suitable fields for visualization.'}), 400

        return jsonify({'success': True, 'charts': charts})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Visualization error: {str(e)}'}), 500


# Static uploads (optional, if front-end needs to download back)
@app.route('/uploads/<path:filename>')
def get_upload(filename: str):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development')
