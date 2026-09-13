{{ config(materialized='table') }}

-- Q12: ถังของสถานีใดมีระดับน้ำมันต่ำกว่าเกณฑ์บ่อยที่สุด และเกิดกับน้ำมันชนิดใดในช่วงเวลาใด?
-- เกณฑ์ต่ำกว่า 20% ของ Capacity เป็นค่าสมมติ ปรับได้ผ่าน dbt var 'low_fuel_threshold_pct'
-- นับถัง-วันที่-ชั่วโมงแบบไม่ซ้ำ: รวมทุกธุรกรรมในชั่วโมงเดียวกันด้วย min(remaining_quantity)
-- (จุดต่ำสุดที่เกิดขึ้นจริงในชั่วโมงนั้น) ก่อนเทียบเกณฑ์ ไม่ตีความเป็นระยะเวลาต่อเนื่อง

with base as (
    select
        f.gasstation_id,
        f.tank_id,
        f.product_id,
        f.date_key,
        f.hour_of_day,
        min(f.remaining_quantity) as remaining_quantity
    from {{ ref('fact_inventory_transaction') }} f
    where not f.is_data_quality_flagged
    group by 1, 2, 3, 4, 5
),

capacity as (
    select tank_id, capacity_liters
    from {{ ref('dim_tank') }}
    where is_current
)

select
    b.gasstation_id,
    g.gasstation_name,
    b.tank_id,
    b.product_id,
    p.product_name,
    d.date_day,
    b.hour_of_day,
    b.remaining_quantity,
    c.capacity_liters,
    b.remaining_quantity / nullif(c.capacity_liters, 0) as pct_remaining,
    (b.remaining_quantity / nullif(c.capacity_liters, 0))
        < ({{ var('low_fuel_threshold_pct', 20) }} / 100.0)  as is_below_threshold
from base b
join capacity c on b.tank_id = c.tank_id
join {{ ref('dim_gasstation') }} g on b.gasstation_id = g.gasstation_id
join {{ ref('dim_product') }} p on b.product_id = p.product_id
join {{ ref('dim_date') }} d on b.date_key = d.date_key