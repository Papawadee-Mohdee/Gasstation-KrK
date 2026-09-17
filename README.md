# Gasstation_KRK
Project Group1

## Data Warehouse Architecture & Dimensional Modeling

---

##  Members

| รหัสนักศึกษา | ชื่อ-นามสกุล |
| :---: | :--- |
| **673020045-9** | นายประภากร มีใส |
| **673020244-3** | นายกิตติพัศ ลาล้ำ |
| **673020256-6** | นางสาวปภาวดี เหมาะดี |
| **673020264-7** | นางสาวสุกัญญา อุดมกัน |
| **673020266-3** | นางสาวสุพิชญา ผ่องสนาม |
| **673020270-2** | นางสาวอาทิติญา ชาชัย |

---

##  Data Warehouse Architecture & Dimensional Modeling

คลังข้อมูล **GasStation Data Warehouse** ออกแบบตามสถาปัตยกรรม **Galaxy Schema (Fact Constellation Schema)** ประกอบด้วย **9 Dimension Tables**, **1 Bridge Table** และ **3 Fact Tables** เพื่อรองรับระดับความละเอียดข้อมูล (Grain) ที่แตกต่างกัน ป้องกันปัญหายอดเงินรวมคูณซ้ำ (Double Counting) และรองรับการทำ OLAP Analytics ครอบคลุมทั้งงานขาย พฤติกรรมลูกค้า และการบริหารสต็อกน้ำมันคงคลัง

---

### 1. Data Model Summary (ภาพรวมตารางทั้งหมด)

| Table Name | Model Type | Primary / Foreign Key | Primary Source / Logic | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`dim_customer`** | Dimension | customer_key (PK) | stg_Customer | ประวัติลูกค้า ข้อมูลติดต่อ และทะเบียนรถ |
| **`dim_vehicle_category`** | Dimension | vehicle_category_key (PK) | stg_Customer (Distinct) | กลุ่มประเภทยานพาหนะ (Car, Truck, Motorcycle) |
| **`dim_employee`** | Dimension | employee_key (PK) | stg_Employee | ข้อมูลพนักงาน ตำแหน่ง และสาขาต้นสังกัด |
| **`dim_gasstation`** | Dimension | gasstation_key (PK) | stg_GasStation | ข้อมูลสาขาสถานีบริการน้ำมันและสถานที่ตั้ง |
| **`dim_product`** | Dimension | product_key (PK) | stg_Product | รายการชนิดน้ำมัน/สินค้า ซัพพลายเออร์ และราคาตั้งขาย |
| **`dim_tank`** | Dimension | tank_key (PK) | snap_storage_tank | ข้อมูลถังน้ำมัน (รองรับ SCD Type 2 บันทึกประวัติ) |
| **`bridge_tank_product`** | Bridge | `tank_key`, product_key (FK) | Junction Mapping | สะพานเชื่อมความสัมพันธ์ N:M ระหว่างถังและชนิดน้ำมัน |
| **`dim_payment_method`** | Dimension | payment_method_key (PK) | stg_Invoice (Distinct) | ช่องทางการชำระเงิน (Cash, Credit Card) |
| **`dim_date`** | Dimension | date_key (PK) | Dynamic Date Series | มิติวัน (คำนวณช่วงวันออโต้ตามปฏิทินธุรกรรม) |
| **`dim_hour`** | Dimension | hour_key (PK) | range(0, 24) | มิติชั่วโมงในรอบวัน (0-23) และช่วงเวลา (Day Part) |
| **`fact_sales`** | Fact | sales_key (PK) | stg_InvoiceDetail + stg_Invoice | แฟกต์รายการขายน้ำมันระดับบรรทัดสินค้า (Sales Line Item) |
| **`fact_invoice`** | Fact | invoice_key (PK) | stg_Invoice | แฟกต์ยอดขายระดับหัวใบเสร็จ (ป้องกัน Double Counting) |
| **`fact_inventory_transaction`** | Fact | transaction_key (PK) | stg_InventoryTransaction | แฟกต์การรับ/จ่าย และยอดคงเหลือสต็อกน้ำมันในถัง |

---

### 2. Dimension Tables & Governance Detail

ทุกตาราง Dimension รองรับเทคนิค **Unknown Member Fallback (`key = -1`)** เพื่อรักษาความสมบูรณ์ของข้อมูลอ้างอิง (Referential Integrity) ไม่ให้ตัวเลขการเงินสูญหาย

