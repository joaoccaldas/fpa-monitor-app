import os
import io
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
import numpy as np
import pandas as pd
from flask import Flask, render_template, jsonify, request, send_file, session
from werkzeug.exceptions import RequestEntityTooLarge, BadRequest
from openai import OpenAI

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

# LLM Configuration
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'perplexity')  # 'perplexity', 'ollama', 'openai'
LLM_API_KEY = os.getenv('LLM_API_KEY', '')
LLM_BASE_URL = os.getenv('LLM_BASE_URL', 'https://api.perplexity.ai')  # For Perplexity or Ollama
LLM_MODEL = os.getenv('LLM_MODEL', 'llama-3.1-sonar-small-128k-online')  # Default Perplexity model

# Initialize chat history storage (in-memory for simplicity; use Redis/DB for production)
chat_sessions: Dict[str, List[Dict[str, str]]] = {}

def get_llm_client():
    """Initialize LLM client based on provider configuration."""
    if LLM_PROVIDER == 'ollama':
        return OpenAI(base_url=os.getenv('LLM_BASE_URL', 'http://localhost:11434/v1'), api_key='ollama')
    elif LLM_PROVIDER == 'perplexity':
        return OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    else:  # openai or compatible
        return OpenAI(api_key=LLM_API_KEY)

