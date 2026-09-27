# FP&A Monitor App

A personal reference project for exploring financial metric monitoring, anomaly detection, and automated finance insights.

## What it explores

- configurable FP&A metrics such as revenue, expenses, margin, cash flow, AR days and AP days;
- statistical anomaly detection;
- configurable thresholds and lookback periods;
- structured logging and JSON-style outputs;
- a path toward reusable finance-monitoring components.

The current data generator is synthetic. Public examples and fixtures must not contain employer, client, family, or other private production data.

## Technology

- Python
- NumPy
- pandas / SciPy dependencies for future analysis extensions
- environment-based configuration

## Project context

This is a personal, self-directed learning project by João Caldas. I use projects like this to learn software engineering, FP&A automation, statistics, AI-assisted development, and system design by building and testing concrete implementations.

AI tools are used extensively during research, design, coding, debugging, testing, and documentation. AI-generated suggestions are treated as inputs to review, not proof of correctness. Finance logic should be validated with explicit assumptions, tests, and synthetic or appropriately licensed data.

## Relationship to the FP&A portfolio

This repository is a more statistical monitoring experiment than `fp-a-metric-monitor`. The two should share finance metric schemas and anomaly-result contracts where that reduces duplicated logic, while remaining separate if their learning goals and implementation styles differ.

## Status

Lab / active learning project.
