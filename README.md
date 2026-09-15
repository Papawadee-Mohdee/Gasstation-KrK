# GasStationDB - Data Warehouse & Business Intelligence Project

> **Repository:** Gasstation_KRK  
> **Group:** Project Group 1  
> **Course:** SC663402 Data Warehouse and Big Data Analytics  

โครงงานออกแบบและพัฒนาคลังข้อมูล (Data Warehouse) จากระบบ OLTP สู่ OLAP สำหรับธุรกิจสถานีบริการน้ำมัน (GasStationDB) เพื่อตอบคำถามทางธุรกิจและสร้าง Interactive Dashboard สื่อสารข้อมูลเพื่อการบริหารจัดการ

---

## Tech Stack Badges

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![DuckDB](https://img.shields.io/badge/DuckDB-0.9+-FFF000?style=for-the-badge&logo=duckdb&logoColor=black)
![dbt](https://img.shields.io/badge/dbt-Core-FF694B?style=for-the-badge&logo=dbt&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)

---

## สมาชิกในกลุ่ม

| รหัสนักศึกษา | ชื่อ-นามสกุล | 
| :---: | :--- | 
| **673020045-9** | นายประภากร มีใส | 
| **673020244-3** | นายกิตติพัศ ลาล้ำ |
| **673020256-6** | นางสาวปภาวดี เหมาะดี | 
| **673020264-7** | นางสาวสุกัญญา อุดมกัน | 
| **673020266-3** | นางสาวสุพิชญา ผ่องสนาม | 
| **673020270-2** | นางสาวอาทิติญา ชาชัย | 

---
## 1. Operational Database (OLTP)

* **ชุดข้อมูลต้นทาง:** GasStationDB (HCM City - PostgreSQL) จาก Kaggle
* **ขอบเขตระบบ:** บันทึกธุรกรรมการขายน้ำมันประจำวัน การจัดการคลังน้ำมัน หัวจ่าย พนักงาน และลูกค้า รวม 24 วัน (15 มีนาคม – 7 เมษายน 2024)
* **ER Diagram ต้นทาง:** [คลิกเปิดดู ER Diagram บน Google Drive](https://drive.google.com/file/d/1JGIX7BkISNF0DNA6mARoEywLSQCLhmJH/view)

![Operational ER Diagram](ER_gas.drawio.png)

แบบจำลองฐานข้อมูลเชิงสัมพันธ์นี้ ออกแบบเพื่อรองรับการดำเนินงานบริหารจัดการสถานีบริการน้ำมัน ครอบคลุมกระบวนการขาย บุคลากรประจำสาขา และปริมาณน้ำมันคงคลัง แบ่งเป็น 3 กลุ่มหลักดังนี้
1. กลุ่มข้อมูลหลักและโครงสร้างสาขา

ทำหน้าที่จัดเก็บข้อมูลพื้นฐานที่ใช้ในการอ้างอิงทั่วทั้งระบบ ได้แก่

   • gasstation(ข้อมูลสถานีบริการน้ำมัน) จัดเก็บข้อมูลสาขา ที่อยู่ ช่องทางการติดต่อ ทำหน้าที่เป็นศูนย์กลางความสัมพันธ์ของพนักงาน ถังน้ำมัน และยอดขายในแต่ละสาขา

   • employee(ข้อมูลพนักงาน) จัดเก็บข้อมูลบุคลากร ตำแหน่ง วันที่เริ่มงาน โดยเชื่อมโยงผ่าน gasstationid เพื่อระบุสาขาต้นสังกัดที่พนักงานปฏิบัติงาน

   • customer(ข้อมูลลูกค้า) จัดเก็บประวัติลูกค้า ช่องทางการติดต่อ พร้อมทั้งข้อมูลประเภทยานพาหนะ (vehicletypename) และเลขทะเบียนรถ (licenseplate) เพื่อรองรับการสะสมแต้ม การออกใบกำกับภาษี หรือบริการลูกค้าสัมพันธ์

   • product(ข้อมูลสินค้า) จัดเก็บรายละเอียดสินค้า ราคาต่อหน่วย ประเภทสินค้า ซัพพลายเออร์ และจำนวนสต็อกคงเหลือ
  
  2. กลุ่มธุรกรรมงานขาย 
  
ทำหน้าที่บันทึกข้อมูลการค้าและการให้บริการลูกค้ารายวัน โดยใช้รูปแบบการกระจายข้อมูลแบบ Master-Detail เพื่อรองรับการซื้อสินค้าหลายรายการต่อ 1 ใบเสร็จ

   • invoice (หัวใบเสร็จ / การขาย) บันทึกการทำรายการขายในภาพรวม เช่น วันที่และเวลาที่ทำรายการ (issuedate), ยอดรวมสุทธิ (totalamount), รูปแบบการชำระเงิน (paymentmethod) พร้อมระบุความสัมพันธ์ว่าเกิดที่สาขาใด (gasstationid), พนักงานคนใดเป็นผู้ขาย (employeeid), และขายให้แก่ลูกค้าคนใด (customerid)

   • invoicedetail (รายการสินค้าในใบเสร็จ) ทำหน้าที่เป็น Junction Table ระหว่าง invoice และ product เพื่อแจกแจงรายการสินค้า ปริมาณที่ซื้อ (quantitysold), ราคาขายต่อหน่วย ณ ขณะนั้น (sellingprice), และราคารวมของแต่ละบรรทัดรายการ (totalprice)
 
  3. กลุ่มคลังและการเคลื่อนไหวน้ำมันเชื้อเพลิง
ทำหน้าที่ควบคุมและตรวจสอบสต็อกน้ำมันเชื้อเพลิงทางกายภาพ

  • storagetank (ถังเก็บน้ำมันใต้ดิน/คลังน้ำมัน) บันทึกรายละเอียดถังบรรจุน้ำมันประจำสาขา (gasstationid), ชนิดน้ำมันเชื้อเพลิง (materialtype), ความจุสูงสุดของถัง (capcity), และปริมาณน้ำมันคงเหลือปัจจุบัน (currentquantity)

  • inventorytransaction (ประวัติการเคลื่อนไหวของน้ำมัน) บันทึก Log การรับน้ำมันเข้าคลัง (quantityin) และการจ่ายออก (quantityout) เชื่อมโยงกับ tankid พร้อมบันทึกยอดคงเหลือและเวลา เพื่อใช้ในการตรวจสอบยอดทางบัญชีและการสูญหายของน้ำมัน

---

## 2. โครงสร้างโปรเจกต์และกระบวนการ ELT (Project Structure)
โครงสร้างโปรเจกต์ทั้งหมด

```
Gasstation_KRK/
├── Gasstation_dw_duckdb/
│   ├── dbt_project.yml
│   ├── packages.yml / package-lock.yml
│   ├── check_schema.py
│   ├── app.py
│   ├── snapshots/
│   │   └── snap_storage_tank.sql           # SCD Type 2 Track ประวัติการเปลี่ยนแปลงถังน้ำมัน
│   └── models/
│       ├── staging/
│       │   ├── src_gas.yml                 # ประกาศ Data Sources (CSV Raw Files)
│       │   ├── stg_Customer.sql
│       │   ├── stg_Employee.sql
│       │   ├── stg_GasStation.sql
│       │   ├── stg_Product.sql
│       │   ├── stg_Invoice.sql
│       │   ├── stg_InvoiceDetail.sql
│       │   ├── stg_StorageTank.sql
│       │   └── stg_InventoryTransaction.sql
│       └── datawarehouse/
│           ├── schema.yml                  # Schema Validation & Unit Tests
│           ├── bridge_tank_product.sql     # Bridge Table เชื่อมมิติถังน้ำมันและผลิตภัณฑ์
│           ├── dim_customer.sql            # Dimensions (9 Tables)
│           ├── dim_date.sql
│           ├── dim_employee.sql
│           ├── dim_gasstation.sql
│           ├── dim_hour.sql
│           ├── dim_payment_method.sql
│           ├── dim_product.sql
│           ├── dim_tank.sql
│           ├── dim_vehicle_category.sql
│           ├── fact_sales.sql              # Fact Tables (3 Tables)
│           ├── fact_invoice.sql
│           ├── fact_inventory_transaction.sql
│           ├── int_sales_daily.sql         # Intermediate Transformations
│           ├── int_inventory_daily.sql
│           ├── mart_01_station_product_daily.sql   # Data Marts (15 Analytical Marts)
│           ├── mart_02_hourly_demand.sql
│           ├── mart_03_vehicle_fuel_station.sql
│           ├── mart_04_payment_value.sql
│           ├── mart_05_top10_customers.sql
│           ├── mart_06_repeat_purchase.sql
│           ├── mart_07_multi_station_customers.sql
│           ├── mart_08_employee_workload.sql
│           ├── mart_09_wow_change.sql
│           ├── mart_10_product_affinity.sql
│           ├── mart_11_inventory_imbalance.sql
│           ├── mart_12_low_fuel_frequency.sql
│           ├── mart_13_refill_pattern.sql
│           ├── mart_14_sales_dispense_reconciliation.sql
│           └── mart_15_reorder_priority.sql
├── app_old.py                              # Streamlit Dashboard App
├── query_duckdb.py                         # DuckDB Inspection Utility
├── build_warehouse.py                      # Automated Build Wrapper Script
├── requirements.txt
└── README.md
```
---

## 3. Business Questions (15 ข้อ)
1. สถานีใดสร้างยอดขายสูงสุดในแต่ละวัน และยอดขายมาจากน้ำมันชนิดใดเป็นหลัก

2. แต่ละสถานีมีช่วงเวลาขายหนาแน่นต่างกันอย่างไร เมื่อแยกตามวันในสัปดาห์และชนิดน้ำมัน เพื่อวางแผนรองรับความต้องการ

3. ลูกค้าที่ใช้รถแต่ละประเภทนิยมซื้อน้ำมันชนิดใด และรูปแบบการซื้อแตกต่างกันระหว่างสถานีอย่างไร

4. วิธีชำระเงินสัมพันธ์กับมูลค่าการซื้ออย่างไร เมื่อจำแนกตามประเภทรถ สถานี และช่วงเวลา

5. ลูกค้า 10 อันดับแรกที่สร้างยอดขายสูงสุดของแต่ละสถานีใช้รถประเภทใด และซื้อน้ำมันชนิดใดเป็นหลัก

6. ลูกค้ารถแต่ละประเภทกลับมาซื้อซ้ำที่สถานีเดิมมากน้อยเพียงใด และแตกต่างกันระหว่างสถานีอย่างไรในช่วงข้อมูลที่มี

7. ลูกค้ากลุ่มใดใช้บริการหลายสถานี และยอดขายของลูกค้ากลุ่มนี้กระจายระหว่างสถานีและชนิดน้ำมันอย่างไร

8. พนักงานแต่ละคนและแต่ละตำแหน่งมีปริมาณรายการขายที่บันทึกแตกต่างกันอย่างไร ตามสถานี วัน และช่วงเวลา เพื่อใช้ประกอบการวางแผนกำลังคน

9. ยอดขายของแต่ละสถานีเพิ่มขึ้นหรือลดลงจากวันเดียวกันในสัปดาห์ก่อนเท่าใด และน้ำมันชนิดใดมีส่วนต่อการเปลี่ยนแปลงมากที่สุด

10. ในแต่ละสถานี ลูกค้ารถประเภทใดมักซื้อน้ำมันหลายชนิดในบิลเดียว และคู่สินค้าใดปรากฏร่วมกันบ่อยที่สุด

11. สถานีและชนิดน้ำมันใดมีปริมาณรับเข้าไม่สมดุลกับปริมาณจ่ายออกในแต่ละวัน เพื่อทบทวนแผนเติมน้ำมัน

12. ถังของสถานีใดมีระดับน้ำมันต่ำกว่าเกณฑ์ที่กำหนดบ่อยที่สุด และเกิดกับน้ำมันชนิดใดในช่วงเวลาใด

13. การเติมน้ำมันแต่ละครั้งของแต่ละสถานีมีขนาดและความถี่เหมาะสมกับความจุถังและอัตราจ่ายออกของน้ำมันแต่ละชนิดเพียงใด

14. ปริมาณขายตามใบเสร็จตรงกับปริมาณจ่ายออกจากถังหรือไม่ และส่วนต่างกระจุกตัวที่สถานี น้ำมันชนิด หรือวันใด

15. เมื่ออิงยอดคงเหลือ ณ สิ้นสุดข้อมูลและอัตราขายเฉลี่ยย้อนหลัง 7 วัน สถานีและน้ำมันชนิดใดควรได้รับการเติมก่อน

## 4.Data Cube Diagram
Data Cube นี้ได้รับการออกแบบในรูปแบบ **Galaxy Schema** (หรือ *Fact Constellation Schema*) เนื่องจากระบบมีตาราง **Fact ถึง 3 ตาราง** ได้แก่ `fact_sales`, `fact_invoice` และ `fact_inventory_transaction` ซึ่งรองรับมิติการวิเคราะห์ที่หลากหลาย โดยตาราง Fact ทั้งหมดนี้มีการเชื่อมโยงและใช้งานตารางมิติร่วมกัน เช่น `dim_date`, `dim_hour`, `dim_gasstation`, `dim_product`, `dim_customer` และ `dim_employee` ทำให้สามารถวิเคราะห์ข้อมูลข้ามฟังก์ชันได้อย่างมีประสิทธิภาพ

### แผนผัง Data Cube (Galaxy Schema Diagram)
![Galaxy Schema](./Galaxy%20Schema.jpg)
### รายละเอียดโครงสร้าง Data Cube (Data Cube Specification)

#### 1. ตารางข้อเท็จจริง (Fact Tables)

| ตาราง Fact | Primary Key / Foreign Keys | Measures (ตัวชี้วัด) | รายละเอียดและบทบาททางธุรกิจ |
| :--- | :--- | :--- | :--- |
| **`fact_sales`** | `invoice_detail_id`<br>• `date_key`<br>• `hour_of_day`<br>• `gasstation_id`<br>• `customer_id`<br>• `employee_id`<br>• `product_id`<br>• `payment_method_key` | • `quantity_sold`<br>• `unit_price`<br>• `total_price` | บันทึกข้อมูลการขายสินค้ารายบรรทัด (Line-item level) เหมาะสำหรับการวิเคราะห์ยอดขายแยกตามรายสินค้า/ชนิดน้ำมัน เพื่อตอบ Business Questions ข้อ 1, 3, 5, 9, 10 |
| **`fact_invoice`** | `invoice_id`<br>• `date_key`<br>• `hour_of_day`<br>• `gasstation_id`<br>• `customer_id`<br>• `employee_id`<br>• `payment_method_key`<br>• `vehicle_type_key` | • `total_amount` | บันทึกสรุปรวมระดับใบเสร็จ/ธุรกรรม (Header level) ใช้สำหรับการวิเคราะห์พฤติกรรมการซื้อตามประเภทพาหนะ ช่องทางการชำระเงิน การซื้อซ้ำ และการกระจายตัวของลูกค้า เพื่อตอบ Business Questions ข้อ 3, 4, 6, 7 |
| **`fact_inventory_transaction`** | `transaction_id`<br>• `date_key`<br>• `hour_of_day`<br>• `gasstation_id`<br>• `tank_id`<br>• `product_id`| • `quantity_in`<br>• `quantity_out`<br>•`remaining_quantity` | • บันทึก Log การเคลื่อนไหวของน้ำมันในถังเก็บ (รับเข้า, จ่ายออก, ยอดคงเหลือ)ใช้ในการตรวจสอบสต็อก ตรวจจับน้ำมันรั่วไหล/สูญหาย และวางแผนการเติมน้ำมัน เพื่อตอบ Business Questions ข้อ 11, 12, 13, 14, 15 |


#### 2. ตารางมิติที่ใช้งานร่วมกัน (Conformed Dimension Tables)

* **`dim_date`**: มิติด้านวันที่ (ปี, เดือน, วัน, วันในสัปดาห์, วันหยุดเสาร์-อาทิตย์, วันเริ่มต้น/สิ้นสุดเดือน) สำหรับทำ Time-series Analysis และ DoD/WoW Comparison
* **`dim_hour`**: มิติด้านช่วงเวลา (`hour_of_day`, `day_part`) สำหรับวิเคราะห์ช่วงเวลาขายหนาแน่น (Peak Hours) และการวางแผนกำลังคน
* **`dim_gasstation`**: มิติสถานีบริการน้ำมัน (ชื่อสาขา, ที่อยู่, เบอร์โทรศัพท์) สำหรับเปรียบเทียบผลการดำเนินงานรายสาขา
* **`dim_employee`**: มิติพนักงาน (ชื่อ, ตำแหน่ง, สาขาต้นสังกัด `home_gasstation_id`, วันเริ่มงาน) สำหรับวัดประสิทธิภาพและภาระงานของบุคลากร
* **`dim_customer`**: มิติลูกค้า/สมาชิก (ชื่อ, ที่อยู่, เบอร์โทร, ประเภทพาหนะ, ทะเบียนรถ) สำหรับทำ Customer Segmentation & Loyalty Analytics
* **`dim_product`**: มิติสินค้า/น้ำมันเชื้อเพลิง (ชื่อสินค้า, ประเภทสินค้า `product_type`,ซัพพลายเออร์, ราคาต่อหน่วย, หน่วยนับ)
* **`dim_payment_method`**: มิติช่องทางการชำระเงิน (เงินสด, บัตรเครดิต, สแกน QR)
* **`dim_vehicle_category`**: มิติหมวดหมู่ยานพาหนะ (รถยนต์ส่วนบุคคล, รถบรรทุก, รถจักรยานยนต์)
* **`dim_tank` & `bridge_tank_product`**: มิติทรัพย์สินถังเก็บน้ำมันใต้ดิน ความจุ และตารางสะพานเชื่อมแบบDynamic Mapping เพื่อรองรับการเปลี่ยนประเภทน้ำมันบรรจุในถังตามช่วงเวลา(SCD Type 2 Pattern)

---
* [คลิกที่นี่เพื่อเปิดดู ER Diagram บน Google Drive](https://drive.google.com/file/d/1p_veBgEP3hKBFL9z522rmi3cKWPJ4uxq/view?usp=sharing)

![Operational ER Diagram](Data_Model_Diagram.drawio.png)

## Interactive Web Application & Analytics Dashboard

โปรเจกต์นี้ได้รับการพัฒนาและเปิดให้เข้าใช้งานผ่านStreamlit Web Application ที่รวมทั้งระบบตรวจเช็กคลังข้อมูล(DW Inspector)และแดชบอร์ดวิเคราะห์ธุรกิจ(Executive Analytics)ไว้ในระบบเดียว:

สามารถเข้าสู่หน้าแอปพลิเคชันได้ 2 วิธี ดังนี้:

## 1. เข้าใช้งานผ่านลิงก์ (URL)
คลิกที่ลิงก์ด้านล่างเพื่อเปิดหน้าเว็บไซต์ได้โดยตรงบนเบราว์เซอร์: 
**Live Demo Web Application:**
[เข้าใช้งาน GasStation Enterprise DW & Analytics Studio](https://kdvxcyh5deojv4aewtnmwb.streamlit.app/)

## 2. เข้าใช้งานด้วยการสแกน QR Code
คุณสามารถใช้แอปพลิเคชันกล้องถ่ายรูปในสมาร์ทโฟน(iOS/Android)หรือแอปพลิเคชันสแกนQRหรือLINEเพื่อสแกนรูปภาพQR Codeด้านล่างนี้ระบบจะพาคุณไปยังหน้าเว็บไซต์ทันที
<img width="1000" height="1000" alt="qrcode_399807304_e48b6be23f710493606f9ddc4a216e22 (2)" src="https://github.com/user-attachments/assets/d578cb4b-e1b7-461f-92c4-2c114d732a8a" />





---

## โครงสร้างฟังก์ชันการทำงานบน Web Application

=======
>>>>>>> krk_gas
