with source as (

    select * 
    from {{ source('gas_station_raw', 'storagetank') }}
)
select
    * replace (
        try_cast(TankID as bigint) as TankID,
        try_cast(Capacity as double) as Capacity,
        try_cast(CurrentQuantity as double) as CurrentQuantity
    ),
    current_localtimestamp() as ingestion_timestamp
from source