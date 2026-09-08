# FP&A Monitor App

**Financial Planning & Analysis metric monitoring with anomaly detection and automated insights.** Helps finance teams watch key metrics, catch unusual movements early, and turn them into actionable recommendations.

## Features

- **Automated metric monitoring** — revenue, expenses, profit margins, cash flow, AP/AR days
- **Anomaly detection** — statistical analysis using z-scores
- **Automated insights** — generated, plain-language recommendations
- **Flexible configuration** — tune thresholds via environment variables
- **Comprehensive logging** — every analysis run is traceable
- **JSON export** — detailed results for downstream use

## Getting started

```bash
pip install -r requirements.txt
python -m app   # entry point may vary — see the source
```

Configure metric thresholds and data sources via environment variables.

## Status

Complete — built for finance-team metric monitoring.

---

Built by [João Caldas](https://github.com/joaoccaldas).
