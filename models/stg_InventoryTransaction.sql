{{ config(materialized='view') }}
with typed as (
select
  {{ gas_id('TransactionID') }} as transaction_id,
  {{ gas_id('TankID') }} as tank_id,
  {{ gas_num('QuantityIn') }} as quantity_in,
  {{ gas_num('QuantityOut') }} as quantity_out,
  {{ gas_num('RemainingQuantity') }} as remaining_quantity,
  {{ gas_ts('TransactionDate') }} as transaction_date,
  {{ gas_meta('InventoryTransaction.csv', 'TransactionID') }}
from {{ source('gas_station_raw', 'inventorytransaction') }} s
)
select *,
  (transaction_id is null
   or tank_id is null
   or quantity_in is null
   or quantity_out is null
   or remaining_quantity is null
   or transaction_date is null)
    as has_required_value_error,
  cast(transaction_date as date) as transaction_day,
  date_trunc('hour', transaction_date) as transaction_hour,
  quantity_in - quantity_out as net_quantity,
  quantity_in > 0 as is_receipt_event
from typed
