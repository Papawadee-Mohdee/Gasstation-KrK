{{ config(materialized='table') }}
 
select
    d.invoice_detail_id,
    d.invoice_id,
    coalesce(i.customer_id, -1)                as customer_id,
    coalesce(i.employee_id, -1)                as employee_id,
    coalesce(i.gasstation_id, -1)               as gasstation_id,
    coalesce(d.product_id, -1)                  as product_id,
    coalesce(i.payment_method_key, 'unknown')   as payment_method_key,
    cast(strftime(i.issue_day, '%Y%m%d') as integer) as date_key,
    extract(hour from i.issue_date)::integer     as hour_of_day,
    i.issue_weekday,
    d.quantity_sold,
    d.selling_price,
    d.total_price,
    (d.has_required_value_error or i.has_required_value_error)
        as is_data_quality_flagged
from {{ ref('stg_InvoiceDetail') }} d
left join {{ ref('stg_Invoice') }} i on d.invoice_id = i.invoice_id
