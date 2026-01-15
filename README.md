# at-trade-pulse-api

AT Trade Pulse API is a compact FastAPI + Postgres service that ingests Statistics Austria trade indices and serves clean, queryable time series for quick analysis, dashboards, or interview-ready demos.

> This README includes commands and context so a non-technical reader can follow along.

## CV summary (copy/paste ready)
Built an end-to-end data product for Austrian trade indices: automated ingestion, raw storage, analytics-ready mart modeling (dbt), and a Streamlit dashboard with momentum, seasonality, and sector comparison views.

## Skills demonstrated
- Data ingestion & normalization (Python, FastAPI)
- SQL modeling & testing (dbt, Postgres)
- Analytics API design (query filters, latest deltas)
- Data visualization (Streamlit + Plotly)
- Reproducible local setup (Docker Compose)

## Portfolio screenshots
Add 2–3 screenshots here (recommended):
1) Latest snapshot + line chart + YoY bar  
2) Nominal vs. real with gap  
3) Seasonality heatmap + sector comparison  

```
+---------+      +-----------+      +----------------------+
|  CSV    | ---> |  FastAPI  | ---> | Postgres (raw/marts) |
+---------+      +-----------+      +----------------------+
```

**Key endpoints**
- `GET /health`
- `POST /ingest?mode=live|mock`
- `GET /nace`
- `GET /series?nace=<code>&metric=<metric>&start=<YYYY-MM-DD>&end=<YYYY-MM-DD>&limit=<int>`
- `GET /latest?nace=<code>&metric=<metric>`
- `GET /insights/nominal-vs-real?nace=<code>`

**Run in 3 commands**
```bash
cp .env.example .env
./scripts/run.sh
open http://localhost:8000/docs
```

## Exact commands to reproduce the dashboard flow
```bash
cp .env.example .env
./scripts/run.sh
curl -X POST "http://localhost:8000/ingest?mode=live"
pip install -r requirements_dbt.txt
DBT_PROFILES_DIR=./dbt dbt run --project-dir ./dbt
DBT_PROFILES_DIR=./dbt dbt test --project-dir ./dbt
pip install -r requirements_dashboard.txt
streamlit run dashboard/app.py
```

### What you will see
- **Latest snapshot**: latest value with absolute and % change for the chosen NACE + metric.
- **Line chart**: level series over time.
- **MoM / YoY bars**: momentum views for the last 12 months.
- **Nominal vs Real**: uidxnom vs uidxreal with gap line.
- **Seasonality heatmap**: year x month view of index intensity.
- **Data preview**: last 20 rows with computed changes.

## dbt modeling (CV feature)
The dbt project builds `marts.trade_index` from `raw.statat_trade_raw` and runs basic tests
(`not_null`, `accepted_values`). Run it after ingestion:

```bash
pip install -r requirements_dbt.txt
DBT_PROFILES_DIR=./dbt dbt run --project-dir ./dbt
DBT_PROFILES_DIR=./dbt dbt test --project-dir ./dbt
```

## Key deliverables (what to show in an interview)
- **ETL**: live ingestion from Statistik Austria into raw + mart tables.
- **Modeling**: dbt model with tests and lineage.
- **Analytics**: FastAPI endpoints for latest + time series.
- **Visualization**: Streamlit dashboard with business-friendly charts.

## Quick verification (Swagger + curl)
1. Open Swagger UI: http://localhost:8000/docs
2. Click **POST /ingest** → **Try it out** → set `mode=mock` → **Execute**.
3. Click **GET /latest** → **Try it out** → `nace=47`, `metric=uidxnom` → **Execute**.
4. Optional analytics endpoints:
   - **GET /series** for a time series window.
   - **GET /insights/nominal-vs-real** for the latest nominal vs real gap.

### cURL examples
```bash
curl -X POST "http://localhost:8000/ingest?mode=mock"
curl "http://localhost:8000/nace"
curl "http://localhost:8000/series?nace=47&metric=uidxnom&start=2021-01-01&end=2021-03-01"
curl "http://localhost:8000/latest?nace=47&metric=uidxnom"
curl "http://localhost:8000/insights/nominal-vs-real?nace=47"
```
