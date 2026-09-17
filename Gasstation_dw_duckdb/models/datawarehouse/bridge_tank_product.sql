{{ config(materialized='table') }}

-- การจับคู่ถัง → สินค้า มาจาก 2 แหล่ง ตามลำดับความน่าเชื่อถือ
-- 1) manual  : stg_TankProductMap ที่ผ่านการรีวิวแล้ว (review_status = 'approved')
-- 2) derived : เมื่อถังไม่มี manual mapping ให้อนุมานจาก tank_name ('<ชื่อผลิตภัณฑ์> Tank')

with manual as (
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
),

derived as (
    select
        t.tank_id,
        p.product_id,
        timestamp '1900-01-01 00:00:00' as valid_from,
        cast(null as timestamp)         as valid_to,
        'derived_from_tank_name'        as mapping_method,
        cast(null as varchar)           as reviewed_by,
        cast(null as timestamp)         as reviewed_at
    from {{ ref('dim_tank') }} t
    join {{ ref('dim_product') }} p
        on trim(replace(t.tank_name, 'Tank', '')) = p.product_name
    where t.tank_id not in (select tank_id from manual)
)

select * from manual
union all
select * from derived
