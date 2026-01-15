# at-trade-pulse-api

AT Trade Pulse API is a compact FastAPI + Postgres service that ingests Statistics Austria trade indices and serves clean, queryable time series for quick analysis, dashboards, or interview-ready demos.

## CV summary (copy/paste ready)
Built an end-to-end data product for Austrian trade indices: automated ingestion, raw storage, analytics-ready mart modeling (dbt), and a Streamlit dashboard with momentum, seasonality, and sector comparison views.

## Key Features
- Data ingestion & normalization (Python, FastAPI)
- SQL modeling & testing (dbt, Postgres)
- Analytics API design (query filters, latest deltas)
- Data visualization (Streamlit + Plotly)
- Reproducible local setup (Docker Compose)

<img width="1725" height="565" alt="image" src="https://github.com/user-attachments/assets/83b8c4a1-9d98-437a-bf9f-592a28cf4792" />
<img width="1696" height="1279" alt="image" src="https://github.com/user-attachments/assets/70412e4c-e040-47ab-a843-ba5d13bd0e26" />
<img width="1697" height="1304" alt="image" src="https://github.com/user-attachments/assets/422ed1db-656d-4d71-97cd-9796f88af366" />




**Key endpoints**
- `GET /health`
- `POST /ingest?mode=live|mock`
- `GET /nace`
- `GET /series?nace=<code>&metric=<metric>&start=<YYYY-MM-DD>&end=<YYYY-MM-DD>&limit=<int>`
- `GET /latest?nace=<code>&metric=<metric>`
- `GET /insights/nominal-vs-real?nace=<code>`


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

## Quick verification (Swagger + curl)
1. Open Swagger UI: http://localhost:8000/docs
2. Click **POST /ingest** → **Try it out** → set `mode=mock` → **Execute**.
3. Click **GET /latest** → **Try it out** → `nace=47`, `metric=uidxnom` → **Execute**.
4. Optional analytics endpoints:
   - **GET /series** for a time series window.
   - **GET /insights/nominal-vs-real** for the latest nominal vs real gap.

