{{ config(materialized='table') }}
 
select
    i.invoice_id,
    coalesce(c.customer_id, -1)               as customer_id,
    coalesce(e.employee_id, -1)                as employee_id,
    coalesce(g.gasstation_id, -1)               as gasstation_id,
    coalesce(pm.payment_method_key, 'unknown')  as payment_method_key,
    cast(strftime(i.issue_day, '%Y%m%d') as integer) as date_key,
    extract(hour from i.issue_date)::integer    as hour_of_day,
    i.issue_weekday,
    i.total_amount,
    i.has_required_value_error                  as is_data_quality_flagged
from {{ ref('stg_Invoice') }} i
left join {{ ref('dim_customer') }} c        on i.customer_id = c.customer_id
left join {{ ref('dim_employee') }} e        on i.employee_id = e.employee_id
left join {{ ref('dim_gasstation') }} g      on i.gasstation_id = g.gasstation_id
left join {{ ref('dim_payment_method') }} pm on i.payment_method_key = pm.payment_method_key
