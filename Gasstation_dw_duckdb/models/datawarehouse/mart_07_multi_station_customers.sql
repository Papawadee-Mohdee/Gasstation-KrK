{{ config(materialized='table') }}

-- Q7: ลูกค้ากลุ่มใดใช้บริการหลายสถานี และยอดขายกระจายระหว่างสถานี/ชนิดน้ำมันอย่างไร?
-- station_count และ pct_of_customer_sales คำนวณจากยอดขายน้ำมันรวมของลูกค้าทั้งหมด (ทุกสถานี)

with base as (
    select
        f.customer_id,
        f.gasstation_id,
        f.product_id,
        sum(f.total_price) as sales_amount
    from {{ ref('fact_sales') }} f
    join {{ ref('dim_product') }} p on f.product_id = p.product_id
    where p.is_fuel
      and not f.is_data_quality_flagged
    group by 1, 2, 3
),

customer_totals as (
    select
        customer_id,
        count(distinct gasstation_id) as station_count,
        sum(sales_amount)             as customer_total_sales
    from base
    group by 1
)

select
    b.customer_id,
    c.customer_name,
    c.vehicle_category,
    b.gasstation_id,
    g.gasstation_name,
    b.product_id,
    p.product_name,
    ct.station_count,
    b.sales_amount,
    b.sales_amount / nullif(ct.customer_total_sales, 0) as pct_of_customer_sales,
    (ct.station_count > 1) as is_multi_station
from base b
join customer_totals ct on b.customer_id = ct.customer_id
join {{ ref('dim_customer') }} c on b.customer_id = c.customer_id
join {{ ref('dim_gasstation') }} g on b.gasstation_id = g.gasstation_id
join {{ ref('dim_product') }} p on b.product_id = p.product_id