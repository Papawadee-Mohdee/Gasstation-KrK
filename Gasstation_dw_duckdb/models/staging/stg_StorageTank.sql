{{ config(materialized='view') }}
with typed as (
select
  {{ gas_id('TankID') }} as tank_id,
  {{ gas_id('GasStationID') }} as gasstation_id,
  {{ gas_text('TankName') }} as tank_name,
  {{ gas_num('Capacity') }} as capacity_liters,
  {{ gas_text('MaterialType') }} as material_type,
  {{ gas_num('CurrentQuantity') }} as current_quantity,
  {{ gas_meta('StorageTank.csv', 'TankID') }}
from {{ source('gas_station_raw', 'storagetank') }} s
)
select *,
  (tank_id is null
   or gasstation_id is null
   or capacity_liters is null
   or current_quantity is null)
    as has_required_value_error
from typed
