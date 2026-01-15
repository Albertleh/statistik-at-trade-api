
  
    

  create  table "tradepulse"."marts_marts"."trade_index__dbt_tmp"
  
  
    as
  
  (
    -- dbt model: unpivot raw stats into an analytics-ready trade_index table.


with raw_data as (
    -- Load raw rows as ingested from the CSV.
    select
        period_key,
        nace_key,
        uidxnom,
        uidxreal,
        beschidx,
        uidxnsb,
        uidxrsb,
        ingested_at
    from raw.statat_trade_raw
),

normalized as (
    -- Unpivot each metric into a unified (period, nace, metric, value) row.
    select
        to_date(replace(period_key, 'TIIDX-', ''), 'YYYYMM') as period_date,
        replace(nace_key, 'NACEIDX-', '') as nace_code,
        'uidxnom' as metric,
        uidxnom as value,
        ingested_at
    from raw_data
    where uidxnom is not null

    union all

    select
        to_date(replace(period_key, 'TIIDX-', ''), 'YYYYMM') as period_date,
        replace(nace_key, 'NACEIDX-', '') as nace_code,
        'uidxreal' as metric,
        uidxreal as value,
        ingested_at
    from raw_data
    where uidxreal is not null

    union all

    select
        to_date(replace(period_key, 'TIIDX-', ''), 'YYYYMM') as period_date,
        replace(nace_key, 'NACEIDX-', '') as nace_code,
        'beschidx' as metric,
        beschidx as value,
        ingested_at
    from raw_data
    where beschidx is not null

    union all

    select
        to_date(replace(period_key, 'TIIDX-', ''), 'YYYYMM') as period_date,
        replace(nace_key, 'NACEIDX-', '') as nace_code,
        'uidxnsb' as metric,
        uidxnsb as value,
        ingested_at
    from raw_data
    where uidxnsb is not null

    union all

    select
        to_date(replace(period_key, 'TIIDX-', ''), 'YYYYMM') as period_date,
        replace(nace_key, 'NACEIDX-', '') as nace_code,
        'uidxrsb' as metric,
        uidxrsb as value,
        ingested_at
    from raw_data
    where uidxrsb is not null
)

select
    -- Final selection filters any rows missing a period_date.
    period_date,
    nace_code,
    metric,
    value,
    ingested_at
from normalized
where period_date is not null
  );
  