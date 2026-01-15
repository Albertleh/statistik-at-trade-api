select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select metric
from "tradepulse"."marts_marts"."trade_index"
where metric is null



      
    ) dbt_internal_test