{{ config(materialized='table') }}

-- Q10: ลูกค้ารถประเภทใดมักซื้อน้ำมันหลายชนิดในบิลเดียว และคู่สินค้าใดพบร่วมกันบ่อยที่สุด?
-- นับคู่สินค้าแบบไม่เรียงลำดับเพียงครั้งเดียวต่อบิล (product_id_a < product_id_b กันนับซ้ำ)
-- หมายเหตุ: self-join นี้เหมาะกับข้อมูลขนาดเล็ก/กลาง ถ้าข้อมูลใหญ่มากควรทำ incremental

with detail as (
    select
        f.invoice_id,
        f.gasstation_id,
        f.customer_id,
        f.product_id
    from {{ ref('fact_sales') }} f
    where not f.is_data_quality_flagged
),

pairs as (
    select distinct
        d1.invoice_id,
        d1.gasstation_id,
        d1.customer_id,
        d1.product_id as product_id_a,
        d2.product_id as product_id_b
    from detail d1
    join detail d2
        on d1.invoice_id = d2.invoice_id
       and d1.product_id < d2.product_id
),

enriched as (
    select
        p.gasstation_id,
        c.vehicle_category,
        p.product_id_a,
        p.product_id_b,
        p.invoice_id
    from pairs p
    join {{ ref('dim_customer') }} c on p.customer_id = c.customer_id
),

pair_counts as (
    select
        gasstation_id, vehicle_category, product_id_a, product_id_b,
        count(distinct invoice_id) as bill_count_with_pair
    from enriched
    group by 1, 2, 3, 4
),

group_totals as (
    select
        gasstation_id, vehicle_category,
        count(distinct invoice_id) as group_bill_count
    from enriched
    group by 1, 2
),

bill_values as (
    select invoice_id, sum(total_price) as invoice_amount
    from {{ ref('fact_sales') }}
    where not is_data_quality_flagged
    group by 1
),

pair_bill_value as (
    select
        e.gasstation_id, e.vehicle_category, e.product_id_a, e.product_id_b,
        avg(bv.invoice_amount) as avg_bill_value
    from enriched e
    join bill_values bv on e.invoice_id = bv.invoice_id
    group by 1, 2, 3, 4
)

select
    pc.gasstation_id,
    g.gasstation_name,
    pc.vehicle_category,
    pc.product_id_a,
    pa.product_name as product_name_a,
    pc.product_id_b,
    pb.product_name as product_name_b,
    pc.bill_count_with_pair,
    pc.bill_count_with_pair / nullif(gt.group_bill_count, 0) as pct_of_group_bills,
    pv.avg_bill_value
from pair_counts pc
join group_totals gt
    on pc.gasstation_id = gt.gasstation_id
   and pc.vehicle_category = gt.vehicle_category
join pair_bill_value pv
    on pc.gasstation_id = pv.gasstation_id
   and pc.vehicle_category = pv.vehicle_category
   and pc.product_id_a = pv.product_id_a
   and pc.product_id_b = pv.product_id_b
join {{ ref('dim_gasstation') }} g on pc.gasstation_id = g.gasstation_id
join {{ ref('dim_product') }} pa on pc.product_id_a = pa.product_id
join {{ ref('dim_product') }} pb on pc.product_id_b = pb.product_id