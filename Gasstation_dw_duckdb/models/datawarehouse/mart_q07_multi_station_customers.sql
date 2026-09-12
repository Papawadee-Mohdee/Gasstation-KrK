{{ config(materialized='table') }}
 
with customer_station_sales as (
    select s.customer_id, c.vehicle_category, s.gasstation_id, s.product_id,
           sum(s.total_price) as sales_amount
    from {{ ref('fact_sales') }} s
    join {{ ref('dim_customer') }} c on s.customer_id = c.customer_id
    where not s.is_data_quality_flagged
    group by 1, 2, 3, 4
),
customer_totals as (
    select customer_id, sum(sales_amount) as customer_total_sales,
           count(distinct gasstation_id) as station_count
    from customer_station_sales group by 1
)
select
    css.customer_id, css.vehicle_category, css.gasstation_id, css.product_id,
    ct.station_count, css.sales_amount,
    css.sales_amount / nullif(ct.customer_total_sales, 0) as share_of_customer_sales
from customer_station_sales css
join customer_totals ct on css.customer_id = ct.customer_id
where ct.station_count > 1
