{{ config(materialized='table') }}

-- Q4: วิธีชำระเงินสัมพันธ์กับมูลค่าการซื้ออย่างไร เมื่อจำแนกตามประเภทรถ สถานี และช่วงเวลา?
-- รวมยอดที่ระดับ invoice ก่อน (invoice_totals) เพื่อไม่ให้ยอดขายเฉลี่ยต่อบิลถูกคูณซ้ำ
-- ตามจำนวนรายการสินค้าในบิล

with invoice_totals as (
    select
        f.invoice_id,
        f.gasstation_id,
        f.customer_id,
        f.payment_method_key,
        f.hour_of_day,
        sum(f.total_price) as invoice_amount
    from {{ ref('fact_sales') }} f
    where not f.is_data_quality_flagged
    group by 1, 2, 3, 4, 5
),

enriched as (
    select
        it.gasstation_id,
        pm.payment_method_label,
        c.vehicle_category,
        h.day_part,
        it.invoice_id,
        it.invoice_amount
    from invoice_totals it
    join {{ ref('dim_customer') }} c on it.customer_id = c.customer_id
    join {{ ref('dim_payment_method') }} pm on it.payment_method_key = pm.payment_method_key
    join {{ ref('dim_hour') }} h
        on extract(hour from cast(it.hour_of_day as timestamp))
        = cast(h.hour_of_day as bigint)),

grouped as (
    select
        gasstation_id,
        payment_method_label,
        vehicle_category,
        day_part,
        count(distinct invoice_id) as bill_count,
        sum(invoice_amount)        as total_amount
    from enriched
    group by 1, 2, 3, 4
),

station_totals as (
    select gasstation_id, sum(bill_count) as station_bill_count
    from grouped
    group by 1
)

select
    g.gasstation_id,
    g.payment_method_label,
    g.vehicle_category,
    g.day_part,
    g.bill_count,
    g.total_amount / nullif(g.bill_count, 0)        as avg_sales_per_bill,
    g.bill_count / nullif(s.station_bill_count, 0)  as pct_bills_by_method
from grouped g
join station_totals s on g.gasstation_id = s.gasstation_id