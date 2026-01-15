"""FastAPI application with endpoints for health, ingestion, and analytics queries."""
from datetime import date, datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from app import ingest as ingest_service
from app.db import fetch_all, fetch_one, get_conn
from app.models import (
    HealthResponse,
    IngestResponse,
    LatestResponse,
    NominalVsRealResponse,
    SeriesPoint,
)

# Main FastAPI app instance with human-friendly title.
app = FastAPI(title="AT Trade Pulse API")

# Metrics exposed by the API (mapped from the source CSV).
ALLOWED_METRICS = {"uidxnom", "uidxreal", "beschidx", "uidxnsb", "uidxrsb"}


def _parse_date(value: Optional[str]) -> Optional[date]:
    """Parse a YYYY-MM-DD string into a date for query filtering."""
    if value is None:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid date format") from exc


def _validate_metric(metric: str) -> str:
    """Guardrail for valid metric keys."""
    if metric not in ALLOWED_METRICS:
        raise HTTPException(status_code=400, detail="Invalid metric")
    return metric


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Lightweight health check that validates DB connectivity."""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    except Exception:
        return JSONResponse(status_code=500, content={"status": "error", "db": "error"})
    return {"status": "ok", "db": "ok"}


@app.post("/ingest", response_model=IngestResponse)
def ingest(mode: str = Query("mock", pattern="^(mock|live)$")):
    """Trigger ingestion for mock or live datasets."""
    try:
        result = ingest_service.ingest(mode)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Ingestion failed") from exc


@app.get("/nace", response_model=List[str])
def list_nace():
    """List all distinct NACE codes available in the mart table."""
    rows = fetch_all(
        "SELECT DISTINCT nace_code FROM marts.trade_index ORDER BY nace_code",
        (),
    )
    return [row["nace_code"] for row in rows]


@app.get("/series", response_model=List[SeriesPoint])
def get_series(
    nace: str = Query(..., min_length=1),
    metric: str = Query(...),
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = Query(500, ge=1, le=5000),
):
    """Return a time series for the given NACE + metric and optional date range."""
    metric = _validate_metric(metric)
    start_date = _parse_date(start)
    end_date = _parse_date(end)

    conditions = ["nace_code = %s", "metric = %s"]
    params = [nace, metric]
    if start_date:
        conditions.append("period_date >= %s")
        params.append(start_date)
    if end_date:
        conditions.append("period_date <= %s")
        params.append(end_date)

    where_clause = " AND ".join(conditions)
    sql = (
        "SELECT period_date, value FROM marts.trade_index "
        f"WHERE {where_clause} ORDER BY period_date ASC LIMIT %s"
    )
    params.append(limit)
    rows = fetch_all(sql, tuple(params))
    return [
        SeriesPoint(period_date=row["period_date"], value=float(row["value"]))
        for row in rows
    ]


@app.get("/latest", response_model=LatestResponse)
def get_latest(nace: str = Query(...), metric: str = Query(...)):
    """Return the latest value plus previous value and deltas."""
    metric = _validate_metric(metric)
    rows = fetch_all(
        """
        SELECT period_date, value FROM marts.trade_index
        WHERE nace_code = %s AND metric = %s
        ORDER BY period_date DESC
        LIMIT 2
        """,
        (nace, metric),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="No data for query")

    latest = rows[0]
    previous = rows[1] if len(rows) > 1 else None
    latest_value = float(latest["value"])
    previous_value = float(previous["value"]) if previous else None
    delta = latest_value - previous_value if previous_value is not None else None
    delta_percent = (
        (delta / previous_value) * 100 if previous_value not in (None, 0) else None
    )

    return {
        "nace": nace,
        "metric": metric,
        "latest_date": latest["period_date"],
        "latest_value": latest_value,
        "previous_value": previous_value,
        "delta": delta,
        "delta_percent": delta_percent,
    }


@app.get("/insights/nominal-vs-real", response_model=NominalVsRealResponse)
def nominal_vs_real(nace: str = Query(...)):
    """Compare nominal vs. real indices for the latest period."""
    rows = fetch_all(
        """
        SELECT period_date, metric, value FROM marts.trade_index
        WHERE nace_code = %s AND metric IN ('uidxnom', 'uidxreal')
        ORDER BY period_date DESC
        """,
        (nace,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="No data for query")

    latest_date = rows[0]["period_date"]
    latest_rows = [row for row in rows if row["period_date"] == latest_date]
    metric_map = {row["metric"]: float(row["value"]) for row in latest_rows}
    uidxnom = metric_map.get("uidxnom")
    uidxreal = metric_map.get("uidxreal")
    gap = uidxnom - uidxreal if uidxnom is not None and uidxreal is not None else None

    return {
        "nace": nace,
        "period_date": latest_date,
        "uidxnom": uidxnom,
        "uidxreal": uidxreal,
        "gap": gap,
        "caveat": "Nominal vs. real gap is indicative; interpret with context.",
    }
