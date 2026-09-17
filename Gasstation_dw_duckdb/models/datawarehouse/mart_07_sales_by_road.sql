{{ config(materialized='table') }}

-- Q7: สถานีบริการที่ตั้งอยู่บนถนนสายใดสร้างยอดขายรวมได้สูงที่สุดและต่ำที่สุด

with station_sales as (
    select gasstation_id, sum(total_amount) as total_sales
    from {{ ref('fact_invoice') }}
    group by 1
)

select
    g.gasstation_id,
    g.gasstation_name,
    trim(split_part(g.address, ',', 1)) as road_name,
    s.total_sales,
    row_number() over (order by s.total_sales desc) as rank_highest,
    row_number() over (order by s.total_sales asc)  as rank_lowest
from station_sales s
join {{ ref('dim_gasstation') }} g on s.gasstation_id = g.gasstation_id
