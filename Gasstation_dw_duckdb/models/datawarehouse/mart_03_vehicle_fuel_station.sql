{{ config(materialized='table') }}

-- Q3: ลูกค้าที่ใช้รถแต่ละประเภทนิยมซื้อน้ำมันชนิดใด และรูปแบบต่างกันระหว่างสถานีอย่างไร?

with base as (
    select
        c.vehicle_category,
        f.product_id,
        f.gasstation_id,
        f.invoice_id,
        f.quantity_sold
    from {{ ref('fact_sales') }} f
    join {{ ref('dim_customer') }} c on f.customer_id = c.customer_id
    join {{ ref('dim_product') }} p on f.product_id = p.product_id
    where p.is_fuel
      and not f.is_data_quality_flagged
)

select
    b.vehicle_category,
    b.gasstation_id,
    g.gasstation_name,
    b.product_id,
    p.product_name,
    sum(b.quantity_sold)                                              as quantity_sold,
    count(distinct b.invoice_id)                                      as bill_count,
    sum(b.quantity_sold) / nullif(count(distinct b.invoice_id), 0)    as avg_qty_per_bill
from base b
join {{ ref('dim_gasstation') }} g on b.gasstation_id = g.gasstation_id
join {{ ref('dim_product') }} p on b.product_id = p.product_id
group by 1, 2, 3, 4, 5