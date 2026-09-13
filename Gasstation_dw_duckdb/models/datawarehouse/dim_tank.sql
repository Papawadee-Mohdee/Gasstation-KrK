{{ config(materialized='table') }}

-- SCD Type 2 ของถังเก็บน้ำมัน
--
-- ปัญหาที่แก้: dbt_valid_from ของ snapshot คือ "เวลาที่รัน dbt snapshot ครั้งแรก"
-- ไม่ใช่เวลาที่ถังเริ่มมีอยู่จริง เมื่อ snapshot ถูกรันปี 2026 แต่ธุรกรรมเป็นปี 2024
-- เงื่อนไข transaction_timestamp >= valid_from จึงไม่เป็นจริงสักแถว
-- ทำให้ fact_inventory_transaction หา gasstation_id ไม่เจอและติดธงทั้งหมด
--
-- วิธีแก้: เวอร์ชันแรกสุดของแต่ละถังให้มีผลย้อนหลังถึง 1900-01-01
-- (ถือว่าถังมีอยู่มาก่อนข้อมูลที่เรามี) ส่วนเวอร์ชันถัดไปยังใช้เวลาจริง
-- ที่ snapshot ตรวจพบการเปลี่ยนแปลง ซึ่งเป็นพฤติกรรมมาตรฐานของ SCD2

with history as (
    select
        tank_id,
        gasstation_id,
        tank_name,
        capacity_liters,
        material_type,
        case
            when row_number() over (
                     partition by tank_id order by dbt_valid_from
                 ) = 1
                then timestamp '1900-01-01 00:00:00'
            else dbt_valid_from
        end                        as valid_from,
        dbt_valid_to               as valid_to,
        (dbt_valid_to is null)     as is_current
    from {{ ref('snap_storage_tank') }}
)

select *, false as is_unknown_member from history
union all
select
    -1, -1, 'Unknown Tank', null, null,
    timestamp '1900-01-01 00:00:00', cast(null as timestamp), true, true