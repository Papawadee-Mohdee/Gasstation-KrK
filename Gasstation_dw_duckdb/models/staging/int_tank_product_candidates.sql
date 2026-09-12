{{ config(materialized='view') }}
select t.tank_id, t.gasstation_id, t.tank_name,
       p.product_id, p.product_name,
       count(p.product_id) over (partition by t.tank_id)
         as candidate_count,
       'pending_review' as review_status
from {{ ref('stg_StorageTank') }} t
left join {{ ref('stg_Product') }} p
  on lower(trim(regexp_replace(t.tank_name, ' Tank$', '')))
   = lower(trim(p.product_name))

