{{ config(materialized='table') }}
 
with base as (
    select fi.payment_method_key, c.vehicle_category, fi.gasstation_id,
           fi.hour_of_day, fi.invoice_id, fi.total_amount
    from {{ ref('fact_invoice') }} fi
    join {{ ref('dim_customer') }} c on fi.customer_id = c.customer_id
    where not fi.is_data_quality_flagged
),
group_totals as (
    select gasstation_id, hour_of_day, vehicle_category,
           count(invoice_id) as group_invoice_count
    from base group by 1, 2, 3
)
select
    b.payment_method_key, b.vehicle_category, b.gasstation_id, b.hour_of_day,
    count(b.invoice_id)                                as invoice_count,
    sum(b.total_amount) / nullif(count(b.invoice_id),0) as avg_amount_per_invoice,
    count(b.invoice_id)::decimal / nullif(g.group_invoice_count, 0)
        as share_of_payment_method_in_group
from base b
join group_totals g
    on b.gasstation_id = g.gasstation_id and b.hour_of_day = g.hour_of_day
   and b.vehicle_category = g.vehicle_category
group by 1, 2, 3, 4, g.group_invoice_count
