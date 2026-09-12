{{ config(materialized='view') }}
with typed as (
select
  {{ gas_id('CustomerID') }} as customer_id,
  {{ gas_text('CustomerName') }} as customer_name,
  {{ gas_text('Address') }} as address,
  {{ gas_text('PhoneNumber') }} as phone_number,
  {{ gas_text('Email') }} as email,
  {{ gas_text('Notes') }} as notes,
  {{ gas_text('VehicleTypeName') }} as vehicle_type,
  {{ gas_text('LicensePlate') }} as license_plate,
  {{ gas_meta('Customer.csv', 'CustomerID') }}
from {{ source('gas_station_raw', 'customer') }} s
)
select *,
  (customer_id is null)
    as has_required_value_error,
  lower(vehicle_type) as vehicle_type_key
from typed