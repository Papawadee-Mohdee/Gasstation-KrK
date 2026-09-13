{{ config(materialized='table') }}

-- Q14: ปริมาณขายตามใบเสร็จตรงกับปริมาณจ่ายออกจากถังหรือไม่ ส่วนต่างกระจุกตัวที่ใด?
-- สรุปยอดขายและยอดจ่ายออกแยกกันก่อน แล้วเชื่อมที่ สถานี × สินค้า × วัน เพื่อกันยอดคูณซ้ำ
-- ส่วนต่างเป็น "จุดให้ตรวจสอบ" ไม่ใช่ข้อสรุปว่าน้ำมันสูญหาย

with sales_daily as (
    select
        f.gasstation_id, f.product_id, d.date_day,
        sum(f.quantity_sold) as quantity_sold
    from {{ ref('fact_sales') }} f
    join {{ ref('dim_product') }} p on f.product_id = p.product_id
    join {{ ref('dim_date') }} d on f.date_key = d.date_key
    where p.is_fuel
      and not f.is_data_quality_flagged
    group by 1, 2, 3
),

dispense_daily as (
    select
        f.gasstation_id, f.product_id, d.date_day,
        sum(f.quantity_out) as quantity_out
    from {{ ref('fact_inventory_transaction') }} f
    join {{ ref('dim_product') }} p on f.product_id = p.product_id
    join {{ ref('dim_date') }} d on f.date_key = d.date_key
    where p.is_fuel
      and not f.is_data_quality_flagged
    group by 1, 2, 3
)

select
    coalesce(s.gasstation_id, i.gasstation_id) as gasstation_id,
    g.gasstation_name,
    coalesce(s.product_id, i.product_id)       as product_id,
    p.product_name,
    coalesce(s.date_day, i.date_day)           as date_day,
    coalesce(s.quantity_sold, 0)               as quantity_sold,
    coalesce(i.quantity_out, 0)                as quantity_out,
    coalesce(s.quantity_sold, 0) - coalesce(i.quantity_out, 0) as diff,
    case when coalesce(i.quantity_out, 0) = 0 then null
         else (coalesce(s.quantity_sold, 0) - i.quantity_out) / i.quantity_out * 100
    end as pct_diff
from sales_daily s
full outer join dispense_daily i
    on s.gasstation_id = i.gasstation_id
   and s.product_id = i.product_id
   and s.date_day = i.date_day
join {{ ref('dim_gasstation') }} g
    on coalesce(s.gasstation_id, i.gasstation_id) = g.gasstation_id
join {{ ref('dim_product') }} p
    on coalesce(s.product_id, i.product_id) = p.product_id