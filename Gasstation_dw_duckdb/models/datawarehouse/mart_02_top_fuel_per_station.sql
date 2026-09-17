{{ config(materialized='table') }}

-- Q2: น้ำมันประเภทใดมียอดจำหน่ายสูงสุดในแต่ละสถานี ทั้งปริมาณลิตรและมูลค่าเงิน

with agg as (
    select gasstation_id, product_id,
        sum(total_quantity_sold) as total_liters,
        sum(total_sales_value)   as total_value
    from {{ ref('int_sales_daily') }}
    group by 1, 2
)

select
    a.gasstation_id,
    a.product_id,
    p.product_name,
    a.total_liters,
    a.total_value,
    row_number() over (partition by a.gasstation_id order by a.total_liters desc) as rank_by_liters,
    row_number() over (partition by a.gasstation_id order by a.total_value desc)  as rank_by_value
from agg a
join {{ ref('dim_product') }} p on a.product_id = p.product_id
where p.is_fuel
