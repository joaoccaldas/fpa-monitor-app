import os
import io
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

import numpy as np
import pandas as pd
from flask import Flask, render_template, jsonify, request, send_file
from werkzeug.exceptions import RequestEntityTooLarge, BadRequest

app = Flask(__name__)

# Config
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
UPLOAD_FOLDER = app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO').upper())
logger = logging.getLogger(__name__)

ALLOWED_EXT = {'.csv', '.xls', '.xlsx', '.json'}

dataframe: pd.DataFrame | None = None


def allowed_file(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXT


def load_to_df(path: str) -> pd.DataFrame:
    ext = os.path.splitext(path.lower())[1]
    if ext == '.csv':
        return pd.read_csv(path)
    if ext in {'.xls', '.xlsx'}:
        return pd.read_excel(path)
    if ext == '.json':
        return pd.read_json(path)
    raise BadRequest('Unsupported file type')


def infer_fields(df: pd.DataFrame) -> List[Dict[str, Any]]:
    fields: List[Dict[str, Any]] = []
    for c in df.columns:
        series = df[c]
        if pd.api.types.is_numeric_dtype(series):
            ftype = 'number'
        elif pd.api.types.is_datetime64_any_dtype(series):
            ftype = 'date'
        else:
            ftype = 'string'
        fields.append({'name': str(c), 'type': ftype})
    return fields


@app.route('/')
def index():
    return render_template('index.html')


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    return jsonify({'error': 'File too large'}), 413


@app.route('/upload', methods=['POST'])
def upload():
    global dataframe
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    f = request.files['file']
    if f.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if not allowed_file(f.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    try:
        tmp_path = os.path.join(UPLOAD_FOLDER, f.filename)
        f.save(tmp_path)
        df = load_to_df(tmp_path)
        # Normalize: parse dates
        for col in df.columns:
            if df[col].dtype == object:
                try:
                    parsed = pd.to_datetime(df[col], errors='raise')
                    # Accept only if many values parsed to datetime
                    if parsed.notna().mean() > 0.8:
                        df[col] = parsed
                except Exception:
                    pass
        dataframe = df
        meta = {'rows': int(len(df)), 'fields': infer_fields(df)}
        return jsonify({'status': 'ok', 'meta': meta})
    except Exception as ex:
        logger.exception('Upload failed')
        return jsonify({'error': str(ex)}), 500


@app.route('/sample')
def sample():
    # Generate small FP&A-like sample
    rng = pd.date_range(end=datetime.today(), periods=12, freq='M')
    categories = ['North', 'South', 'East', 'West']
    df = pd.DataFrame({
        'month': np.repeat(rng, len(categories)),
        'region': categories * len(rng),
        'revenue': np.random.randint(80, 200, len(rng) * len(categories)),
        'cost': np.random.randint(40, 120, len(rng) * len(categories))
    })
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return send_file(io.BytesIO(buf.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name='sample.csv')


@app.route('/export/csv')
def export_csv():
    if dataframe is None:
        return jsonify({'error': 'No data loaded'}), 400
    buf = io.StringIO()
    dataframe.to_csv(buf, index=False)
    buf.seek(0)
    return send_file(io.BytesIO(buf.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name='data.csv')


@app.route('/meta')
def meta():
    if dataframe is None:
        return jsonify({'fields': [], 'rows': 0})
    return jsonify({'fields': infer_fields(dataframe), 'rows': int(len(dataframe))})


def build_plotly_config(df: pd.DataFrame, chart_type: str, x: str | None, y: str | None, group: str | None) -> Dict[str, Any]:
    if df is None or df.empty:
        return {'data': [], 'layout': {'title': 'No data', 'paper_bgcolor': 'rgba(0,0,0,0)'}}

    layout: Dict[str, Any] = {
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'margin': {'t': 40, 'r': 20, 'b': 60, 'l': 60},
        'legend': {'orientation': 'h'},
        'xaxis': {'title': x or ''},
        'yaxis': {'title': y or ''},
    }

    config = {'responsive': True, 'displaylogo': False, 'modeBarButtonsToRemove': ['toggleSpikelines']}

    traces: List[Dict[str, Any]] = []

    if chart_type in {'line', 'area', 'bar', 'stacked_bar', 'scatter'}:
        if not x or not y:
            raise BadRequest('x and y are required for this chart type')
        dfx = df.copy()
        if group and group in dfx.columns:
            for g, d in dfx.groupby(group):
                trace_type = 'scatter'
                mode = 'lines' if chart_type in {'line', 'area'} else 'markers'
                if chart_type in {'bar', 'stacked_bar'}:
                    t = {'type': 'bar'}
                else:
                    t = {'type': 'scatter', 'mode': mode}
                tr = {**t, 'name': str(g), 'x': d[x].astype(str).tolist(), 'y': d[y].tolist()}
                if chart_type == 'area':
                    tr['fill'] = 'tozeroy'
                traces.append(tr)
            if chart_type == 'stacked_bar':
                layout['barmode'] = 'stack'
        else:
            if chart_type in {'bar', 'stacked_bar'}:
                traces.append({'type': 'bar', 'name': y, 'x': dfx[x].astype(str).tolist(), 'y': dfx[y].tolist()})
            else:
                mode = 'lines' if chart_type in {'line', 'area'} else 'markers'
                tr = {'type': 'scatter', 'mode': mode, 'name': y, 'x': dfx[x].astype(str).tolist(), 'y': dfx[y].tolist()}
                if chart_type == 'area':
                    tr['fill'] = 'tozeroy'
                traces.append(tr)

    elif chart_type == 'pie':
        if not x or not y:
            raise BadRequest('x and y required for pie')
        agg = df.groupby(x, dropna=False)[y].sum().reset_index()
        traces.append({'type': 'pie', 'labels': agg[x].astype(str).tolist(), 'values': agg[y].tolist(), 'hole': 0.3})

    elif chart_type == 'heatmap':
        # For heatmap, require x and group as axes and use y as value
        if not x or not group or not y:
            raise BadRequest('x, y and group required for heatmap (x axis = x, y axis = group, cell = y)')
        piv = pd.pivot_table(df, values=y, index=group, columns=x, aggfunc='sum', fill_value=0)
        traces.append({'type': 'heatmap', 'z': piv.values.tolist(), 'x': piv.columns.astype(str).tolist(), 'y': piv.index.astype(str).tolist(), 'colorscale': 'Viridis'})
        layout['xaxis'] = {'title': x}
        layout['yaxis'] = {'title': group}

    else:
        raise BadRequest('Unsupported chart type')

    return {'data': traces, 'layout': layout, 'config': config}


@app.route('/chart', methods=['POST'])
def chart():
    if dataframe is None:
        return jsonify({'error': 'No data loaded'}), 400
    try:
        payload = request.get_json(force=True)
        chart_type = payload.get('chart_type', 'line')
        x = payload.get('x')
        y = payload.get('y')
        group = payload.get('group')
        cfg = build_plotly_config(dataframe, chart_type, x, y, group)
        return jsonify(cfg)
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as ex:
        logger.exception('Chart build failed')
        return jsonify({'error': str(ex)}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', '8000'))
    app.run(host='0.0.0.0', port=port)
