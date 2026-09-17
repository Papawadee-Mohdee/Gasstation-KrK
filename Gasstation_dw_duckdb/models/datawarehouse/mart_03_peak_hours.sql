{{ config(materialized='table') }}

-- Q3: ช่วงเวลาใดในรอบวันที่แต่ละสถานีมีปริมาณการออกบิลหนาแน่นที่สุด (Peak Hours)

with hourly as (
    select gasstation_id, hour_of_day, count(*) as invoice_count
    from {{ ref('fact_invoice') }}
    group by 1, 2
)

select
    h.gasstation_id,
    h.hour_of_day,
    d.day_part,
    h.invoice_count,
    row_number() over (partition by h.gasstation_id order by h.invoice_count desc) as rnk
from hourly h
join {{ ref('dim_hour') }} d on h.hour_of_day = d.hour_of_day
