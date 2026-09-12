stg Product sql
{{ config(materialized='view') }}
with typed as (
select
  {{ gas_id('ProductID') }} as product_id,
  {{ gas_text('ProductName') }} as product_name,
  {{ gas_num('UnitPrice') }} as unit_price,
  {{ gas_text('ProductType') }} as product_type,
  {{ gas_text('Supplier') }} as supplier,
  {{ gas_num('StockQuantity') }} as stock_quantity,
  {{ gas_meta('Product.csv', 'ProductID') }}
from {{ source('gas_station_raw', 'product') }} s
)
select *,
  (product_id is null
   or unit_price is null
   or stock_quantity is null)
    as has_required_value_error
from typed
