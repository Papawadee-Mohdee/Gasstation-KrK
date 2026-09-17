{{ config(materialized='table') }}

-- Q15: สถานีใดมีประสิทธิภาพยอดขายต่อพนักงาน (Revenue per Employee) สูงสุด
-- และสาขาที่ยอดขายสูงมีพนักงานเติมน้ำมัน (Pump Attendant) เพียงพอต่อปริมาณงานหรือไม่

with revenue as (
    select gasstation_id, sum(total_amount) as total_sales
    from {{ ref('fact_invoice') }}
    group by 1
),

headcount as (
    select
        home_gasstation_id as gasstation_id,
        count(*) as total_employees,
        sum(case when position = 'Pump Attendant' then 1 else 0 end) as pump_attendant_count
    from {{ ref('dim_employee') }}
    where home_gasstation_id is not null
    group by 1
),

workload as (
    select gasstation_id, count(*) as invoice_count
    from {{ ref('fact_invoice') }}
    group by 1
)

select
    r.gasstation_id,
    r.total_sales,
    h.total_employees,
    round(r.total_sales / nullif(h.total_employees, 0), 2) as revenue_per_employee,
    h.pump_attendant_count,
    w.invoice_count,
    round(w.invoice_count / nullif(h.pump_attendant_count, 0), 2) as invoices_per_pump_attendant
from revenue r
join headcount h on r.gasstation_id = h.gasstation_id
join workload w on r.gasstation_id = w.gasstation_id
