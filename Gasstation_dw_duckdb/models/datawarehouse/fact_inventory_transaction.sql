{{ config(materialized='table') }}
 
select
    it.transaction_id,
    it.tank_id,
    coalesce(t.gasstation_id, -1)               as gasstation_id,
    coalesce(bp.product_id, -1)                  as product_id,
    case when bp.product_id is null then 'unmapped' else 'approved' end
        as mapping_status,
    cast(strftime(it.transaction_day, '%Y%m%d') as integer) as date_key,
    extract(hour from it.transaction_date)::integer as hour_of_day,
    it.quantity_in,
    it.quantity_out,
    it.net_quantity,
    it.remaining_quantity,
    it.is_receipt_event,
    it.has_required_value_error                  as is_data_quality_flagged
from {{ ref('stg_InventoryTransaction') }} it
left join {{ ref('stg_StorageTank') }} t on it.tank_id = t.tank_id
left join {{ ref('bridge_tank_product') }} bp
    on it.tank_id = bp.tank_id
   and it.transaction_date >= bp.valid_from
   and (it.transaction_date < bp.valid_to or bp.valid_to is null)
