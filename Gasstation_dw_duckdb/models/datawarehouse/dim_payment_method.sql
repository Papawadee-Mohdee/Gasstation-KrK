{{ config(materialized='table') }}

with source as (

    select distinct
        lower(PaymentMethod) as payment_method_key,
        PaymentMethod as payment_method_label
    from {{ ref('stg_Invoice') }}
    where PaymentMethod is not null

)

select *,
    current_localtimestamp() as insertion_timestamp
from source
