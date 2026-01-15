select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select period_date
from "tradepulse"."marts_marts"."trade_index"
where period_date is null



      
    ) dbt_internal_test