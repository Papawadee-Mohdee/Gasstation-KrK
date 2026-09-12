{{ config(materialized='view') }}
with typed as (
select
  {{ gas_id('InvoiceID') }} as invoice_id,
  {{ gas_id('CustomerID') }} as customer_id,
  {{ gas_id('EmployeeID') }} as employee_id,
  {{ gas_id('GasStationID') }} as gasstation_id,
  {{ gas_ts('IssueDate') }} as issue_date,
  {{ gas_num('TotalAmount') }} as total_amount,
  {{ gas_text('PaymentMethod') }} as payment_method,
  {{ gas_meta('Invoice.csv', 'InvoiceID') }}
from {{ source('gas_station_raw', 'invoice') }} s
)
select *,
  (invoice_id is null
   or customer_id is null
   or employee_id is null
   or gasstation_id is null
   or issue_date is null
   or total_amount is null)
    as has_required_value_error,
  cast(issue_date as date) as issue_day,
  date_trunc('hour', issue_date) as issue_hour,
  extract(isodow from issue_date)::integer as issue_weekday,
  lower(payment_method) as payment_method_key
from typed
