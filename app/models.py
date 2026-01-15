"""Pydantic response models for API endpoints."""
from datetime import date
from typing import Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health status response."""
    status: str
    db: str


class IngestResponse(BaseModel):
    """Ingestion summary response."""
    rows_loaded: int
    distinct_nace: int
    min_date: Optional[date]
    max_date: Optional[date]
    source_mode: str


class SeriesPoint(BaseModel):
    """Single time-series point."""
    period_date: date
    value: float


class LatestResponse(BaseModel):
    """Latest value and delta response."""
    nace: str
    metric: str
    latest_date: date
    latest_value: float
    previous_value: Optional[float]
    delta: Optional[float]
    delta_percent: Optional[float]


class NominalVsRealResponse(BaseModel):
    """Nominal vs real comparison response."""
    nace: str
    period_date: date
    uidxnom: Optional[float]
    uidxreal: Optional[float]
    gap: Optional[float]
    caveat: str
