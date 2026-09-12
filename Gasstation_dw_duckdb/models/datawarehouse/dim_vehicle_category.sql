{{ config(materialized='table') }}
 
with mapped as (
    select
        vehicle_type_key,
        vehicle_type_label,
        vehicle_category
    from {{ ref('ref_vehicle_category') }}
)
select *, false as is_unknown_member from mapped
union all
select 'unknown', 'Unknown', 'Unknown', true
