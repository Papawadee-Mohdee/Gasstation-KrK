{{ config(materialized='table') }}
 
with refills as (
    select f.gasstation_id, f.tank_id, t.capacity_liters, f.product_id, f.date_key,
           f.quantity_in
    from {{ ref('fact_inventory_transaction') }} f
    join {{ ref('dim_tank') }} t on f.tank_id = t.tank_id
    where f.is_receipt_event   -- quantity_in > 0
),
dispensed as (
    select gasstation_id, product_id, date_key, quantity_out
    from {{ ref('int_inventory_daily') }}
)
select
    r.gasstation_id, r.tank_id, r.capacity_liters, r.product_id, r.date_key,
    count(*)                                       as refill_count,
    avg(r.quantity_in)                              as avg_refill_quantity,
    avg(r.quantity_in / nullif(r.capacity_liters,0)) as avg_refill_ratio_to_capacity,
    d.quantity_out                                  as dispensed_quantity
from refills r
left join dispensed d
    on r.gasstation_id = d.gasstation_id and r.product_id = d.product_id
   and r.date_key = d.date_key
group by 1, 2, 3, 4, 5, d.quantity_out
