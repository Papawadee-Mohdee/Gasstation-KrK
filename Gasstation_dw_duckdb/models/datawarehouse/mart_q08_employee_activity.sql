{{ config(materialized='table') }}
 
with daily as (
    select fi.employee_id, e.position, fi.gasstation_id, fi.date_key,
           fi.hour_of_day,
           count(fi.invoice_id) as invoice_count,
           sum(fi.total_amount) as sales_amount
    from {{ ref('fact_invoice') }} fi
    join {{ ref('dim_employee') }} e on fi.employee_id = e.employee_id
    where not fi.is_data_quality_flagged
    group by 1, 2, 3, 4, 5
),
active_days as (
    select employee_id, gasstation_id, count(distinct date_key) as active_day_count
    from daily group by 1, 2
)
select
    d.employee_id, d.position, d.gasstation_id, d.date_key, d.hour_of_day,
    d.invoice_count, d.sales_amount,
    sum(d.invoice_count) over (partition by d.employee_id, d.gasstation_id)
        / nullif(a.active_day_count, 0) as avg_invoices_per_active_day
from daily d
join active_days a on d.employee_id = a.employee_id and d.gasstation_id = a.gasstation_id
