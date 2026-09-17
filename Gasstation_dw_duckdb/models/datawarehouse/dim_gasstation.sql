{{ config(materialized='table') }}
 
with valid_stations as (
    select
        gasstation_id,
        gasstation_name,
        address,
        phone_number,
        email,
        notes
    from {{ ref('stg_GasStation') }}
    where not has_required_value_error
),

unique_stations as (
    select *,
        row_number() over (partition by gasstation_id) as row_num
    from valid_stations
)

select * exclude (row_num), current_localtimestamp() as insertion_timestamp, false as is_unknown_member
from unique_stations
where row_num = 1
union all
select -1, 'Unknown Gas Station', null, null, null, null, current_localtimestamp(), true
