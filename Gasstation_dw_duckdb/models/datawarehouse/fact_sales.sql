{{ config(materialized='table') }}

select
    d.InvoiceDetailID as invoice_detail_id,
    cast(strftime(cast(i.IssueDate as date), '%Y%m%d') as integer) as date_key,
    extract(hour from cast(i.IssueDate as timestamp))::integer as hour_of_day,
    i.GasStationID as gasstation_id,
    i.CustomerID as customer_id,
    i.EmployeeID as employee_id,
    d.ProductID as product_id,
    lower(i.PaymentMethod) as payment_method_key,
    d.QuantitySold as quantity_sold,
    d.SellingPrice as unit_price,
    d.TotalPrice as total_price
from {{ ref('stg_InvoiceDetail') }} d
join {{ ref('stg_Invoice') }} i
    on d.InvoiceID = i.InvoiceID
where d.InvoiceDetailID is not null
