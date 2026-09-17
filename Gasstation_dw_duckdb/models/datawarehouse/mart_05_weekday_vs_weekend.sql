{{ config(materialized='table') }}

-- Q5: ยอดขายรวมและปริมาณการออกบิลระหว่างวันธรรมดากับวันหยุดสุดสัปดาห์

select
    f.gasstation_id,
    d.is_weekend,
    count(*)               as invoice_count,
    sum(f.total_amount)    as total_sales,
    avg(f.total_amount)    as avg_invoice_amount
from {{ ref('fact_invoice') }} f
join {{ ref('dim_date') }} d on f.date_key = d.date_key
group by 1, 2
