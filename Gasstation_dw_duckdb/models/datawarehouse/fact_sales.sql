{{ config(materialized='table') }}

-- Grain: 1 แถวต่อรายการสินค้าในบิล (InvoiceDetailID)
-- ไม่ทิ้งแถวที่ไม่ผ่าน has_required_value_error แต่ติดธง is_data_quality_flagged ไว้แทน
-- เพื่อให้ mart เลือกกรองเองว่าจะรวมหรือไม่รวม (สอดคล้องกติกาเดิม: ห้ามตัดแถวแบบเงียบ ๆ)

with detail as (
    select
        d.invoice_detail_id,
        d.invoice_id,
        d.product_id,
        d.quantity_sold as quantity_sold,
        d.selling_price as unit_price,
        d.total_price,
        d.has_required_value_error as detail_error
    from {{ ref('stg_InvoiceDetail') }} d
),

header as (
    select
        i.invoice_id,
        i.issue_day,
        i.issue_hour,
        i.gasstation_id,
        i.customer_id,
        i.employee_id,
        i.payment_method_key,
        i.has_required_value_error as header_error
    from {{ ref('stg_Invoice') }} i
)

select
    de.invoice_detail_id,
    de.invoice_id,
    dt.date_key,
    h.issue_hour                          as hour_of_day,
    h.gasstation_id,
    h.customer_id,
    h.employee_id,
    de.product_id,
    h.payment_method_key,
    de.quantity_sold,
    de.unit_price,
    de.total_price,
    (de.detail_error or h.header_error)   as is_data_quality_flagged
from detail de
join header h
    on de.invoice_id = h.invoice_id
join {{ ref('dim_date') }} dt
    on h.issue_day = dt.date_day