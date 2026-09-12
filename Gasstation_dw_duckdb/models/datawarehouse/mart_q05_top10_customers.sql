{{ config(materialized='table') }}
 
with customer_station as (
    select s.gasstation_id, s.customer_id, c.vehicle_category,
           sum(s.total_price) as customer_sales_amount
    from {{ ref('fact_sales') }} s
    join {{ ref('dim_customer') }} c on s.customer_id = c.customer_id
    join {{ ref('dim_product') }} p  on s.product_id  = p.product_id
    where p.is_fuel and not s.is_data_quality_flagged
    group by 1, 2, 3
),
station_totals as (
    select gasstation_id, sum(customer_sales_amount) as station_sales_amount
    from customer_station group by 1
),
ranked as (
    select *, row_number() over (
        partition by gasstation_id
        order by customer_sales_amount desc, customer_id
    ) as customer_rank
    from customer_station
),
top_product as (
    -- สินค้าหลักของแต่ละลูกค้าต่อสถานี ตามยอดขายสูงสุด
    select gasstation_id, customer_id, product_id,
           row_number() over (
               partition by gasstation_id, customer_id
               order by sum(total_price) desc, product_id
           ) as product_rank
    from {{ ref('fact_sales') }}
    where not is_data_quality_flagged
    group by 1, 2, 3
)
select
    r.gasstation_id, r.customer_id, r.vehicle_category, r.customer_rank,
    r.customer_sales_amount,
    r.customer_sales_amount / nullif(t.station_sales_amount, 0) as share_of_station_sales,
    tp.product_id as top_product_id
from ranked r
join station_totals t on r.gasstation_id = t.gasstation_id
left join top_product tp
    on r.gasstation_id = tp.gasstation_id and r.customer_id = tp.customer_id
   and tp.product_rank = 1
where r.customer_rank <= 10
