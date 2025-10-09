# FP&A Monitor App (PingPong)
Comprehensive FP&A dashboard with universal AI chatbot, interactive Plotly visualizations, and enterprise-grade finance analytics.

## 🤖 Universal AI Chatbot
Fully deployed conversational AI assistant that:
- Answers questions about your uploaded financial data with natural language queries
- Provides general assistance and conversations on any topic
- Offers contextual help for dashboard features and FP&A best practices
- Integrates seamlessly with data exploration workflows

**Access:** Click the chatbot icon in the bottom-right corner of any dashboard page.

## 📊 Advanced Plotly Finance Analytics
Interactive visualization suite with:
- **Chart types:** line, area, bar, stacked_bar, pie, scatter, heatmap, waterfall
- **Controls:** select X, Y, and group-by fields; toggle drilldown; add multiple panels
- **Exports:** download data as CSV; export charts as PNG or SVG
- **Sample data:** one-click sample dataset to explore features
- **Debug console:** raw JSON inspection for troubleshooting

## 🏗️ System Architecture

### Backend (Flask)
- **app.py:** Main application server handling uploads, metadata inference, Plotly config generation
- **Data processing:** Supports CSV, XLS, XLSX, JSON formats
- **API layer:** RESTful endpoints for upload, chart building, export, and chatbot integration

### Frontend (HTML/JS)
- **Interactive dashboard:** Responsive UI with real-time chart rendering
- **Chatbot widget:** Embedded conversational interface
- **Export tools:** Client-side PNG/SVG generation and CSV download

### AI/ML Layer
- **Universal chatbot:** LLM-powered assistant for data queries and general conversation
- **Context awareness:** Maintains session state and dataset context

## 🚀 Frontend Usage
1. Open the web dashboard and click **Sample** to download a sample CSV
2. Upload your dataset (CSV/XLS/XLSX/JSON)
3. Select **Chart type**, **X**, **Y**, and optional **Group by**
4. Click **Build chart** to render; **Add panel** to create additional chart tiles
5. Use **PNG/SVG** buttons on each panel to export images; **Export CSV** to download full dataset
6. Click the **chatbot icon** to ask questions about your data or get help

## 🔌 API Endpoints
- `GET /` → Render dashboard (templates/index.html)
- `POST /upload` → Multipart form upload of file under key `file`
  - Returns: `{ status, meta: { rows, fields: [{name, type}] } }`
  - Errors: 400 on bad input, 413 on large file, 500 on server error
- `GET /meta` → `{ rows, fields }` for currently loaded dataset
- `POST /chart` → Build Plotly config for chart
  - Body: `{ chart_type, x, y, group? }`
  - Returns: `{ data, layout, config }` (Plotly JSON)
- `GET /export/csv` → Download current dataset as CSV
- `GET /sample` → Download synthetic FP&A-like sample CSV
- `POST /chatbot` → Send message to AI assistant
  - Body: `{ message, context? }`
  - Returns: `{ response, timestamp }`

## 📋 Roadmap: Next-Generation FP&A Tools Integration

### Phase 1: Top Missing FP&A Tools (Research-Backed)
Based on industry analysis from Cube, Mosaic, SAP S/4HANA, and finance professional communities:

#### 1. **Real-Time KPI Alerts & Monitoring**
- Automated threshold alerts for variance detection
- Slack/Teams/email notifications for critical metrics
- Custom alert rules per user role

#### 2. **Advanced Scenario Planning & What-If Analysis**
- Multi-scenario modeling (best/worst/likely cases)
- Sensitivity analysis with adjustable drivers
- Version control for forecast iterations
- Scenario comparison dashboards

#### 3. **Automated Consolidation & Multi-Entity Reporting**
- Inter-company eliminations
- Currency translation (FX rate management)
- Roll-up hierarchies (BU/region/global)
- Audit trails for compliance

#### 4. **Workflow Automation & Approval Chains**
- Budget submission and approval workflows
- Automated month-end close checklists
- Task assignment and tracking
- Integration with ERP systems (SAP, Oracle, NetSuite)

#### 5. **AI-Powered Variance Explanation & Commentary**
- Automated variance analysis with natural language explanations
- Root cause identification using ML
- Automated commentary generation for executive reports
- Trend prediction and anomaly detection

### Phase 2: Implementation Plan

#### Sprint 1: Real-Time KPI Alerts (Weeks 1-2)
**User Stories:**
- As a Finance Manager, I want to set thresholds for key metrics so I'm notified when variances exceed limits
- As a CFO, I want to receive daily digest emails of critical KPI changes

**Technical Tasks:**
- [ ] Build alert configuration UI (threshold, metric, channel)
- [ ] Implement background job scheduler (Celery/APScheduler)
- [ ] Integrate notification APIs (SendGrid, Slack SDK)
- [ ] Create alert history log and management dashboard
- [ ] Deploy with Redis for job queue
- [ ] Test: Create alert, trigger threshold, verify notification

