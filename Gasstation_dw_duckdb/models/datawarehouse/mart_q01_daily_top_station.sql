{{ config(materialized='table') }}
 
with sales as (
    select s.gasstation_id, s.date_key, s.product_id,
           sum(s.quantity_sold) as quantity_sold,
           sum(s.total_price)   as sales_amount
    from {{ ref('fact_sales') }} s
    join {{ ref('dim_product') }} p on s.product_id = p.product_id
    where p.is_fuel and not s.is_data_quality_flagged
    group by 1, 2, 3
),
station_daily as (
    select gasstation_id, date_key, sum(sales_amount) as station_sales_amount
    from sales group by 1, 2
),
ranked_station as (
    select *, dense_rank() over (
        partition by date_key order by station_sales_amount desc
    ) as station_rank
    from station_daily
)
select
    r.date_key, r.gasstation_id, r.station_rank, r.station_sales_amount,
    s.product_id, s.sales_amount, s.quantity_sold,
    s.sales_amount / nullif(r.station_sales_amount, 0) as product_share_within_station
from ranked_station r
join sales s on r.gasstation_id = s.gasstation_id and r.date_key = s.date_key
