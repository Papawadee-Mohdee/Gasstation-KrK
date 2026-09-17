{{ config(materialized='table') }}

-- Q10: วันใดในรอบสัปดาห์ที่แต่ละสถานีทำยอดขายเฉลี่ยได้สูงที่สุด

with daily as (
    select f.gasstation_id, d.iso_weekday, d.weekday_name, f.date_key,
        sum(f.total_amount) as daily_sales
    from {{ ref('fact_invoice') }} f
    join {{ ref('dim_date') }} d on f.date_key = d.date_key
    group by 1, 2, 3, 4
),

by_weekday as (
    select gasstation_id, iso_weekday, weekday_name, avg(daily_sales) as avg_sales
    from daily
    group by 1, 2, 3
)

select
    gasstation_id,
    iso_weekday,
    weekday_name,
    avg_sales,
    row_number() over (partition by gasstation_id order by avg_sales desc) as rnk
from by_weekday
