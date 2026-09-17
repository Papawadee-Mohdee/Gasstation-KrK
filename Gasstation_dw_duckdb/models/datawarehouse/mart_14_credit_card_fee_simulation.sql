{{ config(materialized='table') }}

-- Q14: หากอัตราค่าธรรมเนียมบัตรเครดิตอยู่ที่ 2% ต้นทุนค่าธรรมเนียมคิดเป็นสัดส่วนเท่าใดของยอดขายรวมแต่ละสถานี

with agg as (
    select
        gasstation_id,
        sum(total_amount) as total_sales,
        sum(case when payment_method_key = 'credit card' then total_amount else 0 end) as credit_card_sales
    from {{ ref('fact_invoice') }}
    group by 1
)

select
    gasstation_id,
    total_sales,
    credit_card_sales,
    round(credit_card_sales * 0.02, 2) as simulated_cc_fee,
    round(credit_card_sales * 0.02 / nullif(total_sales, 0) * 100, 4) as fee_pct_of_total_sales
from agg