#### Sprint 2: Scenario Planning Engine (Weeks 3-5)
**User Stories:**
- As an FP&A Analyst, I want to create 3 forecast scenarios and compare them side-by-side
- As a Business Unit Leader, I want to adjust revenue assumptions and see P&L impact instantly

**Technical Tasks:**
- [ ] Design scenario data model (versions, assumptions, outputs)
- [ ] Build scenario creation and cloning UI
- [ ] Implement driver-based calculation engine
- [ ] Create scenario comparison visualizations
- [ ] Add scenario export to Excel with formatting
- [ ] Deploy with PostgreSQL for scenario storage
- [ ] Test: Create scenarios, adjust drivers, verify calculations

#### Sprint 3: Consolidation & Multi-Entity (Weeks 6-8)
**User Stories:**
- As a Corporate Controller, I want to consolidate 5 subsidiaries with automated eliminations
- As a Treasury Manager, I want to apply monthly FX rates across entities automatically

**Technical Tasks:**
- [ ] Build entity hierarchy configuration UI
- [ ] Implement elimination rules engine
- [ ] Integrate FX rate API (e.g., exchangerate-api.io)
- [ ] Create consolidation worksheet with drill-through
- [ ] Add audit log for all consolidation adjustments
- [ ] Deploy with entity relationship database
- [ ] Test: Set up 3-entity consolidation, verify eliminations

#### Sprint 4: Workflow Automation (Weeks 9-11)
**User Stories:**
- As a Department Head, I want to submit my budget through an approval workflow
- As a Finance Team Lead, I want to track month-end close tasks with automated reminders

**Technical Tasks:**
- [ ] Design workflow builder UI (drag-drop states)
- [ ] Implement approval routing logic
- [ ] Build task assignment and notification system
- [ ] Create workflow status dashboard
- [ ] Add ERP integration layer (REST/SOAP connectors)
- [ ] Deploy with workflow state machine
- [ ] Test: Create budget approval workflow, test all states

#### Sprint 5: AI Variance Explanation (Weeks 12-14)
**User Stories:**
- As an FP&A Director, I want automated variance commentary for my board deck
- As an Analyst, I want to understand why revenue is down 8% with AI-suggested drivers

**Technical Tasks:**
- [ ] Train/fine-tune ML model on financial variance patterns
- [ ] Build variance analysis API endpoint
- [ ] Implement commentary generation with LLM
- [ ] Create variance explanation UI with drill-down
- [ ] Add anomaly detection algorithm
- [ ] Deploy with ML model serving infrastructure
- [ ] Test: Run variance analysis on sample data, validate explanations

### Phase 3: User Onboarding Flows

#### Finance Team Onboarding
1. **Welcome & Setup** (Day 1)
   - Account creation and role assignment
   - Upload first dataset (guided wizard)
   - Create first dashboard with 3 charts
   - Set up 2 KPI alerts

2. **Core Workflows** (Week 1)
   - Build scenario planning model
   - Configure consolidation hierarchy
   - Set up budget workflow
   - Schedule automated reports

3. **Advanced Features** (Week 2)
   - Train chatbot on company-specific data
   - Create custom KPI formulas
   - Set up ERP integration
   - Configure user permissions and data access

#### Senior Leadership Reporting Flow
1. **Executive Dashboard Access**
   - Single sign-on (SSO) integration
   - Mobile-responsive executive summary view
   - Key metrics at-a-glance (revenue, EBITDA, cash, headcount)

2. **Interactive Exploration**
   - One-click drill-down from summary to detail
   - Natural language queries via chatbot ("Why is margin down?")
   - Scenario comparison toggle

3. **Export & Presentation**
   - Download board deck with auto-generated commentary
   - Export to PowerPoint with branded templates
   - Schedule automated distribution

### Phase 4: Testing & Quality Assurance

**Per Feature:**
- Unit tests for all API endpoints
- Integration tests for data pipelines
- UI/UX testing with finance user personas
- Performance testing with large datasets (1M+ rows)
- Security audit (authentication, authorization, data encryption)

**System-Wide:**
- End-to-end workflow testing
- Load testing (concurrent users)
- Disaster recovery and backup validation
- Accessibility compliance (WCAG 2.1)

## 💻 Local Development
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

## 📦 Requirements
Core dependencies (requirements.txt):
- Flask
- pandas
- numpy
- openpyxl (for .xlsx)
- xlrd (for .xls)
- plotly
- openai / anthropic (for chatbot)
- celery (for background jobs)
- redis (for task queue)
- psycopg2 (for PostgreSQL)
- requests (for API integrations)

## 🔐 Security & Compliance
- Role-based access control (RBAC)
- Data encryption at rest and in transit
- Audit logging for all data changes
- GDPR/SOX compliance features
- Regular security updates and patches

## 📞 Support
For questions, feature requests, or bug reports:
- Use the in-app chatbot for immediate assistance
- Submit issues on GitHub
- Contact: support@pingpong-fpa.com

---

**Version:** 2.0.0 (Chatbot + Finance Tools Roadmap)
**Last Updated:** October 2025
**License:** MIT
