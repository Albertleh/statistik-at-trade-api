# Local Setup

> This guide explains each step in plain language for quick local setup.

## Prerequisites
- Docker
- Docker Compose
- curl

## Run the stack
```bash
cp .env.example .env
./scripts/run.sh
```

## Verify
- Open http://localhost:8000/docs
- Ingest mock data:
  ```bash
  curl -X POST "http://localhost:8000/ingest?mode=mock"
  ```
- Query latest:
  ```bash
  curl "http://localhost:8000/latest?nace=47&metric=uidxnom"
  ```
- Inspect analytics-style endpoints:
  ```bash
  curl "http://localhost:8000/nace"
  curl "http://localhost:8000/series?nace=47&metric=uidxnom&start=2021-01-01&end=2021-03-01"
  curl "http://localhost:8000/insights/nominal-vs-real?nace=47"
  ```

### Example responses
- `POST /ingest?mode=mock`
  ```json
  {
    "rows_loaded": 12,
    "distinct_nace": 4,
    "min_date": "2021-01-01",
    "max_date": "2021-03-01",
    "source_mode": "mock"
  }
  ```
- `GET /latest?nace=47&metric=uidxnom`
  ```json
  {
    "nace": "47",
    "metric": "uidxnom",
    "latest_date": "2021-03-01",
    "latest_value": 97.8,
    "previous_value": 96.1,
    "delta": 1.7,
    "delta_percent": 1.769
  }
  ```
- `GET /insights/nominal-vs-real?nace=47`
  ```json
  {
    "nace": "47",
    "period_date": "2021-03-01",
    "uidxnom": 97.8,
    "uidxreal": 95.6,
    "gap": 2.2,
    "caveat": "Nominal vs. real gap is indicative; interpret with context."
  }
  ```

## Live ingestion
```bash
curl -X POST "http://localhost:8000/ingest?mode=live"
```

## dbt modeling (optional)
```bash
pip install -r requirements_dbt.txt
DBT_PROFILES_DIR=./dbt dbt run --project-dir ./dbt
DBT_PROFILES_DIR=./dbt dbt test --project-dir ./dbt
```

### Notes
- `mock` uses the bundled sample CSV with only 3 months of data, so the YoY chart will show a warning.
- `live` pulls the full Statistics Austria CSV and should provide enough history for YoY charts.
- The SQL init output showing “schema already exists” is normal; it means the init is idempotent.

## Troubleshooting
- If ports are busy, stop existing services or edit `docker-compose.yml` ports.
- To reset all containers and volumes:
  ```bash
  ./scripts/reset.sh
  ```
