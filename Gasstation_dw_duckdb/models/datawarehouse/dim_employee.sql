{{ config(materialized='table') }}

with source as (

    select
        EmployeeID as employee_id,
        EmployeeName as employee_name,
        Position as position,
        GasStationID as home_gasstation_id,
        PhoneNumber as phone_number,
        Email as email,
        cast(StartDate as date) as start_date,
        Address as address,
        current_localtimestamp() as insertion_timestamp
    from {{ ref('stg_Employee') }}
    where EmployeeID is not null

),

unique_source as (
    select *,
        row_number() over (partition by employee_id) as row_num
    from source
)

select *
exclude (row_num)
from unique_source
where row_num = 1
