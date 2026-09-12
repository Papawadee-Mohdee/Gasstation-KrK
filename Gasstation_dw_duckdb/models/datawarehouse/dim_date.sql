{{ config(materialized='table') }}
 
with bounds as (
    select
        least(min(issue_day), min(transaction_day))    as min_date,
        greatest(max(issue_day), max(transaction_day)) as max_date
    from (
        select issue_day, cast(null as date) as transaction_day
        from {{ ref('stg_Invoice') }}
        where not has_required_value_error
        union all
        select cast(null as date) as issue_day, transaction_day
        from {{ ref('stg_InventoryTransaction') }}
        where not has_required_value_error
    )
),
spine as (
    select unnest(generate_series(
        (select min_date from bounds),
        (select max_date from bounds),
        interval 1 day
    )) as date_day
)
select
    cast(strftime(date_day, '%Y%m%d') as integer) as date_key,
    date_day,
    extract(year  from date_day)::integer as year,
    extract(month from date_day)::integer as month,
    extract(day   from date_day)::integer as day_of_month,
    extract(isodow from date_day)::integer as iso_weekday,       -- 1 = จันทร์ ... 7 = อาทิตย์
    strftime(date_day, '%A') as weekday_name,
    (extract(isodow from date_day) in (6, 7)) as is_weekend,
    extract(week from date_day)::integer as iso_week,
    date_trunc('month', date_day) as month_start_date,
    (date_day = last_day(date_day)) as is_month_end,
    coalesce(c.is_complete_day, false) as is_complete_day        -- false = ยังไม่ยืนยัน ไม่ใช่ "ไม่ครบ" เสมอไป
from spine
left join {{ ref('ref_data_coverage') }} c
    on spine.date_day = c.coverage_date
