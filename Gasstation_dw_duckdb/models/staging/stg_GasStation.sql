{{ config(materialized='view') }}
with typed as (
select
  {{ gas_id('GasStationID') }} as gasstation_id,
  {{ gas_text('GasStationName') }} as gasstation_name,
  {{ gas_text('Address') }} as address,
  {{ gas_text('PhoneNumber') }} as phone_number,
  {{ gas_text('Email') }} as email,
  {{ gas_text('Notes') }} as notes,
  {{ gas_meta('GasStation.csv', 'GasStationID') }}
from {{ source('gas_station_raw', 'gasstation') }} s
)
select *,
  (gasstation_id is null)
    as has_required_value_error
from typed

