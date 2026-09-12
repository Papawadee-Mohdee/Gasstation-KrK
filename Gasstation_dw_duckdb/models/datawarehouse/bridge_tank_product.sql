{{ config(materialized='table') }}

select
    tank_id,
    product_id,
    valid_from,
    valid_to,
    mapping_method,
    reviewed_by,
    reviewed_at
from {{ ref('stg_TankProductMap') }}
where review_status = 'approved'
  and not invalid_valid_to