* **`dim_customer`**: customer_key (PK), `customer_id`, `customer_name`, `address`, `phone_number`, `email`, `vehicle_type`, `license_plate`, is_unknown_member
* **`dim_vehicle_category`**: vehicle_category_key (PK), `vehicle_category_name`, `vehicle_type`, is_unknown_member
* **`dim_employee`**: employee_key (PK), `employee_id`, `employee_name`, `position`, `home_gasstation_id`, `phone_number`, `email`, `start_date`, is_unknown_member
* **`dim_gasstation`**: gasstation_key (PK), `gasstation_id`, `gasstation_name`, `address`, `phone_number`, `email`, is_unknown_member
* **`dim_product`**: product_key (PK), `product_id`, `product_name`, `product_type`, `supplier`, `list_unit_price`, is_unknown_member
* **`dim_tank` (SCD Type 2 Enabled)**: tank_key (PK), `tank_id`, `gasstation_id`, `tank_name`, `material_type`, `capacity_liters`, `valid_from`, `valid_to`, `is_current`, is_unknown_member
* **`bridge_tank_product`**: tank_key (FK), product_key (FK)
* **`dim_payment_method`**: payment_method_key (PK), `payment_method_name`, is_unknown_member
* **`dim_date`**: date_key (PK: YYYYMMDD), `full_date`, `year`, `quarter`, `month`, `month_name`, `day_of_month`, `day_name`, is_weekend
* **`dim_hour`**: hour_key (PK: 0-23), `hour_24`, day_part (Morning, Midday, Afternoon, Evening, Night)

---

### 3. Fact Tables Detail & Measures Classification

####  1. fact_sales (Sales Item Fact Table)
* **Grain:** 1 แถว ต่อ 1 บรรทัดรายการสินค้าในใบเสร็จ (`invoicedetail_id`)
* **Source Tables:** stg_InvoiceDetail (Main) JOIN `stg_Invoice`, `dim_date`, `dim_hour`, `dim_customer`, `dim_employee`, `dim_gasstation`, `dim_product`, dim_payment_method
* **Measures:**
  * quantity_sold (Additive): ปริมาณน้ำมันที่ขาย (ลิตร)
  * total_price (Additive): มูลค่ายอดขายรวมสุทธิ (`quantity_sold * selling_price`)
  * selling_price (Non-Additive): ราคาขายต่อหน่วย ณ ช่วงเวลานั้น
  * line_count (Additive): จำนวนบรรทัดรายการสินค้า

####  2. fact_invoice (Invoice Header Fact Table)
* **Grain:** 1 แถว ต่อ 1 ใบเสร็จรับเงิน (`invoice_id`)
* **Source Tables:** stg_Invoice (Main) JOIN `dim_date`, `dim_hour`, `dim_customer`, `dim_employee`, `dim_gasstation`, dim_payment_method
* **Objective:** แก้ปัญหายอดเงินรวมคูณซ้ำ (Double Counting) เมื่อวิเคราะห์มูลค่าบิลเฉลี่ย
* **Measures:**
  * total_amount (Additive): ยอดขายรวมสุทธิระดับหัวใบเสร็จ
  * line_count (Additive): จำนวนรายการสินค้าทั้งหมดในใบเสร็จ

####  3. fact_inventory_transaction (Inventory Transaction Fact Table)
* **Grain:** 1 แถว ต่อ 1 ธุรกรรมการรับ/จ่ายน้ำมันในถังเก็บ (`transaction_id`)
* **Source Tables:** stg_InventoryTransaction (Main) JOIN `dim_tank`, `dim_gasstation`, `dim_date`, dim_hour
* **Measures:**
  * quantity_in (Additive): ปริมาณน้ำมันที่รับเข้าถัง (ลิตร)
  * quantity_out (Additive): ปริมาณน้ำมันที่จ่ายออกจากถัง (ลิตร)
  * remaining_quantity (Semi-Additive): ปริมาณน้ำมันคงเหลือในถังหลังทำรายการ (ห้าม SUM บวกสะสมข้ามมิติเวลา)

---

### 4. Data Lineage Flow (การเชื่อมโยงข้อมูล dbt Transformation)

```text
[ STAGING LAYER (OLTP) ]                      [ DATA WAREHOUSE LAYER (OLAP) ]

stg_Customer ───────────────────────────────► dim_customer
stg_Customer (Distinct) ────────────────────► dim_vehicle_category
stg_Employee ───────────────────────────────► dim_employee
stg_GasStation ─────────────────────────────► dim_gasstation
stg_Product ────────────────────────────────► dim_product
snap_storage_tank (SCD Type 2) ─────────────► dim_tank
stg_StorageTank + stg_Product ──────────────► bridge_tank_product

stg_Invoice (payment_method) ───────────────► dim_payment_method
stg_Invoice + stg_InventoryTxn ─────────────► dim_date (Dynamic bounds)
range(0, 24) ───────────────────────────────► dim_hour

stg_InvoiceDetail ──┐
stg_Invoice ────────┼───────────────────────► fact_sales (Grain: Item Line)
Dimensions Keys ────┘

stg_Invoice ────────┐
Dimensions Keys ────┴───────────────────────► fact_invoice (Grain: Invoice Header)

stg_InventoryTransaction ──┐
snap_storage_tank ─────────┼────────────────► fact_inventory_transaction
Dimensions Keys ───────────┘
