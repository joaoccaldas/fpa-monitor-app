# FP&A Monitor App (PingPong)
Comprehensive FP&A dashboard with universal AI chatbot, interactive Plotly visualizations, KPI alerting, and enterprise-grade finance analytics.

## 🔔 Alerts Management Dashboard
Create and manage KPI alerts from a dedicated UI.
- Add, edit, enable/disable, and delete alerts
- Choose KPI (cpu_usage, memory_usage, disk_usage, response_time), operator (> >= < <=), and threshold
- Select notification channel (email, slack, webhook)
- View recent alert history and statuses

Routes:
- Page: GET /alerts
- API: GET/POST /api/alerts
- API: GET/PUT/DELETE /api/alerts/<id>
- API: POST /api/alerts/<id>/toggle {enabled: bool}
- API: GET /api/alerts/history?limit=N

Quick start:
1) Open /alerts to manage alerts
2) Create a new alert and set threshold
3) Use your data pipeline/monitor to evaluate KPIs and call your notifier (see alerts.py)
4) When a condition triggers, notifications are sent and history is recorded

Configuration:
- Set SECRET_KEY and any notification credentials (e.g., Slack webhook) via environment
- See alerts.py for backend logic and extend to your infra

## 🤖 Universal AI Chatbot
Fully deployed conversational AI assistant that:
- Answers questions about your uploaded financial data with natural language queries
- Provides general assistance and conversations on any topic
- Offers contextual help for dashboard features and FP&A best practices
- Integrates seamlessly with data exploration workflows

**Access:** Click the chatbot icon in the bottom-right corner of any dashboard page.

## 📊 Advanced Plotly Finance Analytics
Interactive visualization suite with:
- **Chart types:** line, area, bar, stacked_bar, pie, scatter, heatmap
- **Controls:** select X, Y, and group-by fields; toggle drilldown; add multiple panels
- **Exports:** download data as CSV; export charts as PNG or SVG
- **Sample data:** one-click sample dataset to explore features
- **Debug console:** raw JSON inspection for troubleshooting

## 🏗️ System Architecture
### Backend (Flask)
- **app.py:** Main application server handling uploads, metadata inference, Plotly config generation, alerts routes
- **Data processing:** Supports CSV, XLS, XLSX, JSON formats
- **API layer:** RESTful endpoints for upload, chart building, export, chatbot, and alerts

### Frontend (HTML/JS)
- **Interactive dashboard:** Responsive UI with real-time chart rendering
- **Alerts dashboard:** CRUD UI for KPI alerts with Bootstrap 5
- **Chatbot widget:** Embedded conversational interface
- **Export tools:** Client-side PNG/SVG generation and CSV download

### AI/ML Layer
- **Universal chatbot:** LLM-powered assistant for data queries and general conversation
- **Context awareness:** Maintains session state and dataset context

## 🚀 Usage
1. Open the web dashboard and click **Sample** to download a sample CSV
2. Upload your dataset (CSV/XLS/XLSX/JSON)
3. Select **Chart type**, **X**, **Y**, and optional **Group by**
4. Click **Build chart** to render; **Add panel** to create additional chart tiles
5. Use **PNG/SVG** buttons on each panel to export images; **Export CSV** to download full dataset
6. Click the **chatbot icon** to ask questions about your data or get help
7. Go to **/alerts** to manage KPI alerts
