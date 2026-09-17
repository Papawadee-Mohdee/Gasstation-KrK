{{ config(materialized='table') }}

-- Q6: พนักงานคนใดในแต่ละสถานีมีจำนวนการออกบิลสะสมสูงที่สุดตลอดช่วงข้อมูล

with agg as (
    select gasstation_id, employee_id, count(*) as invoice_count
    from {{ ref('fact_invoice') }}
    group by 1, 2
)

select
    a.gasstation_id,
    a.employee_id,
    e.employee_name,
    a.invoice_count,
    row_number() over (partition by a.gasstation_id order by a.invoice_count desc) as rnk
from agg a
join {{ ref('dim_employee') }} e on a.employee_id = e.employee_id
