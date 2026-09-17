with source as (

    select * 
    from {{ source('gas_station_raw', 'invoicedetail') }}
)
select
    * replace (
        try_cast(QuantitySold as double) as QuantitySold,
        try_cast(SellingPrice as double) as SellingPrice,
        try_cast(TotalPrice as double) as TotalPrice
    ),
    current_localtimestamp() as ingestion_timestamp
from source