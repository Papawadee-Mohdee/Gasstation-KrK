{{ config(materialized='table') }}

with source as (

    select
        TankID as tank_id,
        GasStationID as gasstation_id,
        TankName as tank_name,
        Capacity as capacity_liters,
        MaterialType as material_type,
        CurrentQuantity as current_quantity,
        current_localtimestamp() as insertion_timestamp
    from {{ ref('stg_StorageTank') }}
    where TankID is not null

),

unique_source as (
    select *,
        row_number() over (partition by tank_id) as row_num
    from source
)

select *
exclude (row_num)
from unique_source
where row_num = 1
