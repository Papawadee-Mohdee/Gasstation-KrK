{{ config(materialized='table') }}
 
with tank_snapshot as (
    select f.gasstation_id, f.tank_id, f.date_key, f.hour_of_day,
           f.remaining_quantity, t.capacity_liters,
           f.remaining_quantity / nullif(t.capacity_liters, 0) as level_ratio,
           row_number() over (
               partition by f.tank_id, f.date_key, f.hour_of_day
               order by f.transaction_id desc
           ) as rn   -- แถวสุดท้ายของชั่วโมงนั้นต่อถัง เมื่อเวลาเท่ากันยึด transaction_id
    from {{ ref('fact_inventory_transaction') }} f
    join {{ ref('dim_tank') }} t
        on f.tank_id = t.tank_id
       and f.date_key between cast(strftime(t.valid_from,'%Y%m%d') as integer)
                           and coalesce(cast(strftime(t.valid_to,'%Y%m%d') as integer), 99999999)
    where t.capacity_liters > 0
)
select
    gasstation_id, tank_id, date_key, hour_of_day, level_ratio,
    (level_ratio < {{ var('low_level_threshold', 0.20) }}) as is_low_level
from tank_snapshot
where rn = 1
