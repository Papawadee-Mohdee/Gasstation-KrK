{{ config(materialized='table') }}

-- Q9: ยอดขายของแต่ละสถานีเพิ่ม/ลดจากวันเดียวกันในสัปดาห์ก่อนเท่าใด และน้ำมันชนิดใดมีส่วนมากสุด?
-- ใช้ inner join กับ 7 วันก่อน: เปรียบเทียบเฉพาะวันที่มีข้อมูลครบทั้งสองฝั่งตามกติกาเดิม
-- (ไม่ใช่ left join ที่จะโชว์ pct_change เป็น null ปนกับ "ไม่มีข้อมูลเปรียบเทียบ")

with daily as (
    select
        f.gasstation_id,
        f.product_id,
        d.date_day,
        sum(f.total_price)   as sales_amount,
        sum(f.quantity_sold) as quantity_sold
    from {{ ref('fact_sales') }} f
    join {{ ref('dim_product') }} p on f.product_id = p.product_id
    join {{ ref('dim_date') }} d on f.date_key = d.date_key
    where p.is_fuel
      and not f.is_data_quality_flagged
    group by 1, 2, 3
)

select
    cur.gasstation_id,
    g.gasstation_name,
    cur.product_id,
    p.product_name,
    cur.date_day,
    dd.weekday_name,
    cur.sales_amount,
    prior.sales_amount                                         as sales_amount_prior_week,
    cur.sales_amount - prior.sales_amount                      as sales_diff,
    case when prior.sales_amount = 0 then null
         else (cur.sales_amount - prior.sales_amount) / prior.sales_amount
    end                                                         as pct_change,
    cur.quantity_sold - prior.quantity_sold                    as quantity_diff
from daily cur
join daily prior
    on cur.gasstation_id = prior.gasstation_id
   and cur.product_id = prior.product_id
   and prior.date_day = cur.date_day - interval 7 day
join {{ ref('dim_date') }} dd on cur.date_day = dd.date_day
join {{ ref('dim_gasstation') }} g on cur.gasstation_id = g.gasstation_id
join {{ ref('dim_product') }} p on cur.product_id = p.product_id