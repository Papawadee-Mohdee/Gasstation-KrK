{{ config(materialized='table') }}
 
select
    coalesce(s.gasstation_id, i.gasstation_id) as gasstation_id,
    coalesce(s.product_id, i.product_id)       as product_id,
    coalesce(s.date_key, i.date_key)           as date_key,
    s.quantity_sold,
    i.quantity_out                             as dispensed_quantity,
    s.quantity_sold - i.quantity_out           as quantity_diff,
    case when i.quantity_out is null or i.quantity_out = 0 then null
         else (s.quantity_sold - i.quantity_out) / i.quantity_out * 100
    end                                        as diff_percentage
from {{ ref('int_sales_daily') }} s
full outer join {{ ref('int_inventory_daily') }} i
    on s.gasstation_id = i.gasstation_id and s.product_id = i.product_id
   and s.date_key = i.date_key
