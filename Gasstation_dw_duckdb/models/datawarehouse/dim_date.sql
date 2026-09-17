{{ config(materialized='table') }}

with bounds as (
    select
        least(
            (select min(cast(IssueDate as date)) from {{ ref('stg_Invoice') }}),
            (select min(cast(TransactionDate as date)) from {{ ref('stg_InventoryTransaction') }})
        ) as min_date,
        greatest(
            (select max(cast(IssueDate as date)) from {{ ref('stg_Invoice') }}),
            (select max(cast(TransactionDate as date)) from {{ ref('stg_InventoryTransaction') }})
        ) as max_date
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
    extract(isodow from date_day)::integer as iso_weekday,
    strftime(date_day, '%A') as weekday_name,
    (extract(isodow from date_day) in (6, 7)) as is_weekend,
    coalesce(cast(c.is_complete_day as boolean), false) as is_complete_day,
    current_localtimestamp() as insertion_timestamp
from spine
left join {{ ref('ref_data_coverage') }} c
    on spine.date_day = c.coverage_date
