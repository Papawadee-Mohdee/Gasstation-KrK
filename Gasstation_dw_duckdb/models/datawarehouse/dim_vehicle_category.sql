{{ config(materialized='table') }}

select
    vehicle_type_key,
    vehicle_type_label,
    vehicle_category,
    current_localtimestamp() as insertion_timestamp
from {{ ref('ref_vehicle_category') }}
