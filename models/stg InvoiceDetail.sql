stg InvoiceDetail sql
{{ config(materialized='view') }}
with typed as (
select
  {{ gas_id('InvoiceDetailID') }} as invoice_detail_id,
  {{ gas_id('InvoiceID') }} as invoice_id,
  {{ gas_id('ProductID') }} as product_id,
  {{ gas_num('QuantitySold') }} as quantity_sold,
  {{ gas_num('SellingPrice') }} as selling_price,
  {{ gas_num('TotalPrice') }} as total_price,
  {{ gas_meta('InvoiceDetail.csv', 'InvoiceDetailID') }}
from {{ source('gas_station_raw', 'invoicedetail') }} s
)
select *,
  (invoice_detail_id is null
   or invoice_id is null
   or product_id is null
   or quantity_sold is null
   or selling_price is null
   or total_price is null)
    as has_required_value_error,
  quantity_sold * selling_price as calculated_total_price,
  total_price - quantity_sold * selling_price
    as line_amount_difference
from typed
