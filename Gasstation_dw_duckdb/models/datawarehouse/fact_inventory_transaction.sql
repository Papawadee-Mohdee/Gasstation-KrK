{{ config(materialized='table') }}

select
    t.TransactionID as transaction_id,
    cast(strftime(cast(t.TransactionDate as date), '%Y%m%d') as integer) as date_key,
    extract(hour from cast(t.TransactionDate as timestamp))::integer as hour_of_day,
    s.GasStationID as gasstation_id,
    t.TankID as tank_id,
    bp.product_id as product_id,
    t.QuantityIn as quantity_in,
    t.QuantityOut as quantity_out,
    t.RemainingQuantity as remaining_quantity
from {{ ref('stg_InventoryTransaction') }} t
join {{ ref('stg_StorageTank') }} s
    on t.TankID = s.TankID
left join {{ ref('bridge_tank_product') }} bp
    on t.TankID = bp.tank_id
    and cast(t.TransactionDate as timestamp) >= bp.valid_from
    and (bp.valid_to is null or cast(t.TransactionDate as timestamp) < bp.valid_to)
where t.TransactionID is not null
