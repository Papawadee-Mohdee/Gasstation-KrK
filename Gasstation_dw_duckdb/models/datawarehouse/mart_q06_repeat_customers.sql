{{ config(materialized='table') }}
 
with customer_station_day as (
    select distinct gasstation_id, customer_id, date_key
    from {{ ref('fact_invoice') }}
    where not is_data_quality_flagged
),
days_per_customer as (
    select gasstation_id, customer_id, count(*) as distinct_purchase_days
    from customer_station_day
    group by 1, 2
)
select
    c.vehicle_category,
    d.gasstation_id,
    count(*)                                             as total_customers,
    count(*) filter (where d.distinct_purchase_days >= 2) as repeat_customers,
    count(*) filter (where d.distinct_purchase_days >= 2)::decimal
        / nullif(count(*), 0)                             as repeat_rate,
    avg(d.distinct_purchase_days)                         as avg_purchase_days
from days_per_customer d
join {{ ref('dim_customer') }} c on d.customer_id = c.customer_id
group by 1, 2
