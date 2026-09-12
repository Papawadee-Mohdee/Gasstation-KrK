{{ config(materialized='table') }}
 
select
    gasstation_id,
    product_id,
    date_key,
    sum(quantity_sold)               as quantity_sold,
    sum(total_price)                 as sales_amount,
    count(distinct invoice_id)       as invoice_count
from {{ ref('fact_sales') }}
where not is_data_quality_flagged
group by 1, 2, 3
