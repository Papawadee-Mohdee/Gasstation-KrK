{{ config(materialized='table') }}
 
with current_day as (
    select s.*, dt.iso_weekday, dt.weekday_name
    from {{ ref('int_sales_daily') }} s
    join {{ ref('dim_date') }} dt on s.date_key = dt.date_key
),
prior_week as (
    select gasstation_id, product_id,
           cast(strftime(dt.date_day + interval 7 day, '%Y%m%d') as integer)
               as date_key,   -- key ของวันปัจจุบันที่ควรจับคู่กับแถวนี้
           quantity_sold  as prior_quantity_sold,
           sales_amount   as prior_sales_amount
    from {{ ref('int_sales_daily') }} s
    join {{ ref('dim_date') }} dt on s.date_key = dt.date_key
)
select
    c.gasstation_id, c.product_id, c.date_key, c.iso_weekday, c.weekday_name,
    c.sales_amount, p.prior_sales_amount,
    c.sales_amount - p.prior_sales_amount            as sales_amount_diff,
    (c.sales_amount - p.prior_sales_amount) / nullif(p.prior_sales_amount, 0)
        as sales_amount_change_rate,
    c.quantity_sold - p.prior_quantity_sold          as quantity_diff
from current_day c
join prior_week p
    on c.gasstation_id = p.gasstation_id and c.product_id = p.product_id
   and c.date_key = p.date_key
-- inner join: มีผลเฉพาะคู่วันที่ทั้งวันนี้และ d-7 มีข้อมูลจริงทั้งสองวัน
