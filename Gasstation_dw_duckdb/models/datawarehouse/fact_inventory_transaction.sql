{{ config(materialized='table') }}

with txn as (
    select
        t.transaction_id,
        t.tank_id,
        t.transaction_day,
        t.transaction_hour,

-- ...existing code...
        coalesce(
            cast(t.transaction_hour as timestamp),
            cast(t.transaction_day as timestamp)
        ) as transaction_timestamp,
-- ...existing code...

        t.quantity_in,
        t.quantity_out,
        t.remaining_quantity,
        t.has_required_value_error as txn_error
    from {{ ref('stg_InventoryTransaction') }} t
),

tank_at_time as (
    select tank_id, gasstation_id, valid_from, valid_to
    from {{ ref('dim_tank') }}
    where tank_id <> -1
),

product_at_time as (
    select tank_id, product_id, valid_from, valid_to
    from {{ ref('bridge_tank_product') }}
)

select
    x.transaction_id,
    d.date_key,
    x.transaction_hour as hour_of_day,
    coalesce(tk.gasstation_id, -1) as gasstation_id,
    x.tank_id,
    coalesce(pm.product_id, -1) as product_id,
    x.quantity_in,
    x.quantity_out,
    x.remaining_quantity,
    (
        x.txn_error
        or tk.gasstation_id is null
        or pm.product_id is null
    ) as is_data_quality_flagged
from txn x
join {{ ref('dim_date') }} d
    on x.transaction_day = d.date_day
left join tank_at_time tk
    on x.tank_id = tk.tank_id
   and x.transaction_timestamp >= tk.valid_from
   and (tk.valid_to is null or x.transaction_timestamp < tk.valid_to)
left join product_at_time pm
    on x.tank_id = pm.tank_id
   and x.transaction_timestamp >= pm.valid_from
   and (pm.valid_to is null or x.transaction_timestamp < pm.valid_to)