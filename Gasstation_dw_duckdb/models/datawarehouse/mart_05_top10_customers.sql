{{ config(materialized='table') }}

-- Q5: ลูกค้า 10 อันดับแรกของแต่ละสถานีใช้รถประเภทใด และซื้อน้ำมันชนิดใดเป็นหลัก?
-- customer_sales/rank คำนวณจากยอดขายน้ำมันรวมทุกชนิดของลูกค้าคนนั้นในสถานีนั้น
-- product_name ที่แนบมาคือ "สินค้าที่ลูกค้าคนนั้นซื้อมากสุด" (dominant product) ไม่ใช่ระดับ grain หลัก

with customer_product as (
    select
        f.gasstation_id,
        f.customer_id,
        f.product_id,
        sum(f.total_price)           as product_sales,
        count(distinct f.invoice_id) as product_bill_count
    from {{ ref('fact_sales') }} f
    join {{ ref('dim_product') }} p on f.product_id = p.product_id
    where p.is_fuel
      and not f.is_data_quality_flagged
    group by 1, 2, 3
),

customer_totals as (
    select
        gasstation_id,
        customer_id,
        sum(product_sales)      as customer_sales,
        sum(product_bill_count) as bill_count
    from customer_product
    group by 1, 2
),

dominant_product as (
    select
        *,
        row_number() over (
            partition by gasstation_id, customer_id order by product_sales desc
        ) as product_rank
    from customer_product
),

station_totals as (
    select gasstation_id, sum(customer_sales) as station_customer_sales
    from customer_totals
    group by 1
),

ranked_customers as (
    select
        ct.*,
        dense_rank() over (
            partition by ct.gasstation_id order by ct.customer_sales desc
        ) as rank_in_station
    from customer_totals ct
)

select
    r.gasstation_id,
    g.gasstation_name,
    r.customer_id,
    c.customer_name,
    c.vehicle_category,
    dp.product_id,
    p.product_name,
    r.customer_sales,
    r.bill_count,
    r.customer_sales / nullif(st.station_customer_sales, 0) as pct_from_top10,
    r.rank_in_station
from ranked_customers r
join station_totals st on r.gasstation_id = st.gasstation_id
join dominant_product dp
    on r.gasstation_id = dp.gasstation_id
   and r.customer_id = dp.customer_id
   and dp.product_rank = 1
join {{ ref('dim_gasstation') }} g on r.gasstation_id = g.gasstation_id
join {{ ref('dim_customer') }} c on r.customer_id = c.customer_id
join {{ ref('dim_product') }} p on dp.product_id = p.product_id
where r.rank_in_station <= 10