{{ config(materialized='table') }}
 
select
    gasstation_id,
    product_id,
    date_key,
    quantity_in,
    quantity_out,
    quantity_in - quantity_out as inflow_outflow_diff
from {{ ref('int_inventory_daily') }}
