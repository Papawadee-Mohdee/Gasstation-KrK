{{ config(materialized='view') }}
select
  {{ gas_id('tank_id') }} as tank_id,
  {{ gas_id('product_id') }} as product_id,
  {{ gas_ts('valid_from') }} as valid_from,
  {{ gas_ts('valid_to') }} as valid_to,
  {{ gas_text('mapping_method') }} as mapping_method,
  {{ gas_text('review_status') }} as review_status,
  {{ gas_text('reviewed_by') }} as reviewed_by,
  {{ gas_ts('reviewed_at') }} as reviewed_at,
  ({{ gas_text('valid_to') }} is not null
   and {{ gas_ts('valid_to') }} is null) as invalid_valid_to
from {{ ref('ref_tank_product_map') }}