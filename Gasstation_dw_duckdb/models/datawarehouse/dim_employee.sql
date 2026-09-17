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
),

unique_employees as (
    select *,
        row_number() over (partition by employee_id) as row_num
    from valid_employees
)

select * exclude (row_num), current_localtimestamp() as insertion_timestamp, false as is_unknown_member
from unique_employees
where row_num = 1
union all
select -1, 'Unknown Employee', null, null, null, null, null, null, current_localtimestamp(), true
