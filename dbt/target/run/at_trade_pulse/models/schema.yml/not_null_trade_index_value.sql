select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select value
from "tradepulse"."marts_marts"."trade_index"
where value is null



      
    ) dbt_internal_test