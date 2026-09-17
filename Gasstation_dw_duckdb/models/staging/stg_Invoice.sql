with source as (

    select * 
    from {{ source('gas_station_raw', 'invoice') }}
)
select
    * replace (try_cast(TotalAmount as double) as TotalAmount),
    current_localtimestamp() as ingestion_timestamp
from source