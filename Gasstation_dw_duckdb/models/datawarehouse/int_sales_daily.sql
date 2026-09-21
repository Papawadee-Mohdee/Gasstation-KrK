{{ config(materialized='table') }}

select
    gasstation_id,
    product_id,
    date_key,
    sum(quantity_sold) as total_quantity_sold,
    sum(total_price)   as total_sales_value,
    count(*)           as line_count
from {{ ref('fact_sales') }}
group by 1, 2, 3
