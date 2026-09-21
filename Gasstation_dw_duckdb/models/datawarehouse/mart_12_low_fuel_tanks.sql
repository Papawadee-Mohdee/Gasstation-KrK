{{ config(materialized='table') }}

-- Q12: ถังเก็บน้ำมันใบใดมีระดับน้ำมันคงเหลือล่าสุดต่ำกว่าเกณฑ์เตือนภัย (20% ของความจุถัง)

select
    tank_id,
    gasstation_id,
    tank_name,
    capacity_liters,
    current_quantity,
    round(current_quantity / nullif(capacity_liters, 0) * 100, 2) as fill_pct,
    (current_quantity / nullif(capacity_liters, 0)) < 0.2 as is_below_threshold
from {{ ref('dim_tank') }}
