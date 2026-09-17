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

# เอกสารประกอบโครงการ Data Warehouse (Gas Station System)

โครงการนี้เป็นระบบคลังข้อมูล (Data Warehouse) สำหรับเครือข่ายสถานีบริการน้ำมัน สร้างด้วย **dbt (data build tool)** และ **DuckDB** โดยแปลงข้อมูลธุรกรรมดิบจากระบบปฏิบัติการ (OLTP) ได้แก่ ข้อมูลลูกค้า พนักงาน สถานีบริการ สินค้า ใบเสร็จ รายการขาย ถังเก็บน้ำมัน และธุรกรรมคลังน้ำมัน ให้กลายเป็นแบบจำลองเชิงมิติ (Dimensional Model) ที่พร้อมสำหรับการวิเคราะห์และสร้างรายงาน

ชุดข้อมูลต้นทางมาจาก **GasStationDB** (นครโฮจิมินห์) จาก Kaggle ครอบคลุมช่วงเวลา 24 วัน (15 มีนาคม – 7 เมษายน 2024) ประกอบด้วยตารางดิบ 8 ตาราง และตารางอ้างอิงเสริม (seed) อีก 5 ตาราง ผลลัพธ์สุดท้ายของคลังข้อมูลนี้ถูกนำไปใช้ตอบคำถามทางธุรกิจ 15 ข้อ (ผ่านตาราง mart) และใช้ขับเคลื่อนแดชบอร์ดวิเคราะห์ (Streamlit) แบบโต้ตอบได้

---

## สารบัญ

