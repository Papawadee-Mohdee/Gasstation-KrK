{{ config(materialized='table') }}

with valid_products as (
    select
        p.product_id,
        p.product_name,
        p.product_type,
        p.supplier,
        p.unit_price,
        p.stock_quantity,
        coalesce(pol.is_fuel, false) as is_fuel,
        coalesce(cast(pol.unit_of_measure as varchar), 'unverified') as unit_of_measure
    from {{ ref('stg_Product') }} p
    left join {{ ref('ref_product_policy') }} pol
        on p.product_id = pol.product_id
    where not p.has_required_value_error
)
select *, false as is_unknown_member from valid_products
union all
select -1, 'Unknown Product', null, null, null, null, false, 'unverified', true
