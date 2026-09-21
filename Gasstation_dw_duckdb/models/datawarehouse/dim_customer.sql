{{ config(materialized='table') }}

with source as (

    select
        c.CustomerID as customer_id,
        c.CustomerName as customer_name,
        c.Address as address,
        c.PhoneNumber as phone_number,
        c.Email as email,
        c.Notes as notes,
        c.VehicleTypeName as vehicle_type,
        lower(c.VehicleTypeName) as vehicle_type_key,
        coalesce(v.vehicle_category, 'Unknown') as vehicle_category,
        c.LicensePlate as license_plate,
        current_localtimestamp() as insertion_timestamp
    from {{ ref('stg_Customer') }} c
    left join {{ ref('ref_vehicle_category') }} v
        on lower(c.VehicleTypeName) = v.vehicle_type_key
    where c.CustomerID is not null

),

unique_source as (
    select *,
        row_number() over (partition by customer_id) as row_num
    from source
)

select *
exclude (row_num)
from unique_source
where row_num = 1
