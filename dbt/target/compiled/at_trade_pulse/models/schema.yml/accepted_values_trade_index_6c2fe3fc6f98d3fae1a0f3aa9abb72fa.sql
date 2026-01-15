
    
    

with all_values as (

    select
        metric as value_field,
        count(*) as n_records

    from "tradepulse"."marts_marts"."trade_index"
    group by metric

)

select *
from all_values
where value_field not in (
    'uidxnom','uidxreal','beschidx','uidxnsb','uidxrsb'
)


