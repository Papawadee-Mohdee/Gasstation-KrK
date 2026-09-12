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