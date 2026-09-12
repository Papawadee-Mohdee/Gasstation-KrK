{{ config(materialized='table') }}
 
with invoice_products as (
    select distinct s.invoice_id, s.gasstation_id, c.vehicle_category, s.product_id
    from {{ ref('fact_sales') }} s
    join {{ ref('dim_customer') }} c on s.customer_id = c.customer_id
    where not s.is_data_quality_flagged
),
invoice_amount as (
    select invoice_id, total_amount from {{ ref('fact_invoice') }}
),
pairs as (
    select a.gasstation_id, a.vehicle_category, a.invoice_id,
           a.product_id as product_a, b.product_id as product_b
    from invoice_products a
    join invoice_products b
        on a.invoice_id = b.invoice_id and a.product_id < b.product_id
       and a.gasstation_id = b.gasstation_id
),
group_totals as (
    select gasstation_id, vehicle_category, count(distinct invoice_id) as group_invoice_count
    from invoice_products group by 1, 2
)
select
    p.gasstation_id, p.vehicle_category, p.product_a, p.product_b,
    count(distinct p.invoice_id) as pair_invoice_count,
    count(distinct p.invoice_id)::decimal / nullif(g.group_invoice_count, 0)
        as share_of_group_invoices,
    avg(ia.total_amount) as avg_invoice_amount
from pairs p
join group_totals g
    on p.gasstation_id = g.gasstation_id and p.vehicle_category = g.vehicle_category
join invoice_amount ia on p.invoice_id = ia.invoice_id
group by 1, 2, 3, 4, g.group_invoice_count
