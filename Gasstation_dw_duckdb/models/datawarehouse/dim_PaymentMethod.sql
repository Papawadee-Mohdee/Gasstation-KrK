{{ config(materialized='table') }}
 
with distinct_methods as (
    select distinct
        payment_method_key,
        payment_method as payment_method_label
    from {{ ref('stg_Invoice') }}
    where not has_required_value_error
      and payment_method_key is not null
)
select *, false as is_unknown_member from distinct_methods
union all
select 'unknown', 'Unknown', true
