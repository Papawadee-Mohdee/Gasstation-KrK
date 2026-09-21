{{ config(materialized='table') }}

-- Q9: ในแต่ละวัน สถานีบริการใดทำยอดขายได้สูงสุดและต่ำสุด และส่วนต่างห่างกันกี่เท่า

with daily_station as (
    select gasstation_id, date_key, sum(total_sales_value) as daily_sales
    from {{ ref('int_sales_daily') }}
    group by 1, 2
),

ranked as (
    select *,
        row_number() over (partition by date_key order by daily_sales desc) as rnk_desc,
        row_number() over (partition by date_key order by daily_sales asc)  as rnk_asc
    from daily_station
),

top_bottom as (
    select
        date_key,
        max(case when rnk_desc = 1 then gasstation_id end) as top_gasstation_id,
        max(case when rnk_desc = 1 then daily_sales end)   as top_sales,
        max(case when rnk_asc  = 1 then gasstation_id end) as bottom_gasstation_id,
        max(case when rnk_asc  = 1 then daily_sales end)   as bottom_sales
    from ranked
    group by date_key
)

select
    date_key,
    top_gasstation_id,
    top_sales,
    bottom_gasstation_id,
    bottom_sales,
    round(top_sales / nullif(bottom_sales, 0), 2) as sales_multiple
from top_bottom
