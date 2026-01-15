"""CSV ingestion utilities for Statistics Austria trade indices."""
import csv
import re
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from io import StringIO
from pathlib import Path
from typing import Dict, List, Optional

import requests
from psycopg2 import extras

from app.db import get_conn
from app.settings import settings

# Base directory of the repo (used to find sample data).
BASE_DIR = Path(__file__).resolve().parents[1]
SAMPLE_PATH = BASE_DIR / "data" / "sample" / "statat_trade_sample.csv"

# Required columns from the source CSV.
REQUIRED_COLUMNS = {
    "C-TI-0": "period_key",
    "C-NACEIDX-0": "nace_key",
    "F-UIDXNOM": "uidxnom",
    "F-UIDXREAL": "uidxreal",
    "F-BESCHIDX": "beschidx",
}
# Optional columns that are ingested when present.
OPTIONAL_COLUMNS = {
    "F-UIDXNSB": "uidxnsb",
    "F-UIDXRSB": "uidxrsb",
}

# Metrics to unpivot into the marts table.
METRIC_COLUMNS = {
    "uidxnom": "uidxnom",
    "uidxreal": "uidxreal",
    "beschidx": "beschidx",
    "uidxnsb": "uidxnsb",
    "uidxrsb": "uidxrsb",
}


@dataclass
class ParsedRow:
    """Parsed CSV row containing keys and metric values."""
    period_key: str
    nace_key: str
    values: Dict[str, Optional[Decimal]]


def _parse_decimal(raw: Optional[str]) -> Optional[Decimal]:
    """Parse numeric strings with comma or dot decimal separators."""
    if raw is None:
        return None
    cleaned = raw.strip()
    if not cleaned:
        return None
    cleaned = cleaned.replace(" ", "").replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _normalize_header(value: str) -> str:
    """Normalize CSV header labels to improve matching."""
    return value.strip().lstrip("\ufeff").upper().replace(" ", "").replace("_", "-")


def _resolve_column(fieldnames: List[str], target: str) -> Optional[str]:
    """Find the best-matching column for a required/optional field."""
    target_norm = _normalize_header(target)
    for name in fieldnames:
        normalized = _normalize_header(name)
        if normalized == target_norm or normalized.endswith(target_norm) or normalized.startswith(target_norm):
            return name
    return None


def _find_month_index(data_rows: List[List[str]], header: List[str]) -> Optional[int]:
    """Detect a month column (1-12) when year-only periods are provided."""
    for idx, _ in enumerate(header):
        sample_values = [
            row[idx].strip()
            for row in data_rows[:200]
            if idx < len(row) and row[idx].strip()
        ]
        if not sample_values:
            continue
        if all(value.isdigit() and 1 <= int(value) <= 12 for value in sample_values):
            return idx
    return None


