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
test: ห้ามช่วงเวลาซ้อนกันภายในถังเดียวกัน
-- tests/assert_bridge_tank_product_no_overlap.sql
-- คืนแถว = มีปัญหา (test ต้อง fail ถ้าพบผลลัพธ์)
select a.tank_id, a.valid_from as a_from, b.valid_from as b_from
from {{ ref('bridge_tank_product') }} a
join {{ ref('bridge_tank_product') }} b
    on a.tank_id = b.tank_id
   and a.product_id <> b.product_id
   and a.valid_from < coalesce(b.valid_to, timestamp '9999-12-31')
   and coalesce(a.valid_to, timestamp '9999-12-31') > b.valid_from
