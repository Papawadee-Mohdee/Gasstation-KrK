{{ config(materialized='table') }}

-- Q4: สัดส่วนพฤติกรรมการชำระเงินระหว่าง Cash กับ Credit Card ในแต่ละสถานี

with agg as (
    select gasstation_id, payment_method_key,
        count(*) as invoice_count,
        sum(total_amount) as total_amount
    from {{ ref('fact_invoice') }}
    group by 1, 2
)

select
    gasstation_id,
    payment_method_key,
    invoice_count,
    total_amount,
    round(total_amount / sum(total_amount) over (partition by gasstation_id) * 100, 2) as pct_of_station_sales
from agg
