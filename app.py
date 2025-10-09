import os
import io
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd
import requests
from flask import Flask, render_template, jsonify, request, session, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge, BadRequest

from monitor import MetricMonitor

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
# 16MB max file size
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Logging (avoid sensitive data)
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# Allowed file extensions and MIME types
ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx'}
ALLOWED_MIME_TYPES = {
    'text/csv',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
}

# Session data constraints
SESSION_MAX_ROWS = int(os.getenv('SESSION_MAX_ROWS', '200000'))  # cap rows stored in session
SESSION_MAX_COLS = int(os.getenv('SESSION_MAX_COLS', '200'))     # cap columns stored in session


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def infer_mime(file_storage) -> Optional[str]:
    # Prefer browser-provided mimetype but constrain against our allowlist
    mt = (file_storage.mimetype or '').split(';')[0].strip().lower()
    return mt if mt in ALLOWED_MIME_TYPES else None


def safe_read_dataframe(file_storage) -> pd.DataFrame:
    """Read CSV/XLS/XLSX into a DataFrame with robust handling."""
    filename = file_storage.filename or ''
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    # Read stream once into BytesIO to allow re-reads
    file_bytes = file_storage.stream.read()
    if not file_bytes:
        raise BadRequest('Uploaded file is empty.')

    # Enforce a soft file size limit in addition to MAX_CONTENT_LENGTH
    max_soft_size = int(os.getenv('UPLOAD_SOFT_LIMIT', 12 * 1024 * 1024))
    if len(file_bytes) > max_soft_size:
        raise BadRequest(f'File too large. Soft limit is {max_soft_size // (1024*1024)}MB.')

    bio = io.BytesIO(file_bytes)

    if ext == 'csv':
        # Try utf-8 first, then common fallbacks
        for enc in ('utf-8', 'utf-8-sig', 'latin1'):
            bio.seek(0)
            try:
                return pd.read_csv(bio, encoding=enc)
            except Exception as e:
                last_err = e
        raise BadRequest(f'Failed to parse CSV. Last error: {last_err}')

    if ext in ('xls', 'xlsx'):
        bio.seek(0)
        try:
            # engine auto
            return pd.read_excel(bio)
        except ImportError as e:
            raise BadRequest('Excel support requires openpyxl/xlrd. Please install dependencies.')
        except ValueError as e:
            # Often raised by engine/version mismatches
            raise BadRequest(f'Failed to parse Excel: {e}')
        except Exception as e:
            raise BadRequest(f'Unknown Excel parsing error: {e}')

    raise BadRequest('Unsupported file extension.')


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # Basic sanitation: drop completely empty columns/rows, clip size
    df = df.dropna(how='all').dropna(axis=1, how='all')
    # Limit size to prevent session bloat
    if df.shape[0] > SESSION_MAX_ROWS:
        df = df.iloc[:SESSION_MAX_ROWS, :]
    if df.shape[1] > SESSION_MAX_COLS:
        df = df.iloc[:, :SESSION_MAX_COLS]
    return df


@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(e):
    return jsonify({
        'success': False,
        'error': 'File too large',
        'detail': f'MAX_CONTENT_LENGTH={app.config["MAX_CONTENT_LENGTH"]} bytes'
    }), 413


@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'file' not in request.files:
            logger.warning('Upload attempt without file part')
            return jsonify({'success': False, 'error': 'No file part in request.'}), 400

        file = request.files['file']
        if file.filename == '':
            logger.warning('Upload attempt with empty filename')
            return jsonify({'success': False, 'error': 'No file selected.'}), 400

        if not allowed_file(file.filename):
            logger.warning('Disallowed extension: %s', file.filename)
            return jsonify({'success': False, 'error': 'Unsupported file type. Allowed: csv, xls, xlsx'}), 400

        # MIME type validation (advisory)
        mime = infer_mime(file)
        if mime is None:
            logger.info('Unrecognized MIME for %s; proceeding by extension only', file.filename)

        # Secure filename for any optional persistence
        filename = secure_filename(file.filename)

        # Read dataframe robustly
        df = safe_read_dataframe(file)
        if df is None or df.empty:
            return jsonify({'success': False, 'error': 'No data found in file.'}), 400

        df = clean_dataframe(df)

        # Validate resulting dataframe
        if df.empty:
            return jsonify({'success': False, 'error': 'File contains no usable data after cleaning.'}), 400

        # Store a lightweight representation in session (avoid heavy blobs)
        preview_rows = int(os.getenv('PREVIEW_ROWS', '200'))
        sample = df.head(preview_rows)
        data = {
            'columns': list(map(str, sample.columns.tolist())),
            'rows': sample.astype(object).where(pd.notna(sample), None).values.tolist(),
            'shape': [int(df.shape[0]), int(df.shape[1])]
        }
        session['uploaded_preview'] = data
        session['uploaded_at'] = datetime.utcnow().isoformat()
        session['uploaded_filename'] = filename

        logger.info('Upload processed: file=%s shape=%s', filename, df.shape)

        return jsonify({
            'success': True,
            'filename': filename,
            'mime': mime,
            'shape': data['shape'],
            'preview_rows': len(data['rows'])
        }), 200

    except BadRequest as e:
        # Raised when we deliberately reject the input
        logger.warning('BadRequest on upload: %s', e)
        return jsonify({'success': False, 'error': str(e)}), 400
    except RequestEntityTooLarge as e:
        logger.warning('RequestEntityTooLarge: %s', e)
        return jsonify({'success': False, 'error': 'File too large.'}), 413
    except Exception as e:
        # Catch-all with debug correlation id
        corr = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        logger.exception('Unhandled error in /upload corr=%s', corr)
        return jsonify({
            'success': False,
            'error': 'Internal server error while processing file.',
            'correlation_id': corr
        }), 500


# Existing endpoints below (kept unchanged where possible)
# ... other routes ...

# Static uploads (optional, if front-end needs to download back)
@app.route('/uploads/<path:filename>')
def get_upload(filename: str):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development')