def allowed_file(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXT

def load_to_df(path: str) -> pd.DataFrame:
    ext = os.path.splitext(path.lower())[1]
    if ext == '.csv':
        return pd.read_csv(path)
    elif ext in {'.xls', '.xlsx'}:
        return pd.read_excel(path)
    elif ext == '.json':
        return pd.read_json(path)
    else:
        raise BadRequest('Unsupported file extension')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    global dataframe
    if 'file' not in request.files:
        return jsonify({'error': 'No file in request'}), 400
    f = request.files['file']
    if f.filename == '' or not allowed_file(f.filename):
        return jsonify({'error': 'Invalid or unsupported file'}), 400
    try:
        fpath = os.path.join(UPLOAD_FOLDER, f.filename)
        f.save(fpath)
        dataframe = load_to_df(fpath)
        logger.info(f'Loaded {len(dataframe)} rows, {len(dataframe.columns)} cols')
        return jsonify({'message': f'File uploaded ({len(dataframe)} rows, {len(dataframe.columns)} columns)', 'columns': dataframe.columns.tolist()}), 200
    except Exception as ex:
        logger.exception('Upload/load failed')
        return jsonify({'error': str(ex)}), 500

@app.route('/info', methods=['GET'])
def info():
    if dataframe is None:
        return jsonify({'error': 'No data loaded'}), 400
    info_dict = {
        'shape': dataframe.shape,
        'columns': dataframe.columns.tolist(),
        'dtypes': {c: str(dataframe[c].dtype) for c in dataframe.columns},
        'missing': dataframe.isnull().sum().to_dict(),
        'head': dataframe.head().to_dict('records')
    }
    return jsonify(info_dict)

@app.route('/download', methods=['GET'])
def download():
    if dataframe is None:
        return jsonify({'error': 'No data loaded'}), 400
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as writer:
        dataframe.to_excel(writer, sheet_name='data', index=False)
    out.seek(0)
    return send_file(out, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='data.xlsx')

def build_plotly_config(df: pd.DataFrame, chart_type: str, x: str = None, y: str = None, group: str = None) -> dict:
    traces = []
    layout = {'title': chart_type.replace('_', ' ').title(), 'hovermode': 'closest'}
    config = {'responsive': True}
    if chart_type in {'line', 'bar', 'scatter', 'area', 'stacked_bar'}:
        if not x or not y:
            raise BadRequest('x and y required for line/bar/scatter')
        if group:
            dfx = df[[x, y, group]].dropna()
            for grp_val in dfx[group].unique():
                subset = dfx[dfx[group] == grp_val]
                if chart_type in {'bar', 'stacked_bar'}:
                    traces.append({'type': 'bar', 'name': str(grp_val), 'x': subset[x].astype(str).tolist(), 'y': subset[y].tolist()})
                else:
                    mode = 'lines' if chart_type in {'line', 'area'} else 'markers'
                    tr = {'type': 'scatter', 'mode': mode, 'name': str(grp_val), 'x': subset[x].astype(str).tolist(), 'y': subset[y].tolist()}
                    if chart_type == 'area':
                        tr['fill'] = 'tozeroy'
                    traces.append(tr)
            if chart_type == 'stacked_bar':
                layout['barmode'] = 'stack'
        else:
            dfx = df[[x, y]].dropna()
            y_list = [y] if isinstance(y, str) else y
            for y_col in y_list:
                if y_col not in dfx.columns:
                    continue
                if chart_type in {'bar', 'stacked_bar'}:
                    traces.append({'type': 'bar', 'name': y_col, 'x': dfx[x].astype(str).tolist(), 'y': dfx[y_col].tolist()})
                else:
                    mode = 'lines' if chart_type in {'line', 'area'} else 'markers'
                    tr = {'type': 'scatter', 'mode': mode, 'name': y_col, 'x': dfx[x].astype(str).tolist(), 'y': dfx[y_col].tolist()}
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

@app.route('/chatbot', methods=['POST'])
def chatbot():
    """Universal chatbot endpoint that handles any query using LLM."""
    try:
        payload = request.get_json(force=True)
        user_message = payload.get('message', '').strip()
        session_id = payload.get('session_id', 'default')
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Initialize session if doesn't exist
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []
        
        # Add user message to history
        chat_sessions[session_id].append({'role': 'user', 'content': user_message})
        
        # Prepare system prompt with FP&A context
        system_prompt = {
            'role': 'system',
            'content': '''You are PingPong AI, an intelligent assistant integrated into a Finance & FP&A dashboard application. 
            You can help with:
            1. General conversation and questions on any topic
            2. Financial analysis, FP&A best practices, and business advice
            3. Data insights when users upload financial data
            4. Excel formulas, financial modeling, budgeting, forecasting
            
            Be professional, concise, and helpful. When discussing finance topics, provide actionable insights.
            If asked about the loaded data and no data context is provided, mention that users can upload data files for analysis.'''
        }
        
        # Add data context if available
        data_context = ''
        if dataframe is not None:
            data_context = f"\n\nCurrent dataset loaded: {dataframe.shape[0]} rows, {dataframe.shape[1]} columns. Columns: {', '.join(dataframe.columns.tolist()[:10])}{'...' if len(dataframe.columns) > 10 else ''}"
            system_prompt['content'] += data_context
        
        # Prepare messages for LLM (keep last 10 messages for context)
        messages = [system_prompt] + chat_sessions[session_id][-10:]
        
        # Call LLM
        try:
            client = get_llm_client()
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=800
            )
            
            assistant_message = response.choices[0].message.content
            
            # Add assistant response to history
            chat_sessions[session_id].append({'role': 'assistant', 'content': assistant_message})
            
            return jsonify({
                'reply': assistant_message,
                'session_id': session_id
            }), 200
            
        except Exception as llm_error:
            logger.exception('LLM call failed')
            # Fallback response
            fallback_msg = f"I'm currently unable to connect to the AI service. Error: {str(llm_error)[:100]}. Please check your LLM configuration (API key, base URL, model name)."
            return jsonify({'reply': fallback_msg, 'session_id': session_id}), 200
            
    except Exception as ex:
        logger.exception('Chatbot endpoint failed')
        return jsonify({'error': str(ex)}), 500

@app.route('/chatbot/clear', methods=['POST'])
def clear_chat():
    """Clear chat history for a session."""
    try:
        payload = request.get_json(force=True)
        session_id = payload.get('session_id', 'default')
        
        if session_id in chat_sessions:
            chat_sessions[session_id] = []
        
        return jsonify({'message': 'Chat history cleared'}), 200
    except Exception as ex:
        return jsonify({'error': str(ex)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', '8000'))
    app.run(host='0.0.0.0', port=port)
