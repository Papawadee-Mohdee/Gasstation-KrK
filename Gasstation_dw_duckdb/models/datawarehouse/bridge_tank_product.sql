{{ config(materialized='table') }}

-- การจับคู่ถัง → สินค้า มาจาก 2 แหล่ง ตามลำดับความน่าเชื่อถือ
--
-- 1) manual  : stg_TankProductMap ที่ผ่านการรีวิวแล้ว (review_status = 'approved')
--              ถือเป็น override ใช้ก่อนเสมอ เพราะมีคนยืนยันด้วยมือ
-- 2) derived : เมื่อถังไม่มี manual mapping ให้อนุมานจาก TankName
--              ซึ่งมีรูปแบบ '<ชื่อผลิตภัณฑ์> Tank' เช่น 'RON95-III Tank'
--
-- valid_from ของฝั่ง derived ตั้งเป็น 1900-01-01 เพราะถังผูกกับชนิดน้ำมัน
-- ตั้งแต่ติดตั้ง ไม่ใช่เพิ่งผูกตอนรัน dbt ถ้าใช้เวลารัน ธุรกรรมย้อนหลังทั้งหมด
-- จะหลุดออกนอกช่วง validity และถูกติดธงคุณภาพข้อมูลทิ้งทั้งยวง

with manual as (
    select
        tank_id,
        product_id,
        cast(valid_from as timestamp)     as valid_from,
        cast(valid_to as timestamp)       as valid_to,
        cast(mapping_method as varchar)   as mapping_method,
        cast(reviewed_by as varchar)      as reviewed_by,
        cast(reviewed_at as timestamp)    as reviewed_at
    from {{ ref('stg_TankProductMap') }}
    where review_status = 'approved'
      and not invalid_valid_to
),

derived as (
    select
        t.tank_id,
        p.product_id,
        timestamp '1900-01-01 00:00:00'   as valid_from,
        cast(null as timestamp)           as valid_to,
        'derived_from_tank_name'          as mapping_method,
        cast(null as varchar)             as reviewed_by,
        cast(null as timestamp)           as reviewed_at
    from {{ ref('dim_tank') }} t
    join {{ ref('dim_product') }} p
        on trim(replace(t.tank_name, 'Tank', '')) = p.product_name
    where t.is_current
      and t.tank_id <> -1
      and t.tank_id not in (select tank_id from manual)
)

select * from manual
union all
select * from derived