- [1. บทนำ](#1-บทนำ)
- [2. แนวคิดพื้นฐาน: Dimension และ Fact คืออะไร](#2-แนวคิดพื้นฐาน-dimension-และ-fact-คืออะไร)
  - [2.1 Dimension Table (ตารางมิติ)](#21-dimension-table-ตารางมิติ)
  - [2.2 Fact Table (ตารางข้อเท็จจริง)](#22-fact-table-ตารางข้อเท็จจริง)
  - [2.3 ความสัมพันธ์ระหว่าง Dimension และ Fact](#23-ความสัมพันธ์ระหว่าง-dimension-และ-fact)
- [3. โครงสร้าง Data Cube ของโปรเจกต์นี้](#3-โครงสร้าง-data-cube-ของโปรเจกต์นี้)
  - [3.1 ตาราง Fact ทั้ง 3 ตัว](#31-ตาราง-fact-ทั้ง-3-ตัว)
  - [3.2 Dimension ที่ใช้ร่วมกัน (Conformed Dimensions)](#32-dimension-ที่ใช้ร่วมกัน-conformed-dimensions)
  - [3.3 ตาราง Bridge](#33-ตาราง-bridge)
- [4. กระบวนการ ELT (Extract – Load – Transform)](#4-กระบวนการ-elt-extract--load--transform)
  - [4.1 Extract (สกัดข้อมูล)](#41-extract-สกัดข้อมูล)
  - [4.2 Load (โหลดข้อมูล)](#42-load-โหลดข้อมูล)
  - [4.3 Transform (แปลงข้อมูล)](#43-transform-แปลงข้อมูล)
- [5. รายละเอียด Staging Layer](#5-รายละเอียด-staging-layer)
- [6. รายละเอียด Dimension Tables](#6-รายละเอียด-dimension-tables)
- [7. รายละเอียด Bridge Table](#7-รายละเอียด-bridge-table)
- [8. รายละเอียด Fact Tables](#8-รายละเอียด-fact-tables)
- [9. รายละเอียด Intermediate Tables](#9-รายละเอียด-intermediate-tables)
- [10. รายละเอียด Data Mart](#10-รายละเอียด-data-mart)
- [11. สรุปภาพรวมทั้งระบบ](#11-สรุปภาพรวมทั้งระบบ)

---

## 1. บทนำ

โครงการนี้เป็นระบบคลังข้อมูล (Data Warehouse) สำหรับเครือข่ายสถานีบริการน้ำมัน สร้างด้วย **dbt** และ **DuckDB** โดยแปลงข้อมูลธุรกรรมดิบจากระบบปฏิบัติการ (OLTP) ได้แก่ ข้อมูลลูกค้า พนักงาน สถานีบริการ สินค้า ใบเสร็จ รายการขาย ถังเก็บน้ำมัน และธุรกรรมคลังน้ำมัน ให้กลายเป็นแบบจำลองเชิงมิติ (Dimensional Model) ที่พร้อมสำหรับการวิเคราะห์และสร้างรายงาน

ชุดข้อมูลต้นทางมาจาก **GasStationDB** (นครโฮจิมินห์) จาก Kaggle ครอบคลุมช่วงเวลา 24 วัน (15 มีนาคม – 7 เมษายน 2024) ประกอบด้วยตารางดิบ 8 ตาราง และตารางอ้างอิงเสริม (seed) อีก 5 ตาราง ผลลัพธ์สุดท้ายของคลังข้อมูลนี้ถูกนำไปใช้ตอบคำถามทางธุรกิจ 15 ข้อ (ผ่านตาราง mart) และใช้ขับเคลื่อนแดชบอร์ดวิเคราะห์ (Streamlit) แบบโต้ตอบได้

---

## 2. แนวคิดพื้นฐาน: Dimension และ Fact คืออะไร

### 2.1 Dimension Table (ตารางมิติ)
Dimension table เก็บ **"ข้อมูลเชิงพรรณนา" (descriptive attributes)** ของสิ่งที่เราต้องการใช้อธิบายหรือกรองข้อมูล เช่น ใคร (ลูกค้า, พนักงาน), อะไร (สินค้า), ที่ไหน (สถานี), เมื่อไหร่ (วันที่, ชั่วโมง) 

คุณสมบัติสำคัญของ dimension table มีดังนี้:
* แต่ละแถวแทน **1 หน่วยจริงที่ไม่ซ้ำกัน** (เช่น ลูกค้า 1 คน, สินค้า 1 รายการ) และมีคีย์หลัก (เช่น `customer_id`, `product_id`) ที่ไม่ซ้ำกันในตาราง
* มีจำนวนแถวค่อนข้างคงที่และเปลี่ยนแปลงช้า (Slowly Changing) เมื่อเทียบกับตาราง fact
* ใช้เป็นตัวกรอง (`WHERE`) หรือตัวจัดกลุ่ม (`GROUP BY`) เวลาวิเคราะห์ข้อมูล เช่น "ยอดขายแยกตามสถานี" หรือ "ยอดขายแยกตามประเภทรถของลูกค้า"
* ในโปรเจกต์นี้ dimension แบ่งเป็น 2 กลุ่ม: 
  * **กลุ่มที่โหลดมาจากข้อมูลธุรกรรมจริง:** `dim_customer`, `dim_employee`, `dim_gasstation`, `dim_product`, `dim_tank`
  * **กลุ่มที่สร้างขึ้นเอง / มาจากตารางอ้างอิง:** `dim_date`, `dim_hour`, `dim_payment_method`, `dim_vehicle_category`

### 2.2 Fact Table (ตารางข้อเท็จจริง)
Fact table เก็บ **"เหตุการณ์" หรือ "ธุรกรรม"** ที่วัดผลเป็นตัวเลขได้ (measures) เช่น ยอดขาย จำนวนที่ขาย ปริมาณน้ำมันที่จ่ายออก 

คุณสมบัติสำคัญประกอบด้วย:
* แต่ละแถวแทน **1 เหตุการณ์ที่เกิดขึ้นจริง** (เช่น 1 ใบเสร็จ, 1 รายการสินค้าที่ขาย, 1 ธุรกรรมคลัง) เรียกยานี้ว่า **grain (ระดับความละเอียด)** ของตาราง fact
* มีคอลัมน์ที่เป็น foreign key ชี้ไปยัง dimension table ต่างๆ ที่เกี่ยวข้อง (เช่น `gasstation_id`, `product_id`, `date_key`) และมีคอลัมน์ที่เป็นตัวเลขวัดผล (measure) เช่น `total_amount`, `quantity_sold`
* มีจำนวนแถวมากและเติบโตเร็วตามธุรกรรมที่เกิดขึ้นจริง (`fact_sales` ในโปรเจกต์นี้มีมากกว่า 1.5 ล้านแถว จากข้อมูลเพียง 24 วัน)
* ในโปรเจกต์นี้มี fact table 3 ตัว: `fact_invoice` (ระดับใบเสร็จ), `fact_sales` (ระดับรายการสินค้าในใบเสร็จ) และ `fact_inventory_transaction` (ระดับธุรกรรมคลังน้ำมัน)

### 2.3 ความสัมพันธ์ระหว่าง Dimension และ Fact
ตาราง fact จะอยู่ตรงกลาง ล้อมรอบด้วยตาราง dimension ที่เชื่อมกันผ่าน foreign key เมื่อวาดเป็นแผนภาพจะมีลักษณะคล้ายดาว (แต่ละแขนคือ dimension หนึ่งตัว) จึงเรียกรูปแบบนี้ว่า **Star Schema** 

การวิเคราะห์ข้อมูลทำได้โดย `JOIN` ตาราง fact เข้ากับ dimension ที่ต้องการ แล้ว `GROUP BY` ตามคอลัมน์ใน dimension นั้น เช่น ต้องการ "ยอดขายรวมของแต่ละสถานี" ก็ `JOIN` ระหว่าง `fact_invoice` กับ `dim_gasstation` แล้ว `GROUP BY gasstation_name`

---

## 3. โครงสร้าง Data Cube ของโปรเจกต์นี้

เนื่องจากโปรเจกต์นี้มีตาราง fact มากกว่า 1 ตัว (3 ตัว) ที่ใช้ dimension บางส่วนร่วมกัน (conformed dimensions) รูปแบบ Data Cube ของระบบนี้จึงเป็น **Galaxy Schema** หรือเรียกอีกชื่อว่า **Fact Constellation Schema** (กลุ่มดาวหลายดวงเชื่อมกัน) ไม่ใช่ Star Schema แบบธรรมดาที่มี fact เดียว

### 3.1 ตาราง Fact ทั้ง 3 ตัว

| Fact Table | Grain (ความละเอียด) | Dimension ที่เชื่อมด้วย |
| :--- | :--- | :--- |
| **fact_invoice** | 1 แถว = 1 ใบเสร็จ | `dim_gasstation`, `dim_customer`, `dim_employee`, `dim_payment_method`, `dim_date`, `dim_hour` |
| **fact_sales** | 1 แถว = 1 รายการสินค้าในใบเสร็จ | `dim_gasstation`, `dim_customer`, `dim_employee`, `dim_product`, `dim_payment_method`, `dim_date`, `dim_hour` |
| **fact_inventory_transaction** | 1 แถว = 1 ธุรกรรมคลังน้ำมัน | `dim_gasstation`, `dim_tank`, `dim_product` (ผ่าน `bridge_tank_product`), `dim_date`, `dim_hour` |

### 3.2 Dimension ที่ใช้ร่วมกัน (Conformed Dimensions)
`dim_gasstation`, `dim_date`, `dim_hour` และ `dim_product` เป็น conformed dimension คือถูกใช้ร่วมกันโดยมากกว่า 1 ตาราง fact ทำให้สามารถเปรียบเทียบข้อมูลข้าม fact ได้ (เช่น เทียบยอดขายจาก `fact_sales` กับปริมาณจ่ายออกจาก `fact_inventory_transaction` ในช่วงวันเดียวกัน ผ่าน `dim_date` ร่วมกัน) 

ส่วน `dim_customer`, `dim_employee` และ `dim_payment_method` ใช้เฉพาะกับ `fact_invoice`/`fact_sales` และ `dim_tank` ใช้เฉพาะกับ `fact_inventory_transaction`

### 3.3 ตาราง Bridge
เนื่องจากข้อมูลดิบไม่มีความสัมพันธ์โดยตรงระหว่างถังเก็บน้ำมัน (`tank`) กับสินค้า/ชนิดน้ำมัน (`product`) จึงต้องมีตาราง `bridge_tank_product` ทำหน้าที่เป็นตัวกลางเชื่อม `dim_tank` เข้ากับ `dim_product` ก่อนที่ `fact_inventory_transaction` จะระบุ `product_id` ได้

---

## 4. กระบวนการ ELT (Extract – Load – Transform)

โปรเจกต์นี้ใช้แนวทาง **ELT** (ตรงข้ามกับ ETL แบบดั้งเดิม) คือโหลดข้อมูลดิบเข้าฐานข้อมูลก่อน แล้วค่อยแปลง (Transform) ด้วยคำสั่ง SQL ภายในฐานข้อมูลเอง (ผ่าน dbt) แทนที่จะแปลงข้อมูลก่อนโหลด

### 4.1 Extract (สกัดข้อมูล)
ข้อมูลต้นทางเป็นไฟล์ CSV 8 ไฟล์ที่แทนตารางในระบบ OLTP ได้แก่ `Customer.csv`, `Employee.csv`, `GasStation.csv`, `Invoice.csv`, `InvoiceDetail.csv`, `Product.csv`, `StorageTank.csv` และ `InventoryTransaction.csv` รวมถึงไฟล์ CSV อ้างอิงเพิ่มเติม (seed) อีก 5 ไฟล์ที่ทีมงานสร้างขึ้นเอง (`ref_vehicle_category`, `ref_product_policy`, `ref_hour_bucket`, `ref_data_coverage`, `ref_tank_product_map`)

### 4.2 Load (โหลดข้อมูล)
ไฟล์ CSV ทั้ง 8 ไฟล์ถูกโหลดเข้า DuckDB เป็นตารางในสคีมา `main` โดย **ทุกคอลัมน์ถูกเก็บเป็นชนิดข้อความ (`VARCHAR`) ทั้งหมด** ไม่มีการแปลงชนิดข้อมูลใดๆ ในขั้นตอนนี้ ตารางเหล่านี้ถูกอ้างอิงในโปรเจกต์ dbt ผ่าน `source()` (ประกาศไว้ในไฟล์ `src_gas.yml`) ส่วนไฟล์ seed ทั้ง 5 ไฟล์ถูกโหลดผ่านคำสั่ง `dbt seed` ซึ่ง dbt จะพยายามเดาชนิดข้อมูลให้จากเนื้อหาจริงในไฟล์ (จึงมักจะได้ชนิดข้อมูลที่ถูกต้องกว่า)

การที่ตาราง source เก็บทุกคอลัมน์เป็น `VARCHAR` หมด ทำให้ขั้นตอน Transform ในชั้น staging ต้องรับผิดชอบแปลงชนิดข้อมูลให้ถูกต้องก่อนนำไปคำนวณต่อ (ดูหัวข้อ 5)

### 4.3 Transform (แปลงข้อมูล)
การแปลงข้อมูลทำเป็นชั้นๆ (layers) ผ่าน dbt models โดยแต่ละชั้นอ้างอิง (`ref`) ชั้นก่อนหน้า ทำให้เกิดเป็นสาย dependency ที่ dbt จัดลำดับการรันให้อัตโนมัติ:

| ชั้น (Layer) | โฟลเดอร์ | หน้าที่ |
| :--- | :--- | :--- |
| **Staging** | `models/staging/` | ดึงข้อมูลจาก source/seed มาตรงๆ, แปลงชนิดข้อมูลเฉพาะคอลัมน์ที่จำเป็น, ใส่ `ingestion_timestamp` |
| **Dimension / Fact** | `models/datawarehouse/` | join / คัดข้อมูลซ้ำ / เปลี่ยนชื่อคอลัมน์จาก staging ให้เป็นแบบจำลองเชิงมิติ |
| **Intermediate** | `models/datawarehouse/` | พรีคำนวณผลรวมที่ใช้ซ้ำในหลาย mart |
| **Mart** | `models/datawarehouse/` | ตารางสรุปสุดท้าย ตอบคำถามทางธุรกิจแต่ละข้อโดยตรง |

คำสั่งที่ใช้รันกระบวนการทั้งหมด: `dbt seed` (โหลดตารางอ้างอิง) ตามด้วย `dbt run` (รัน staging → dimension/fact → intermediate → mart ตามลำดับ dependency) และ `dbt test` (ตรวจสอบคุณภาพข้อมูล เช่น ค่าไม่ซ้ำ ไม่เป็นค่าว่าง ตามที่กำหนดไว้ใน `schema.yml`)

---

## 5. รายละเอียด Staging Layer

โมเดลในชั้นนี้ทุกตัวมีรูปแบบเดียวกัน: `select *` จาก source/seed แล้วเพิ่มคอลัมน์ `ingestion_timestamp` (เวลาที่ดึงข้อมูล) โดยจะแปลงชนิดข้อมูล (`cast`) เฉพาะคอลัมน์ที่ถูกนำไปคำนวณเชิงตัวเลขหรือใช้เป็นคีย์เปรียบเทียบในขั้นตอนถัดไปเท่านั้น เพื่อให้โค้ดเรียบง่ายที่สุดเท่าที่จำเป็น

* **`stg_Customer`**: โหลดข้อมูลลูกค้าดิบจากตาราง source ชื่อ `customer` มาทั้งหมด แล้วเพิ่มคอลัมน์ `ingestion_timestamp` บันทึกเวลาที่ดึงข้อมูลเข้ามา
* **`stg_Employee`**: โหลดข้อมูลพนักงานดิบจากตาราง source ชื่อ `employee` มาทั้งหมด แล้วเพิ่ม `ingestion_timestamp`
* **`stg_GasStation`**: โหลดข้อมูลสถานีบริการดิบจากตาราง source ชื่อ `gasstation` มาทั้งหมด แล้วเพิ่ม `ingestion_timestamp`
* **`stg_Product`**: โหลดข้อมูลสินค้าดิบจากตาราง source ชื่อ `product` มาทั้งหมด แล้วเพิ่ม `ingestion_timestamp`
* **`stg_Invoice`**: โหลดข้อมูลใบเสร็จดิบจากตาราง source ชื่อ `invoice`, แปลงคอลัมน์ `TotalAmount` จาก text เป็น double (ตาราง source เก็บทุกคอลัมน์เป็นตัวอักษรล้วน) แล้วเพิ่ม `ingestion_timestamp`
* **`stg_InvoiceDetail`**: โหลดข้อมูลรายการสินค้าในใบเสร็จดิบจากตาราง source ชื่อ `invoicedetail`, แปลงคอลัมน์ `QuantitySold`, `SellingPrice` และ `TotalPrice` จาก text เป็น double แล้วเพิ่ม `ingestion_timestamp`
* **`stg_StorageTank`**: โหลดข้อมูลถังเก็บน้ำมันดิบจากตาราง source ชื่อ `storagetank`, แปลง `TankID` เป็น bigint และ `Capacity`/`CurrentQuantity` เป็น double แล้วเพิ่ม `ingestion_timestamp`
* **`stg_InventoryTransaction`**: โหลดข้อมูลธุรกรรมคลังน้ำมันดิบจากตาราง source ชื่อ `inventorytransaction`, แปลง `TankID` เป็น bigint และ `QuantityIn`/`QuantityOut`/`RemainingQuantity` เป็น double แล้วเพิ่ม `ingestion_timestamp`
* **`stg_TankProductMap`**: โหลดตารางจับคู่ถัง-สินค้าที่ตรวจทานด้วยมือจาก seed ชื่อ `ref_tank_product_map`, แปลง `valid_from`, `valid_to` และ `reviewed_at` เป็น timestamp ด้วย `try_cast` (เพราะบางแถวมีค่าว่าง) แล้วเพิ่ม `ingestion_timestamp`

---
