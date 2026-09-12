{{ config(materialized='table') }}

with valid_customers as (
    select
        c.customer_id,
        c.customer_name,
        c.address,
        c.phone_number,
        c.email,
        c.notes,
        c.vehicle_type,
        c.vehicle_type_key,
        c.license_plate,
        coalesce(cast(v.vehicle_category as varchar), 'Unknown') as vehicle_category
    from {{ ref('stg_Customer') }} c
    left join {{ ref('ref_vehicle_category') }} v
        on c.vehicle_type_key = v.vehicle_type_key
    where not c.has_required_value_error
)
select *, false as is_unknown_member from valid_customers
union all
select
    -1, 'Unknown Customer', null, null, null, null,
    null, null, null, 'Unknown', true
