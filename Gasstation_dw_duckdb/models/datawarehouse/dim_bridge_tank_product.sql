{{ config(materialized='table') }}

select
    tank_id,
    product_id,
    valid_from,
    valid_to,
    review_status
from {{ ref('stg_TankProductMap') }}