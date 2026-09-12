{{ config(materialized='table') }}
 
with base as (
    select s.gasstation_id, dt.iso_weekday, dt.weekday_name,
           h.hour_of_day, s.product_id, s.date_key,
           s.total_price, s.quantity_sold, s.invoice_id
    from {{ ref('fact_sales') }} s
    join {{ ref('dim_date') }} dt on s.date_key = dt.date_key
    join {{ ref('dim_hour') }} h  on s.hour_of_day = h.hour_of_day
    join {{ ref('dim_product') }} p on s.product_id = p.product_id
    where p.is_fuel and not s.is_data_quality_flagged
),
observed_hours as (
    -- นับ date-hour ที่แตกต่างกันจริงในกลุ่ม ไม่ใช่จำนวนธุรกรรม
    select gasstation_id, iso_weekday, hour_of_day, product_id,
           count(distinct date_key) as observed_hours
    from base group by 1, 2, 3, 4
)
select
    b.gasstation_id, b.iso_weekday, b.weekday_name, b.hour_of_day, b.product_id,
    count(distinct b.invoice_id)         as invoice_count,
    sum(b.quantity_sold)                 as quantity_sold,
    o.observed_hours,
    sum(b.quantity_sold) / nullif(o.observed_hours, 0) as avg_quantity_per_observed_hour
from base b
join observed_hours o
    on b.gasstation_id = o.gasstation_id and b.iso_weekday = o.iso_weekday
   and b.hour_of_day   = o.hour_of_day  and b.product_id  = o.product_id
group by 1, 2, 3, 4, 5, o.observed_hours
