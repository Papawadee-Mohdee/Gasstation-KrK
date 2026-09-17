{{ config(materialized='table') }}

select
    InvoiceID as invoice_id,
    cast(strftime(cast(IssueDate as date), '%Y%m%d') as integer) as date_key,
    extract(hour from cast(IssueDate as timestamp))::integer as hour_of_day,
    GasStationID as gasstation_id,
    CustomerID as customer_id,
    EmployeeID as employee_id,
    lower(PaymentMethod) as payment_method_key,
    TotalAmount as total_amount
from {{ ref('stg_Invoice') }}
where InvoiceID is not null
