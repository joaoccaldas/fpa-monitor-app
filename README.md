# FP&A Monitor App

FP&A metric monitoring application with anomaly detection and automated insights. This tool helps financial planning and analysis teams monitor key metrics, detect unusual patterns, and receive actionable recommendations.

## Features

- **Automated Metric Monitoring**: Track revenue, expenses, profit margins, cash flow, and AR/AP days
- **Anomaly Detection**: Statistical analysis using z-scores to identify unusual patterns
- **Automated Insights**: Generate actionable recommendations based on detected anomalies and trends
- **Flexible Configuration**: Customize thresholds and monitoring parameters via environment variables
- **Comprehensive Logging**: Track all analysis runs and detected anomalies
- **JSON Export**: Export detailed results for further analysis or integration

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/joaoccaldas/fpa-monitor-app.git
   cd fpa-monitor-app
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

## Configuration

Edit the `.env` file to customize the application settings:

```bash
# Anomaly Detection Settings
ANOMALY_THRESHOLD=2.5      # Z-score threshold for anomaly detection
LOOKBACK_DAYS=30           # Number of days to analyze

# Alert Configuration
ALERT_EMAIL=your-email@example.com

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=fpa_monitor.log
```

## Usage

### Manual CLI Usage

Run the monitor with default settings (30 days):
```bash
python monitor.py
```

Analyze a custom time period:
```bash
python monitor.py --days 60
```

Specify a custom output file:
```bash
python monitor.py --days 90 --output results_q1.json
```

Use a custom configuration file:
```bash
python monitor.py --config my_config.json
```

### Command-line Options

- `--days`: Number of days to analyze (default: 30)
- `--output`: Output file path (default: fpa_insights.json)
- `--config`: Path to custom configuration file

### Example Output

```
============================================================
FP&A MONITORING REPORT
============================================================

Period: 2025-09-09 to 2025-10-09

Anomalies Detected: 3

Top Anomalies:
  - 2025-10-05: revenue = 125000.00 (Z-score: 3.45, Severity: HIGH)
  - 2025-10-03: cash_flow = 8000.00 (Z-score: 3.12, Severity: HIGH)
  - 2025-09-28: expenses = 85000.00 (Z-score: 2.67, Severity: MEDIUM)

Recommendations:
  1. Revenue is declining. Review sales pipeline and pricing strategy.
  2. Cash flow is declining. Review AR/AP and working capital management.
  3. Accounts receivable days above target. Implement stricter collection policies.

============================================================

Detailed results saved to fpa_insights.json
```

## Deployment

### Option 1: Scheduled Execution with Cron (Linux/macOS)

1. **Make the script executable**:
   ```bash
   chmod +x monitor.py
   ```

2. **Open crontab editor**:
   ```bash
   crontab -e
   ```

3. **Add a scheduled task**:
   
   Run daily at 8 AM:
   ```cron
   0 8 * * * cd /path/to/fpa-monitor-app && /path/to/venv/bin/python monitor.py >> /path/to/logs/monitor.log 2>&1
   ```
   
   Run every Monday at 9 AM:
   ```cron
   0 9 * * 1 cd /path/to/fpa-monitor-app && /path/to/venv/bin/python monitor.py --days 7
   ```
   
   Run on the 1st of every month at 7 AM:
   ```cron
   0 7 1 * * cd /path/to/fpa-monitor-app && /path/to/venv/bin/python monitor.py --days 30 --output monthly_report.json
   ```

### Option 2: Scheduled Execution with Task Scheduler (Windows)

1. **Open Task Scheduler** and click "Create Basic Task"
2. **Set the name** (e.g., "FP&A Monitor")
3. **Choose trigger** (Daily, Weekly, Monthly, etc.)
4. **Set action** to "Start a program"
5. **Program/script**: `C:\path\to\venv\Scripts\python.exe`
6. **Add arguments**: `monitor.py --days 30`
7. **Start in**: `C:\path\to\fpa-monitor-app`

### Option 3: GitHub Actions (Automated Cloud Execution)

Create `.github/workflows/monitor.yml` in your repository:

```yaml
name: FP&A Monitor

on:
  schedule:
    # Run daily at 8 AM UTC
    - cron: '0 8 * * *'
  workflow_dispatch:  # Allow manual trigger

jobs:
  monitor:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run FP&A monitor
      env:
        ANOMALY_THRESHOLD: ${{ secrets.ANOMALY_THRESHOLD }}
        LOOKBACK_DAYS: ${{ secrets.LOOKBACK_DAYS }}
        ALERT_EMAIL: ${{ secrets.ALERT_EMAIL }}
      run: |
        python monitor.py --days 30 --output fpa_insights.json
    
    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: fpa-insights
        path: fpa_insights.json
        retention-days: 30
```

**To use GitHub Actions**:
1. Create the workflow file in `.github/workflows/`
2. Add secrets in repository Settings → Secrets and variables → Actions:
   - `ANOMALY_THRESHOLD`
   - `LOOKBACK_DAYS`
   - `ALERT_EMAIL`
3. The workflow will run automatically on schedule or can be triggered manually from the Actions tab

### Option 4: Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "monitor.py"]
```

**Build and run**:
```bash
docker build -t fpa-monitor .
docker run --env-file .env fpa-monitor
```

**With docker-compose** (create `docker-compose.yml`):
```yaml
version: '3.8'

services:
  monitor:
    build: .
    env_file: .env
    volumes:
      - ./data:/app/data
```

Run with:
```bash
docker-compose up
```

## Data Integration

The current implementation uses sample data. To integrate with your actual data sources:

1. **Modify the `fetch_metrics()` method** in `monitor.py`
2. **Add database or API connections** as needed
3. **Update the `.env` file** with connection credentials

Example integration patterns:

```python
# Database integration
import psycopg2

def fetch_metrics(self, start_date, end_date):
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    # Fetch data from your database
    
# API integration
import requests

def fetch_metrics(self, start_date, end_date):
    response = requests.get(
        os.getenv('API_ENDPOINT'),
        headers={'Authorization': f"Bearer {os.getenv('API_KEY')}"}
    )
    return response.json()
```

## Output Files

- **fpa_insights.json**: Detailed analysis results including summary statistics, anomalies, and recommendations
- **fpa_monitor.log**: Application logs with timestamps and analysis details

## Customization

### Metrics

Add or modify tracked metrics by editing the `config['metrics']` list in `monitor.py`:

```python
'metrics': [
    'revenue',
    'expenses',
    'profit_margin',
    'cash_flow',
    'ar_days',
    'ap_days',
    'customer_acquisition_cost',  # Add custom metrics
    'customer_lifetime_value'
]
```

### Thresholds

Adjust anomaly detection sensitivity:
- **Lower threshold** (e.g., 2.0): More sensitive, detects more anomalies
- **Higher threshold** (e.g., 3.0): Less sensitive, only flags significant anomalies

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure all dependencies are installed: `pip install -r requirements.txt`
2. **Permission errors**: Make script executable: `chmod +x monitor.py`
3. **No data**: Check that date ranges and data sources are configured correctly
4. **Environment variables not loaded**: Ensure `.env` file exists and is properly formatted

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

## Roadmap

- [ ] Email notifications for critical anomalies
- [ ] Web dashboard for visualizing insights
- [ ] Machine learning-based anomaly detection
- [ ] Integration with popular accounting software (QuickBooks, Xero, etc.)
- [ ] Multi-currency support
- [ ] Historical trend analysis and forecasting
