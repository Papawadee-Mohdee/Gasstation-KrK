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
),

unique_customers as (
    select *,
        row_number() over (partition by customer_id) as row_num
    from valid_customers
)

select * exclude (row_num), current_localtimestamp() as insertion_timestamp, false as is_unknown_member
from unique_customers
where row_num = 1
union all
select
    -1, 'Unknown Customer', null, null, null, null,
    null, null, null, 'Unknown', current_localtimestamp(), true
