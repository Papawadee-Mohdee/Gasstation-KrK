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
)
select *, false as is_unknown_member from valid_stations
union all
select -1, 'Unknown Gas Station', null, null, null, null, true
