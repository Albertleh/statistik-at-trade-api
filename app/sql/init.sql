-- Raw schema holds the original ingested CSV data.
CREATE SCHEMA IF NOT EXISTS raw;
-- Marts schema holds analytics-ready tables.
CREATE SCHEMA IF NOT EXISTS marts;

-- Raw table keyed by period + NACE for idempotent upserts.
CREATE TABLE IF NOT EXISTS raw.statat_trade_raw (
    period_key TEXT NOT NULL,
    nace_key TEXT NOT NULL,
    uidxnom NUMERIC NULL,
    uidxreal NUMERIC NULL,
    beschidx NUMERIC NULL,
    uidxnsb NUMERIC NULL,
    uidxrsb NUMERIC NULL,
    ingested_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (period_key, nace_key)
);

-- Unpivoted metrics table for API queries and dashboards.
CREATE TABLE IF NOT EXISTS marts.trade_index (
    period_date DATE NOT NULL,
    nace_code TEXT NOT NULL,
    metric TEXT NOT NULL,
    value NUMERIC NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (period_date, nace_code, metric)
);
