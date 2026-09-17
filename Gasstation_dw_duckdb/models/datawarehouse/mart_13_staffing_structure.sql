{{ config(materialized='table') }}

-- Q13: โครงสร้างกำลังพลในแต่ละสถานีประกอบด้วยตำแหน่งงานใดบ้าง และตำแหน่งใดมีสัดส่วนมากที่สุด

with agg as (
    select home_gasstation_id as gasstation_id, position, count(*) as headcount
    from {{ ref('dim_employee') }}
    where home_gasstation_id is not null
    group by 1, 2
)

select
    gasstation_id,
    position,
    headcount,
    round(headcount / sum(headcount) over (partition by gasstation_id) * 100, 2) as pct_of_station_staff,
    row_number() over (partition by gasstation_id order by headcount desc) = 1 as is_dominant_position
from agg
