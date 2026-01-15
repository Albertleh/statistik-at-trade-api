select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

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



      
    ) dbt_internal_test