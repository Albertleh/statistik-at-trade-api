select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select nace_code
from "tradepulse"."marts_marts"."trade_index"
where nace_code is null



      
    ) dbt_internal_test