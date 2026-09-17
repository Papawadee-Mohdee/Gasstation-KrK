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

* **ชุดข้อมูลต้นทาง:** GasStationDB (HCM City - PostgreSQL) จาก Kaggle ครอบคลุมช่วงเวลา 24 วัน (15 มีนาคม – 7 เมษายน 2024)[cite: 1, 2]
* **ขอบเขตระบบ:** บันทึกธุรกรรมการขายน้ำมันประจำวัน การจัดการคลังน้ำมัน หัวจ่าย พนักงาน และลูกค้า รวม 24 วัน
* **ER Diagram ต้นทาง:** [คลิกเปิดดู ER Diagram บน Google Drive](https://drive.google.com/file/d/1JGIX7BkISNF0DNA6mARoEywLSQCLhmJH/view)

![Operational ER Diagram](ER_gas.drawio.png)

แบบจำลองฐานข้อมูลเชิงสัมพันธ์นี้ ออกแบบเพื่อรองรับการดำเนินงานบริหารจัดการสถานีบริการน้ำมัน ครอบคลุมกระบวนการขาย บุคลากรประจำสาขา และปริมาณน้ำมันคงคลัง แบ่งเป็น 3 กลุ่มหลักดังนี้:
1. **กลุ่มข้อมูลหลักและโครงสร้างสาขา:** ทำหน้าที่จัดเก็บข้อมูลพื้นฐานที่ใช้ในการอ้างอิงทั่วทั้งระบบ ได้แก่ `gasstation` (ข้อมูลสถานีบริการน้ำมัน), `employee` (ข้อมูลพนักงาน), `customer` (ข้อมูลลูกค้า พร้อมประเภทยานพาหนะและทะเบียนรถ), และ `product` (ข้อมูลสินค้า)
2. **กลุ่มธุรกรรมงานขาย:** บันทึกข้อมูลการค้าและการให้บริการลูกค้ารายวันด้วยรูปแบบ Master-Detail ประกอบด้วย `invoice` (หัวใบเสร็จ / การขาย) และ `invoicedetail` (รายการสินค้าในใบเสร็จ) เป็น Junction Table
3. **กลุ่มคลังและการเคลื่อนไหวน้ำมันเชื้อเพลิง:** ควบคุมและตรวจสอบสต็อกน้ำมันทางกายภาพ ประกอบด้วย `storagetank` (ถังเก็บน้ำมันใต้ดิน/คลังน้ำมัน) และ `inventorytransaction` (ประวัติการเคลื่อนไหวของน้ำมัน)

---

## 2. แนวคิดพื้นฐาน: Dimension และ Fact

### 2.1 Dimension Table (ตารางมิติ)
เก็บข้อมูลเชิงพรรณนา (Descriptive Attributes) ของสิ่งที่เราต้องการใช้อธิบายหรือกรองข้อมูล เช่น ใคร (ลูกค้า, พนักงาน), อะไร (สินค้า), ที่ไหน (สถานี), เมื่อไหร่ (วันที่, ชั่วโมง)[cite: 1, 2]
* แต่ละแถวแทน 1 หน่วยจริงที่ไม่ซ้ำกัน และมี Primary Key (เช่น `customer_id`, `product_id`)[cite: 1, 2]
* มีจำนวนแถวค่อนข้างคงที่และเปลี่ยนแปลงช้า (Slowly Changing) เมื่อเทียบกับตาราง Fact[cite: 1, 2]
* ใช้เป็นตัวกรอง (`WHERE`) หรือตัวจัดกลุ่ม (`GROUP BY`) เวลาวิเคราะห์ข้อมูล[cite: 1, 2]
* **การแบ่งกลุ่มในโปรเจกต์นี้:**
  * **กลุ่มโหลดจากข้อมูลธุรกรรมจริง:** `dim_customer`, `dim_employee`, `dim_gasstation`, `dim_product`, `dim_tank`[cite: 1, 2]
  * **กลุ่มสร้างขึ้นเอง / มาจากตารางอ้างอิง:** `dim_date`, `dim_hour`, `dim_payment_method`, `dim_vehicle_category`[cite: 1, 2]

### 2.2 Fact Table (ตารางข้อเท็จจริง)
เก็บเหตุการณ์หรือธุรกรรมที่วัดผลเป็นตัวเลขได้ (Measures) เช่น ยอดขาย, จำนวนที่ขาย, ปริมาณน้ำมันที่จ่ายออก[cite: 1, 2]
* แต่ละแถวแทน 1 เหตุการณ์ที่เกิดขึ้นจริง เรียกว่า Grain (ระดับความละเอียด)[cite: 1, 2]
* มี Foreign Key ชี้ไปยัง Dimension ต่างๆ และมีคอลัมน์วัดผล เช่น `total_amount`, `quantity_sold`[cite: 1, 2]
* มีจำนวนแถวมากและเติบโตเร็ว (เช่น `fact_sales` มีมากกว่า 1.5 ล้านแถว จากข้อมูลเพียง 24 วัน)[cite: 1, 2]
* **Fact Table ในโปรเจกต์นี้มี 3 ตัว:** `fact_invoice` (ระดับใบเสร็จ), `fact_sales` (ระดับรายการสินค้าในใบเสร็จ) และ `fact_inventory_transaction` (ระดับธุรกรรมคลังน้ำมัน)[cite: 1, 2]

### 2.3 ความสัมพันธ์ระหว่าง Dimension และ Fact
ตาราง Fact จะอยู่ตรงกลาง ล้อมรอบด้วยตาราง Dimension ที่เชื่อมกันผ่าน Foreign Key มีลักษณะคล้ายดาวเรียกว่า Star Schema การวิเคราะห์ทำได้โดย `JOIN` ตาราง Fact เข้ากับ Dimension แล้ว `GROUP BY` ตามคอลัมน์ใน Dimension นั้น[cite: 1, 2]

---

## 3. โครงสร้าง Data Cube ของโปรเจกต์นี้

เนื่องจากมี Fact Table ถึง 3 ตัวที่ใช้ Dimension บางส่วนร่วมกัน (Conformed Dimensions) รูปแบบ Data Cube ของระบบนี้จึงเป็น **Galaxy Schema** (หรือ Fact Constellation Schema - กลุ่มดาวหลายดวงเชื่อมกัน)[cite: 1, 2]

### 3.1 แผนผัง Data Cube (Galaxy Schema Diagram)
![Galaxy Schema](./Galaxy%20Schema.jpg)

### 3.2 ตาราง Fact ทั้ง 3 ตัว

| Fact Table | Grain (ความละเอียด) | Dimension ที่เชื่อมด้วย |
| :--- | :--- | :--- |
| **fact_invoice** | 1 แถว = 1 ใบเสร็จ[cite: 1, 2] | `dim_gasstation`, `dim_customer`, `dim_employee`, `dim_payment_method`, `dim_date`, `dim_hour`[cite: 1, 2] |
| **fact_sales** | 1 แถว = 1 รายการสินค้าในใบเสร็จ[cite: 1, 2] | `dim_gasstation`, `dim_customer`, `dim_employee`, `dim_product`, `dim_payment_method`, `dim_date`, `dim_hour`[cite: 1, 2] |
| **fact_inventory_transaction** | 1 แถว = 1 ธุรกรรมคลังน้ำมัน[cite: 1, 2] | `dim_gasstation`, `dim_tank`, `dim_product` (ผ่าน `bridge_tank_product`), `dim_date`, `dim_hour`[cite: 1, 2] |

### 3.3 Dimension ที่ใช้ร่วมกัน (Conformed Dimensions) และ ตาราง Bridge
* **Conformed Dimensions:** `dim_gasstation`, `dim_date`, `dim_hour` และ `dim_product` เป็น Conformed Dimensions ที่ถูกใช้ร่วมกันโดยมากกว่า 1 ตาราง Fact ทำให้สามารถเปรียบเทียบข้อมูลข้าม Fact ได้ ส่วน `dim_customer`, `dim_employee`, `dim_payment_method` ใช้เฉพาะกับ Fact ฝั่งการขาย และ `dim_tank` ใช้เฉพาะกับ Fact ฝั่งคลังน้ำมัน[cite: 1, 2]
* **Bridge Table (`bridge_tank_product`):** รวมการจับคู่ถัง-สินค้าจาก 2 แหล่ง ได้แก่ (1) การจับคู่ที่ตรวจทานด้วยมือจาก `stg_TankProductMap` (เฉพาะสถานะ `approved`) และ (2) การอนุมานจากชื่อถังเทียบกับชื่อสินค้าสำหรับถังที่ไม่มีข้อมูล เพื่อให้ถังทุกใบมีสินค้าจับคู่ครบถ้วน[cite: 1, 2]

---

## 4. กระบวนการ ELT (Extract – Load – Transform)

โปรเจกต์นี้ใช้แนวทาง ELT คือโหลดข้อมูลดิบเข้าฐานข้อมูลก่อน แล้วค่อยแปลงด้วยคำสั่ง SQL ภายในฐานข้อมูลเองผ่าน dbt[cite: 1, 2]

1. **Extract (สกัดข้อมูล):** CSV ดิบ 8 ไฟล์ (`Customer`, `Employee`, `GasStation`, `Invoice`, `InvoiceDetail`, `Product`, `StorageTank`, `InventoryTransaction`) และไฟล์ Seed 5 ไฟล์ (`ref_vehicle_category`, `ref_product_policy`, `ref_hour_bucket`, `ref_data_coverage`, `ref_tank_product_map`)[cite: 1, 2]
2. **Load (โหลดข้อมูล):** โหลดเข้า DuckDB เป็นสคีมา `main` โดยทุกคอลัมน์ถูกเก็บเป็น `VARCHAR` ทั้งหมด (ข้อมูล Seed โหลดผ่าน `dbt seed`)[cite: 1, 2]
3. **Transform (แปลงข้อมูล):** แปลงข้อมูลเป็นชั้นๆ (Layers) ผ่าน dbt models ตามสาย Dependency ที่ dbt จัดลำดับให้อัตโนมัติ[cite: 1, 2]

### โครงสร้างและหน้าที่ของแต่ละชั้น (Layers)

| ชั้น (Layer) | โฟลเดอร์ | หน้าที่หลัก |
| :--- | :--- | :--- |
| **Staging** | `models/staging/`[cite: 1, 2] | ดึงข้อมูลจาก Source/Seed มาตรงๆ, แปลงชนิดข้อมูลเฉพาะที่จำเป็น, ใส่ `ingestion_timestamp`[cite: 1, 2] |
| **Dimension / Fact** | `models/datawarehouse/`[cite: 1, 2] | Join, คัดกรองข้อมูลซ้ำ, เปลี่ยนชื่อคอลัมน์ให้เป็นแบบจำลองเชิงมิติ[cite: 1, 2] |
| **Intermediate** | `models/datawarehouse/`[cite: 1, 2] | พรีคำนวณผลรวมที่ใช้ซ้ำในหลาย Mart[cite: 1, 2] |
| **Mart** | `models/datawarehouse/`[cite: 1, 2] | ตารางสรุปสุดท้าย ตอบคำถามทางธุรกิจแต่ละข้อโดยตรง[cite: 1, 2] |

> **คำสั่งที่ใช้รันโปรเจกต์:**
> ```bash
> dbt seed    # โหลดตารางอ้างอิง
> dbt run     # รัน staging → dimension/fact → intermediate → mart
> dbt test    # ตรวจสอบคุณภาพข้อมูล (Data Quality Tests)
> ```

---

## 5. รายละเอียดเชิงลึกของแต่ละโมเดล (Model Details)

### 5.1 Staging Layer
โมเดลทุกตัวใช้รูปแบบ `SELECT *` จาก Source/Seed พร้อมเพิ่ม `ingestion_timestamp` และแปลงชนิดข้อมูลเฉพาะคอลัมน์ที่จำเป็น[cite: 1, 2]:
* **`stg_Customer`**, **`stg_Employee`**, **`stg_GasStation`**, **`stg_Product`**: โหลดข้อมูลดิบพร้อมใส่ Timestamp[cite: 1, 2]
* **`stg_Invoice`**: แปลง `TotalAmount` จาก Text เป็น Double[cite: 1, 2]
* **`stg_InvoiceDetail`**: แปลง `QuantitySold`, `SellingPrice`, `TotalPrice` จาก Text เป็น Double[cite: 1, 2]
* **`stg_StorageTank`**: แปลง `TankID` เป็น Bigint และ `Capacity`/`CurrentQuantity` เป็น Double[cite: 1, 2]
* **`stg_InventoryTransaction`**: แปลง `TankID` เป็น Bigint และปริมาณต่างๆ เป็น Double[cite: 1, 2]
* **`stg_TankProductMap`**: โหลดจาก Seed พร้อมแปลงวันที่ด้วย `try_cast` ป้องกันค่าว่าง[cite: 1, 2]

### 5.2 Dimension Tables
ใช้เทคนิค `ROW_NUMBER()` กรองข้อมูลซ้ำ (เอาแถวแรกที่สมบูรณ์ที่สุด) และเปลี่ยนชื่อคอลัมน์เป็นรูปแบบ `snake_case`[cite: 1, 2]:
* **`dim_customer`**: เชื่อมข้อมูลหมวดหมู่ยานพาหนะจาก Seed `ref_vehicle_category`[cite: 1, 2]
* **`dim_employee`**: แปลง `StartDate` เป็น Date[cite: 1, 2]
* **`dim_gasstation`**: ข้อมูลสถานีบริการ[cite: 1, 2]
* **`dim_product`**: เชื่อมข้อมูลการจัดประเภทเชื้อเพลิงจาก Seed `ref_product_policy`[cite: 1, 2]
* **`dim_tank`**: เก็บสถานะปัจจุบันของถังเก็บน้ำมัน[cite: 1, 2]
* **`dim_payment_method`**: สร้างจากค่าที่ไม่ซ้ำของวิธีชำระเงินในใบเสร็จ[cite: 1, 2]
* **`dim_vehicle_category`**: โหลดจาก Seed `ref_vehicle_category`[cite: 1, 2]
* **`dim_date`**: สร้างมิติวันที่ด้วย `generate_series()` ครอบคลุมช่วงวันที่ในระบบ คำนวณวันในสัปดาห์ วันหยุด[cite: 1, 2]
* **`dim_hour`**: สร้างมิติชั่วโมง (0-23) พร้อมช่วงเวลา (`day_part`)[cite: 1, 2]

### 5.3 Intermediate Tables (Pre-aggregated)
* **`int_sales_daily`**: สรุปยอดขายรายวัน แยกตามสถานี, สินค้า และวันที่ (`quantity_sold`, `total_price`)[cite: 1, 2]
* **`int_inventory_daily`**: สรุปธุรกรรมคลังน้ำมันรายวัน แยกตามสถานี, สินค้า และวันที่ (`quantity_in`, `quantity_out`)[cite: 1, 2]

### 5.4 Data Marts (15 Business Questions)
ตารางมาร์ทชั้นสุดท้าย ออกแบบเพื่อตอบคำถามทางธุรกิจโดยเฉพาะ
1. **`mart_01_station_sales_tiering`**: จัดกลุ่มสถานีบริการตามยอดขายเฉลี่ยต่อวัน (สูง/กลาง/ต่ำ) ด้วย `NTILE(3)`
2. **`mart_02_top_fuel_per_station`**: จัดอันดับสินค้าเชื้อเพลิงขายดีที่สุดในแต่ละสถานี (ปริมาณและมูลค่า)[cite: 1, 2]
3. **`mart_03_peak_hours`**: วิเคราะห์ชั่วโมงที่มีจำนวนบิลหนาแน่นที่สุดของแต่ละสถานี
4. **`mart_04_payment_mix`**: คำนวณสัดส่วนร้อยละของวิธีชำระเงินในแต่ละสถานี[cite: 1, 2]
5. **`mart_05_weekday_vs_weekend`**: เปรียบเทียบยอดขายระหว่างวันธรรมดาและวันหยุดสุดสัปดาห์[cite: 1, 2]
6. **`mart_06_top_employee_per_station`**: ค้นหาพนักงานที่ออกบิลมากที่สุดในแต่ละสถานี[cite: 1, 2]
7. **`mart_07_sales_by_road`**: จัดอันดับสถานีบริการตามชื่อถนนที่ตั้ง[cite: 1, 2]
8. **`mart_08_gasoline_vs_diesel`**: วิเคราะห์สัดส่วนยอดขายระหว่างกลุ่มน้ำมัน Gasoline และ Diesel[cite: 1, 2]
9. **`mart_09_daily_station_ranking`**: หาสถานีที่มียอดขายสูงสุดและต่ำสุดในแต่ละวัน พร้อมอัตราส่วน[cite: 1, 2]
10. **`mart_10_best_weekday_per_station`**: หาวันในสัปดาห์ที่ทำยอดขายได้ดีที่สุดของแต่ละสถานี[cite: 1, 2]
11. **`mart_11_dispense_vs_sales_variance`**: เปรียบเทียบปริมาณน้ำมันที่ขายกับที่จ่ายออกจากถัง (ตั้งธงส่วนต่างเกิน 5%)[cite: 1, 2]
12. **`mart_12_low_fuel_tanks`**: ตรวจสอบระดับน้ำมันคงเหลือ และตั้งธงแจ้งเตือนเมื่อต่ำกว่า 20%[cite: 1, 2]
13. **`mart_13_staffing_structure`**: วิเคราะห์สัดส่วนโครงสร้างตำแหน่งพนักงานในแต่ละสถานี[cite: 1, 2]
14. **`mart_14_credit_card_fee_simulation`**: จำลองต้นทุนค่าธรรมเนียมธุรกรรม 2% จากยอดชำระด้วยบัตรเครดิต[cite: 1, 2]
15. **`mart_15_revenue_per_employee`**: วิเคราะห์ประสิทธิภาพยอดขายและจำนวนบิลต่อพนักงาน 1 คน[cite: 1, 2]

---
