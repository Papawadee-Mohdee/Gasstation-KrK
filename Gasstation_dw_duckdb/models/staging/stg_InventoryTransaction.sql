with source as (

    select * 
    from {{ source('gas_station_raw', 'inventorytransaction') }}
)
select
    * replace (
        try_cast(TankID as bigint) as TankID,
        try_cast(QuantityIn as double) as QuantityIn,
        try_cast(QuantityOut as double) as QuantityOut,
        try_cast(RemainingQuantity as double) as RemainingQuantity
    ),
    current_localtimestamp() as ingestion_timestamp
from source