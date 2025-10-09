# FP&A Monitor App

PingPong — Minimal FP&A dashboard for uploading data, exploring metrics, and building interactive Plotly visualizations.

## New: Advanced Visualizations (Step 5)
This release adds interactive Plotly charts, dashboard controls, drilldown toggle, and export options.

- Chart types: line, area, bar, stacked_bar, pie, scatter, heatmap
- Controls: select X, Y, and optional group-by fields; toggle drilldown; add multiple panels
- Exports: download data as CSV; export charts as PNG or SVG
- Sample data: one-click sample dataset to try the charts
- Debug console: see raw JSON for troubleshooting

## Frontend Usage
1) Open the web dashboard and click Sample to download a sample CSV.
2) Upload your dataset (CSV/XLS/XLSX/JSON).
3) Select Chart type, X, Y, and optional Group by.
4) Click Build chart to render; Add panel to create additional chart tiles.
5) Use PNG/SVG buttons on each panel to export images; use Export CSV to download full dataset.

## API Endpoints
- GET /                -> Render dashboard (templates/index.html)
- POST /upload         -> Multipart form upload of file under key `file`.
  - Returns: { status, meta: { rows, fields: [{name, type}] } }
  - Errors: 400 on bad input, 413 on large file, 500 on server error
- GET /meta            -> { rows, fields } for currently loaded dataset
- POST /chart          -> Build Plotly config for chart
  - Body: { chart_type, x, y, group? }
  - Returns: { data, layout, config } (Plotly JSON)
- GET /export/csv      -> Download current dataset as CSV
- GET /sample          -> Download a synthetic FP&A-like sample CSV

## Backend Implementation Notes
- app.py handles upload (CSV/XLS/XLSX/JSON), metadata inference, and Plotly config generation.
- build_plotly_config supports line/area/bar/stacked_bar/pie/heatmap/scatter with optional group series.
- Errors are returned as JSON with appropriate status codes for easier debugging in the UI.

## Requirements
Ensure these packages are installed (requirements.txt):
- Flask
- pandas
- numpy
- openpyxl (for .xlsx)
- xlrd (for .xls)

## Local Development
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export FLASK_APP=app.py
export FLASK_ENV=development
flask run -p 8000
```
Open http://localhost:8000 and test upload + charts.

## Deployment (Render)
- Set Build Command to: pip install -r requirements.txt
- Set Start Command to: gunicorn app:app --bind 0.0.0.0:$PORT
- Environment: Python 3.11+, set SECRET_KEY
- Increase instance memory if handling large files; set MAX_CONTENT_LENGTH as needed.

## Troubleshooting
- 500/502 on /upload: verify allowed file types and size limits; check server logs.
- Empty fields: ensure dataset has headers and correct data types; the app infers numeric vs. categorical.
- Charts not rendering: check /chart response in Debug console; ensure x/y fields exist.
- Large XLSX: install openpyxl; for legacy XLS, install xlrd.
