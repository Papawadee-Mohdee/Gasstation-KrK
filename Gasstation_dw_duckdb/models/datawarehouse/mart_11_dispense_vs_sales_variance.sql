{{ config(materialized='table') }}

-- Q11: ปริมาณน้ำมันที่จ่ายออกจากถัง (Quantity Out) สอดคล้องกับยอดขายจริง (Quantity Sold) หรือไม่

select
    coalesce(s.gasstation_id, i.gasstation_id) as gasstation_id,
    coalesce(s.product_id, i.product_id)       as product_id,
    coalesce(s.date_key, i.date_key)           as date_key,
    coalesce(i.total_quantity_out, 0)          as total_dispensed,
    coalesce(s.total_quantity_sold, 0)         as total_sold,
    coalesce(i.total_quantity_out, 0) - coalesce(s.total_quantity_sold, 0) as variance,
    abs(coalesce(i.total_quantity_out, 0) - coalesce(s.total_quantity_sold, 0))
        > 0.05 * nullif(coalesce(i.total_quantity_out, 0), 0) as is_significant_variance
from {{ ref('int_sales_daily') }} s
full outer join {{ ref('int_inventory_daily') }} i
    on s.gasstation_id = i.gasstation_id
    and s.product_id = i.product_id
    and s.date_key = i.date_key
