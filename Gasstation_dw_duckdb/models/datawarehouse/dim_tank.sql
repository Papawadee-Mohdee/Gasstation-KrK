{{ config(materialized='table') }}

with history as (
    select
        tank_id,
        gasstation_id,
        tank_name,
        capacity_liters,
        material_type,
        dbt_valid_from as valid_from,
        dbt_valid_to   as valid_to,
        (dbt_valid_to is null) as is_current
    from {{ ref('snap_storage_tank') }}
)
select *, false as is_unknown_member from history
union all
select
    -1, -1, 'Unknown Tank', null, null,
    timestamp '1900-01-01 00:00:00', cast(null as timestamp), true, true