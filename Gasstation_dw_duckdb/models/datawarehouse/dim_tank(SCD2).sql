# snapshots/snap_storage_tank.sql
{% snapshot snap_storage_tank %}
{{
    config(
        target_schema='snapshots',
        unique_key='tank_id',
        strategy='check',
        check_cols=['gasstation_id', 'tank_name', 'capacity_liters', 'material_type'],
        invalidate_hard_deletes=True
    )
}}
select
    tank_id,
    gasstation_id,
    tank_name,
    capacity_liters,
    material_type
from {{ ref('stg_StorageTank') }}
where not has_required_value_error
{% endsnapshot %}
# models/warehouse/dim_tank.sql
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
