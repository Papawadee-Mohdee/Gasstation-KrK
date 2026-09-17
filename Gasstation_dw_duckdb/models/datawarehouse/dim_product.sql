{{ config(materialized='table') }}

with source as (

    select
        p.ProductID as product_id,
        p.ProductName as product_name,
        p.ProductType as product_type,
        p.Supplier as supplier,
        p.UnitPrice as unit_price,
        p.StockQuantity as stock_quantity,
        coalesce(pol.is_fuel, false) as is_fuel,
        coalesce(pol.unit_of_measure, 'unverified') as unit_of_measure,
        current_localtimestamp() as insertion_timestamp
    from {{ ref('stg_Product') }} p
    left join {{ ref('ref_product_policy') }} pol
        on p.ProductID = pol.product_id
    where p.ProductID is not null

),

unique_source as (
    select *,
        row_number() over (partition by product_id) as row_num
    from source
)

select *
exclude (row_num)
from unique_source
where row_num = 1
