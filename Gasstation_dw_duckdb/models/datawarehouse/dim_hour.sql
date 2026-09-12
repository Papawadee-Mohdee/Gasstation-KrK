{{ config(materialized='table') }}
 
with hours as (
    select unnest(generate_series(0, 23)) as hour_of_day
)
select
    h.hour_of_day,
    coalesce(b.day_part_label, default_bucket.day_part_label) as day_part
from hours h
left join {{ ref('ref_hour_bucket') }} b
    on h.hour_of_day = b.hour_of_day
left join (
    select
        h2.hour_of_day,
        case
            when h2.hour_of_day between 6  and 10 then 'เช้า'
            when h2.hour_of_day between 11 and 13 then 'เที่ยง'
            when h2.hour_of_day between 14 and 17 then 'บ่าย'
            when h2.hour_of_day between 18 and 21 then 'เย็น'
            else 'กลางคืน'
        end as day_part_label
    from hours h2
) default_bucket
    on h.hour_of_day = default_bucket.hour_of_day
