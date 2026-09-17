with source as (

    select
        tank_id,
        product_id,
        try_cast(valid_from as timestamp) as valid_from,
        try_cast(valid_to as timestamp) as valid_to,
        mapping_method,
        review_status,
        reviewed_by,
        try_cast(reviewed_at as timestamp) as reviewed_at
    from {{ ref('ref_tank_product_map') }}
)
select
    *,
    current_localtimestamp() as ingestion_timestamp
from source
