{{ config(materialized='table') }}

select
    gasstation_id,
    product_id,
    date_key,
    sum(quantity_in)  as total_quantity_in,
    sum(quantity_out) as total_quantity_out
from {{ ref('fact_inventory_transaction') }}
where product_id is not null
group by 1, 2, 3
