{{ config(materialized='table') }}

-- Q2: แต่ละสถานีมีช่วงเวลาขายหนาแน่นต่างกันอย่างไร เมื่อแยกวันในสัปดาห์และชนิดน้ำมัน?
-- เฉพาะสินค้าที่เป็นน้ำมัน (is_fuel) ตามที่คำถามระบุ "ชนิดน้ำมัน"
-- denormalize gasstation_name ไว้ในตารางนี้เอง เพราะ app.py query ตรงไม่ join dim เพิ่ม

with base as (
    select
        f.gasstation_id,
        f.hour_of_day,
        d.weekday_name,
        d.iso_weekday,
        f.date_key,
        count(distinct f.invoice_id) as bills_for_date_hour,
        sum(f.quantity_sold)         as quantity_for_date_hour
    from {{ ref('fact_sales') }} f
    join {{ ref('dim_date') }} d on f.date_key = d.date_key
    join {{ ref('dim_product') }} p on f.product_id = p.product_id
    where p.is_fuel
      and not f.is_data_quality_flagged
    group by 1, 2, 3, 4, 5
),

agg as (
    select
        gasstation_id,
        hour_of_day,
        weekday_name,
        iso_weekday,
        sum(bills_for_date_hour)    as bill_count,
        count(distinct date_key)    as observed_occurrences,
        sum(quantity_for_date_hour) as total_quantity
    from base
    group by 1, 2, 3, 4
)

select
    a.gasstation_id,
    g.gasstation_name,
    a.hour_of_day,
    a.weekday_name,
    a.iso_weekday,
    a.bill_count,
    a.total_quantity / nullif(a.observed_occurrences, 0) as avg_qty_per_hour_observed
from agg a
join {{ ref('dim_gasstation') }} g
    on a.gasstation_id = g.gasstation_id