def _parse_csv_rows(text: str) -> List[ParsedRow]:
    """Parse CSV text into normalized rows with flexible header handling."""
    sample = text[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
    except csv.Error:
        dialect = csv.excel

    reader = csv.reader(StringIO(text), dialect=dialect)
    rows_raw = list(reader)
    if not rows_raw:
        return []

    header = rows_raw[0]
    data_rows = rows_raw[1:]
    required_map: Dict[str, int] = {}

    for column in REQUIRED_COLUMNS:
        resolved = _resolve_column(header, column)
        if resolved:
            required_map[column] = header.index(resolved)

    if "C-TI-0" not in required_map:
        for idx, name in enumerate(header):
            if any(
                row[idx].strip().startswith("TIIDX-")
                for row in data_rows[:200]
                if idx < len(row)
            ):
                required_map["C-TI-0"] = idx
                break

    if "C-NACEIDX-0" not in required_map:
        for idx, name in enumerate(header):
            if any(
                row[idx].strip().startswith("NACEIDX-")
                for row in data_rows[:200]
                if idx < len(row)
            ):
                required_map["C-NACEIDX-0"] = idx
                break

    missing = [col for col in REQUIRED_COLUMNS if col not in required_map]
    if missing:
        raise ValueError(
            f"Missing required columns: {', '.join(missing)}. "
            f"Headers detected: {', '.join(header[:20])}"
        )

    optional_map: Dict[str, int] = {}
    for column in OPTIONAL_COLUMNS:
        resolved = _resolve_column(header, column)
        if resolved:
            optional_map[column] = header.index(resolved)

    rows: List[ParsedRow] = []
    month_idx = _find_month_index(data_rows, header)
    for row in data_rows:
        period_idx = required_map["C-TI-0"]
        nace_idx = required_map["C-NACEIDX-0"]
        period_key = row[period_idx] if period_idx < len(row) else None
        nace_key = row[nace_idx] if nace_idx < len(row) else None
        if not period_key or not nace_key:
            continue
        period_key = period_key.strip()
        if re.fullmatch(r"\d{4}", period_key) and month_idx is not None:
            month_value = row[month_idx] if month_idx < len(row) else ""
            if month_value and month_value.isdigit():
                period_key = f"{period_key}{int(month_value):02d}"
        values: Dict[str, Optional[Decimal]] = {}
        for csv_col, metric in REQUIRED_COLUMNS.items():
            col_idx = required_map[csv_col]
            raw_value = row[col_idx] if col_idx < len(row) else None
            values[metric] = _parse_decimal(raw_value)
        for csv_col, metric in OPTIONAL_COLUMNS.items():
            col_idx = optional_map.get(csv_col)
            raw_value = row[col_idx] if col_idx is not None and col_idx < len(row) else None
            values[metric] = _parse_decimal(raw_value)
        rows.append(ParsedRow(period_key=period_key, nace_key=nace_key, values=values))
    return rows


def _load_source(mode: str) -> str:
    """Load CSV content from a bundled mock file or the live URL."""
    if mode == "mock":
        return SAMPLE_PATH.read_text(encoding="utf-8")
    if mode == "live":
        response = requests.get(settings.data_url, timeout=30)
        response.raise_for_status()
        return response.text
    raise ValueError("mode must be 'live' or 'mock'")


def _period_to_date(period_key: str) -> Optional[date]:
    """Convert period strings to dates while tolerating multiple formats."""
    # period_key formats: TIIDX-YYYYMM, YYYYMM, YYYY-MM, or YYYY
    cleaned = period_key.strip()
    if "-" in cleaned:
        parts = cleaned.split("-")
        if len(parts[-1]) == 6:
            cleaned = parts[-1]
        elif len(parts[-1]) == 2 and len(parts[0]) == 4:
            cleaned = f"{parts[0]}{parts[1]}"
        elif len(parts[-1]) == 4:
            cleaned = parts[-1]

    if re.fullmatch(r"\d{6}", cleaned):
        return datetime.strptime(cleaned, "%Y%m").date().replace(day=1)
    if re.fullmatch(r"\d{4}", cleaned):
        return datetime.strptime(cleaned, "%Y").date().replace(day=1)
    return None


def ingest(mode: str) -> Dict[str, object]:
    """Ingest CSV content into raw + marts schemas (idempotent)."""
    source_text = _load_source(mode)
    parsed_rows = _parse_csv_rows(source_text)
    ingested_at = datetime.utcnow()

    if not parsed_rows:
        return {
            "rows_loaded": 0,
            "distinct_nace": 0,
            "min_date": None,
            "max_date": None,
            "source_mode": mode,
        }

    with get_conn() as conn:
        with conn.cursor() as cur:
            raw_rows = []
            for row in parsed_rows:
                raw_rows.append(
                    (
                        row.period_key,
                        row.nace_key,
                        row.values.get("uidxnom"),
                        row.values.get("uidxreal"),
                        row.values.get("beschidx"),
                        row.values.get("uidxnsb"),
                        row.values.get("uidxrsb"),
                        ingested_at,
                    )
                )

            extras.execute_values(
                cur,
                """
                INSERT INTO raw.statat_trade_raw (
                    period_key, nace_key, uidxnom, uidxreal, beschidx, uidxnsb, uidxrsb, ingested_at
                ) VALUES %s
                ON CONFLICT (period_key, nace_key) DO UPDATE SET
                    uidxnom = EXCLUDED.uidxnom,
                    uidxreal = EXCLUDED.uidxreal,
                    beschidx = EXCLUDED.beschidx,
                    uidxnsb = EXCLUDED.uidxnsb,
                    uidxrsb = EXCLUDED.uidxrsb,
                    ingested_at = EXCLUDED.ingested_at
                """,
                raw_rows,
            )

            mart_rows = []
            for row in parsed_rows:
                period_date = _period_to_date(row.period_key)
                if period_date is None:
                    continue
                nace_code = row.nace_key.replace("NACEIDX-", "")
                for metric_key, metric_col in METRIC_COLUMNS.items():
                    value = row.values.get(metric_col)
                    if value is None:
                        continue
                    mart_rows.append(
                        (
                            period_date,
                            nace_code,
                            metric_key,
                            value,
                            ingested_at,
                        )
                    )

            extras.execute_values(
                cur,
                """
                INSERT INTO marts.trade_index (
                    period_date, nace_code, metric, value, ingested_at
                ) VALUES %s
                ON CONFLICT (period_date, nace_code, metric) DO UPDATE SET
                    value = EXCLUDED.value,
                    ingested_at = EXCLUDED.ingested_at
                """,
                mart_rows,
            )

    valid_dates = [
        parsed_date
        for parsed_date in (_period_to_date(row.period_key) for row in parsed_rows)
        if parsed_date is not None
    ]
    min_date = min(valid_dates) if valid_dates else None
    max_date = max(valid_dates) if valid_dates else None
    distinct_nace = len({row.nace_key for row in parsed_rows})

    return {
        "rows_loaded": len(parsed_rows),
        "distinct_nace": distinct_nace,
        "min_date": min_date,
        "max_date": max_date,
        "source_mode": mode,
    }
