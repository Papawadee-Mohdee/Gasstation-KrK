{{ config(materialized='table') }}

-- Q8: สัดส่วนยอดขายระหว่างน้ำมันกลุ่มเบนซิน (Gasoline) กับกลุ่มดีเซล (Diesel) ในแต่ละสถานี

with agg as (
    select s.gasstation_id, p.product_type,
        sum(s.total_sales_value)   as total_value,
        sum(s.total_quantity_sold) as total_liters
    from {{ ref('int_sales_daily') }} s
    join {{ ref('dim_product') }} p on s.product_id = p.product_id
    where p.product_type in ('Gasoline', 'Diesel')
    group by 1, 2
)

select
    gasstation_id,
    product_type,
    total_liters,
    total_value,
    round(total_value / sum(total_value) over (partition by gasstation_id) * 100, 2) as pct_of_fuel_sales
from agg
