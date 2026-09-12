{% snapshot dim_tank_scd2 %}

{{
    config(
      target_schema='main',
      unique_key='tank_id',
      strategy='check',
      check_cols=['capacity_liters', 'material_type', 'gasstation_id']
    )
}}

select * from {{ ref('stg_StorageTank') }}

{% endsnapshot %}