{{ config(materialized='table') }}

-- Q1: ยอดขายเฉลี่ยรายวันของแต่ละสถานี และจัดกลุ่มสถานีตามระดับยอดขาย (Sales Tiering)

with daily_station as (
    select gasstation_id, date_key, sum(total_sales_value) as daily_sales
    from {{ ref('int_sales_daily') }}
    group by 1, 2
),

station_avg as (
    select gasstation_id, avg(daily_sales) as avg_daily_sales
    from daily_station
    group by 1
)

select
    gasstation_id,
    avg_daily_sales,
    case ntile(3) over (order by avg_daily_sales desc)
        when 1 then 'High'
        when 2 then 'Medium'
        else 'Low'
    end as sales_tier
from station_avg
