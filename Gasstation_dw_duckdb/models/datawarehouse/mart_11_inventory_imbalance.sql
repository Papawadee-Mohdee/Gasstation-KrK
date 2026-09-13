{{ config(materialized='table') }}

select
    f.gasstation_id,
    g.gasstation_name,
    f.tank_id,
    f.product_id,
    p.product_name,
    d.date_day,
    sum(f.quantity_in) as quantity_in,
    sum(f.quantity_out) as quantity_out,
    sum(f.quantity_in) - sum(f.quantity_out) as imbalance
from {{ ref('fact_inventory_transaction') }} f
join {{ ref('dim_gasstation') }} g
    on f.gasstation_id = g.gasstation_id
join {{ ref('dim_product') }} p
    on f.product_id = p.product_id
join {{ ref('dim_date') }} d
    on f.date_key = d.date_key
where p.is_fuel
  and not f.is_data_quality_flagged
group by 1, 2, 3, 4, 5, 6