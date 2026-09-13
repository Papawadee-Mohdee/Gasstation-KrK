{{ config(materialized='table') }}

-- Q15: เมื่ออิงยอดคงเหลือล่าสุดและอัตราขายเฉลี่ยย้อนหลัง 7 วัน สถานีและน้ำมันชนิดใดควรเติมก่อน?
-- latest_remaining_quantity ใช้ธุรกรรมล่าสุดต่อถัง (ไม่รวมข้ามเวลา, ใช้ transaction_id
-- ตัดสินลำดับเมื่อวันเวลาเท่ากัน) ถ้าอัตราขายเฉลี่ยเป็นศูนย์ ให้ estimated_days_to_stockout
-- เป็น null (แปลว่าประมาณด้วยสูตรนี้ไม่ได้ ไม่ใช่ "ไม่ต้องเติม")

with latest_txn as (
    select
        f.gasstation_id,
        f.tank_id,
        f.product_id,
        f.remaining_quantity,
        f.date_key,
        row_number() over (
            partition by f.tank_id
            order by f.date_key desc, f.transaction_id desc
        ) as rn
    from {{ ref('fact_inventory_transaction') }} f
    where not f.is_data_quality_flagged
),

latest as (
    select gasstation_id, tank_id, product_id, remaining_quantity
    from latest_txn
    where rn = 1
),

max_date as (
    select max(date_day) as ref_date
    from {{ ref('dim_date') }}
    where date_key <> -1
),

sales_7d as (
    select
        f.gasstation_id,
        f.product_id,
        sum(f.quantity_sold) / 7.0 as avg_daily_sales_qty_7d
    from {{ ref('fact_sales') }} f
    join {{ ref('dim_date') }} d on f.date_key = d.date_key
    cross join max_date m
    where d.date_day > m.ref_date - interval 7 day
      and d.date_day <= m.ref_date
      and not f.is_data_quality_flagged
    group by 1, 2
)

select
    l.gasstation_id,
    g.gasstation_name,
    l.tank_id,
    l.product_id,
    p.product_name,
    l.remaining_quantity as latest_remaining_quantity,
    s.avg_daily_sales_qty_7d,
    case when s.avg_daily_sales_qty_7d is null or s.avg_daily_sales_qty_7d = 0 then null
         else l.remaining_quantity / s.avg_daily_sales_qty_7d
    end as estimated_days_to_stockout
from latest l
left join sales_7d s
    on l.gasstation_id = s.gasstation_id
   and l.product_id = s.product_id
join {{ ref('dim_gasstation') }} g on l.gasstation_id = g.gasstation_id
join {{ ref('dim_product') }} p on l.product_id = p.product_id