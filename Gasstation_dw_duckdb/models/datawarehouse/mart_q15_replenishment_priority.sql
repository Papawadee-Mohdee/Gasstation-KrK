{{ config(materialized='table') }}
 
with cutoff as (
    -- as_of_date = วันสุดท้ายที่พบข้อมูลจริง กำหนดผ่าน var เพื่อทดสอบ cutoff อื่นได้
    select {{ var('as_of_date', "(select max(date_day) from " ~ ref('dim_date') ~ ")") }} as as_of_date
),
latest_per_tank as (
    select f.tank_id, f.gasstation_id, f.product_id, f.remaining_quantity,
           row_number() over (
               partition by f.tank_id
               order by f.date_key desc, f.hour_of_day desc, f.transaction_id desc
           ) as rn
    from {{ ref('fact_inventory_transaction') }} f, cutoff c
    where f.date_key <= cast(strftime(c.as_of_date, '%Y%m%d') as integer)
      and f.mapping_status = 'approved'
),
latest_stock as (
    select gasstation_id, product_id, sum(remaining_quantity) as latest_remaining
    from latest_per_tank where rn = 1 group by 1, 2
),
sales_7d as (
    select s.gasstation_id, s.product_id,
           sum(s.quantity_sold) / 7.0 as avg_daily_sales
    from {{ ref('int_sales_daily') }} s, cutoff c
    where s.date_key between cast(strftime(c.as_of_date - interval 6 day, '%Y%m%d') as integer)
                          and cast(strftime(c.as_of_date, '%Y%m%d') as integer)
    group by 1, 2
)
select
    l.gasstation_id, l.product_id, l.latest_remaining, s.avg_daily_sales,
    case when s.avg_daily_sales is null or s.avg_daily_sales = 0 then null
         else l.latest_remaining / s.avg_daily_sales
    end as days_of_cover,
    rank() over (
        order by (case when s.avg_daily_sales > 0
                       then l.latest_remaining / s.avg_daily_sales end) asc
        nulls last
    ) as replenishment_priority_rank
from latest_stock l
left join sales_7d s on l.gasstation_id = s.gasstation_id and l.product_id = s.product_id
