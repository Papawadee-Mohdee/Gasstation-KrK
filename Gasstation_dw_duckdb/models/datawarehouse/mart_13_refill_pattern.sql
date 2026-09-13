{{ config(materialized='table') }}

-- Q13: การเติมน้ำมันแต่ละครั้งมีขนาดและความถี่เหมาะสมกับความจุถังและอัตราจ่ายออกเพียงใด?
-- นับรายการเติมเมื่อ QuantityIn > 0 ตามกติกาเดิม

with base as (
    select
        f.gasstation_id,
        f.tank_id,
        f.product_id,
        f.date_key,
        f.quantity_in,
        f.quantity_out
    from {{ ref('fact_inventory_transaction') }} f
    where not f.is_data_quality_flagged
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
    c.capacity_liters,
    b.product_id,
    p.product_name,
    d.date_day,
    count(case when b.quantity_in > 0 then 1 end)             as refill_count,
    avg(case when b.quantity_in > 0 then b.quantity_in end)   as avg_qty_per_refill,
    avg(case when b.quantity_in > 0 then b.quantity_in end)
        / nullif(c.capacity_liters, 0)                        as pct_refill_of_capacity,
    sum(b.quantity_out)                                       as quantity_out_per_day
from base b
join capacity c on b.tank_id = c.tank_id
join {{ ref('dim_gasstation') }} g on b.gasstation_id = g.gasstation_id
join {{ ref('dim_product') }} p on b.product_id = p.product_id
join {{ ref('dim_date') }} d on b.date_key = d.date_key
group by 1, 2, 3, 4, 5, 6, 7