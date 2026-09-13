{{ config(materialized='table') }}

select
    gasstation_id,
    product_id,
    date_key,
    sum(quantity_in) as quantity_in,
    sum(quantity_out) as quantity_out,
    sum(quantity_in - quantity_out) as net_quantity
from {{ ref('fact_inventory_transaction') }}
where not is_data_quality_flagged
group by 1, 2, 3