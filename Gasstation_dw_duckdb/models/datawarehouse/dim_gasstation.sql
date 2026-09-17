{{ config(materialized='table') }}

with source as (

    select
        GasStationID as gasstation_id,
        GasStationName as gasstation_name,
        Address as address,
        PhoneNumber as phone_number,
        Email as email,
        Notes as notes,
        current_localtimestamp() as insertion_timestamp
    from {{ ref('stg_GasStation') }}
    where GasStationID is not null

),

unique_source as (
    select *,
        row_number() over (partition by gasstation_id) as row_num
    from source
)

select *
exclude (row_num)
from unique_source
where row_num = 1
