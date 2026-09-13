{{ config(materialized='table') }}

-- Q1: สถานีใดสร้างยอดขายสูงสุดในแต่ละวัน และยอดขายมาจากน้ำมันชนิดใดเป็นหลัก?
-- จัดอันดับสถานีจากยอดขาย "ทุกสินค้า" (ไม่กรอง is_fuel ตอน rank) แล้วแนบสัดส่วนราย
-- สินค้าไว้ให้ app.py กรอง is_fuel เองตอนวาดสัดส่วนน้ำมัน
-- app.py join dim_gasstation/dim_product เพิ่มเอง จึงไม่ denormalize ชื่อไว้ในนี้

with sales as (
    select
        s.gasstation_id,
        s.date_key,
        s.product_id,
        sum(s.quantity_sold) as quantity_sold,
        sum(s.total_price)   as sales_amount
    from {{ ref('fact_sales') }} s
    where not s.is_data_quality_flagged
    group by 1, 2, 3
),

station_daily as (
    select gasstation_id, date_key, sum(sales_amount) as station_sales_amount
    from sales
    group by 1, 2
),

ranked_station as (
    select
        *,
        dense_rank() over (
            partition by date_key order by station_sales_amount desc
        ) as station_day_rank
    from station_daily
)

select
    d.date_day,
    r.gasstation_id,
    s.product_id,
    r.station_day_rank,
    r.station_sales_amount,
    s.sales_amount,
    s.quantity_sold,
    s.sales_amount / nullif(r.station_sales_amount, 0) as pct_of_station_day
from ranked_station r
join sales s
    on r.gasstation_id = s.gasstation_id
   and r.date_key = s.date_key
join {{ ref('dim_date') }} d
    on r.date_key = d.date_key