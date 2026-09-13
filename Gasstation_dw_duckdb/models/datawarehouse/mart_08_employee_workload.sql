{{ config(materialized='table') }}

-- Q8: พนักงานและตำแหน่งมีปริมาณรายการขายต่างกันอย่างไร ตามสถานี วัน และช่วงเวลา?
-- นับจากรายการที่บันทึกภายใต้พนักงานนั้น (ไม่มีชั่วโมงทำงานจริง จึงยังสรุปประสิทธิภาพ
-- ต่อชั่วโมงทำงานไม่ได้ ตามที่ระบุไว้ในเอกสาร Staging)

select
    f.employee_id,
    e.employee_name,
    e.position,
    f.gasstation_id,
    g.gasstation_name,
    d.date_day,
    f.hour_of_day,
    count(distinct f.invoice_id) as bill_count,
    sum(f.total_price)           as sales_amount
from {{ ref('fact_sales') }} f
join {{ ref('dim_employee') }} e on f.employee_id = e.employee_id
join {{ ref('dim_gasstation') }} g on f.gasstation_id = g.gasstation_id
join {{ ref('dim_date') }} d on f.date_key = d.date_key
where not f.is_data_quality_flagged
group by 1, 2, 3, 4, 5, 6, 7