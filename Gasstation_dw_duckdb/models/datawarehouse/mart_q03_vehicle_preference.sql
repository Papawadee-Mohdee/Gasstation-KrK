{{ config(materialized='table') }}
 
select
    c.vehicle_type,
    c.vehicle_category,
    s.product_id,
    s.gasstation_id,
    sum(s.quantity_sold)               as quantity_sold,
    count(distinct s.invoice_id)       as invoice_count,
    sum(s.quantity_sold) / nullif(count(distinct s.invoice_id), 0)
        as avg_quantity_per_invoice
from {{ ref('fact_sales') }} s
join {{ ref('dim_customer') }} c on s.customer_id = c.customer_id
join {{ ref('dim_product') }} p  on s.product_id  = p.product_id
where p.is_fuel and not s.is_data_quality_flagged
group by 1, 2, 3, 4
