# FP&A Monitor App

Statistical financial monitoring prototype. Use `python monitor.py --input /private/observations.json --days 30` for a JSON array of dated observations. Synthetic generation is opt-in using `--demo`; it is never a live feed. Missing metric rows retain their original dates during anomaly scoring. Invalid numeric observations are rejected.

Each observation contains an ISO `date` and financial metrics such as revenue, expenses, profit_margin, cash_flow, ar_days and ap_days. Run `python -m unittest discover -v`.

Commercial gaps: a provider connector, causal out-of-sample anomaly baselines, configurable currency/units, customer onboarding, scheduling, authentication and persistence. Whole-window z-scores describe the sample; they are not predictive anomaly detection. No employer deployment or business impact is asserted.
