{{ config(materialized='view') }}
with typed as (
select
  {{ gas_id('EmployeeID') }} as employee_id,
  {{ gas_text('EmployeeName') }} as employee_name,
  {{ gas_text('Position') }} as position,
  {{ gas_id('GasStationID') }} as gasstation_id,
  {{ gas_text('PhoneNumber') }} as phone_number,
  {{ gas_text('Email') }} as email,
  cast({{ gas_ts('StartDate') }} as date) as start_date,
  {{ gas_text('Address') }} as address,
  {{ gas_meta('Employee.csv', 'EmployeeID') }}
from {{ source('gas_station_raw', 'employee') }} s
)
select *,
  (employee_id is null
   or gasstation_id is null
   or start_date is null)
    as has_required_value_error
from typed