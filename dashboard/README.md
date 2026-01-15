# Dashboard

> This guide explains how to run and interpret the dashboard.

## Prerequisites
- API running at http://localhost:8000
- Ingested data (use `curl -X POST "http://localhost:8000/ingest?mode=mock"`)

## Exact commands to run (end-to-end)
```bash
cp .env.example .env
./scripts/run.sh
curl -X POST "http://localhost:8000/ingest?mode=mock"
pip install -r requirements_dbt.txt
DBT_PROFILES_DIR=./dbt dbt run --project-dir ./dbt
pip install -r requirements_dashboard.txt
streamlit run dashboard/app.py
```

## Install
```bash
pip install -r requirements_dashboard.txt
```

## Run
```bash
streamlit run dashboard/app.py
```

## Screenshot guidance (for CV/README)
- Use the "Latest snapshot" card plus the line chart and nominal-vs-real chart as your hero visuals.
- Optional: show the seasonality heatmap and sector comparison toggle for depth.
- Capture the data preview table to show traceability.

## Why the YoY chart may be missing
- The mock dataset only includes 3 months of data, so YoY needs live ingestion.
- Run `curl -X POST "http://localhost:8000/ingest?mode=live"` to fetch the full history.

## NACE code reference
- The dashboard labels common trade codes (G/45/46/47 and sub-codes like 461, 471).
- Use the “NACE code reference” expander in the app to see the mapping table.
