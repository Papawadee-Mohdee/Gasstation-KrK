{{ config(materialized='table') }}
with valid_employees as (
    select
        employee_id,
        employee_name,
        position,
        gasstation_id as home_gasstation_id,   -- attribute เท่านั้น ไม่ใช่สถานีบันทึกบิล
        phone_number,
        email,
        start_date,
        address
    from {{ ref('stg_Employee') }}
    where not has_required_value_error
)
select *, false as is_unknown_member from valid_employees
union all
select -1, 'Unknown Employee', null, null, null, null, null, null, true
