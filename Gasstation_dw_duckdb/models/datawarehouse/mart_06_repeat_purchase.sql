{{ config(materialized='table') }}

-- Q6: ลูกค้ารถแต่ละประเภทกลับมาซื้อซ้ำที่สถานีเดิมมากน้อยเพียงใด?
-- ลูกค้าซื้อซ้ำ = ผู้ซื้อที่สถานีเดิมอย่างน้อย 2 วัน (นับวันที่ไม่ซ้ำ ไม่ใช่จำนวนบิล)
-- อัตราซื้อซ้ำ = ลูกค้าซื้อซ้ำ ÷ ลูกค้าทั้งหมดในกลุ่ม (ประเภทรถ × สถานี)

with visits as (
    select distinct
        c.vehicle_category,
        f.gasstation_id,
        f.customer_id,
        d.date_day
    from {{ ref('fact_sales') }} f
    join {{ ref('dim_customer') }} c on f.customer_id = c.customer_id
    join {{ ref('dim_date') }} d on f.date_key = d.date_key
    where not f.is_data_quality_flagged
),

customer_days as (
    select
        vehicle_category,
        gasstation_id,
        customer_id,
        count(distinct date_day) as purchase_days
    from visits
    group by 1, 2, 3
),

grouped as (
    select
        gasstation_id,
        vehicle_category,
        count(distinct customer_id) as total_customers,
        count(distinct case when purchase_days >= 2 then customer_id end) as repeat_customers,
        avg(purchase_days) as avg_purchase_days_per_customer
    from customer_days
    group by 1, 2
)

select
    grp.gasstation_id,
    g.gasstation_name,
    grp.vehicle_category,
    grp.total_customers,
    grp.repeat_customers,
    grp.repeat_customers / nullif(grp.total_customers, 0) as repeat_rate,
    grp.avg_purchase_days_per_customer
from grouped grp
join {{ ref('dim_gasstation') }} g on grp.gasstation_id = g.gasstation_id