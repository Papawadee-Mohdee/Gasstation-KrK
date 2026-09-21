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

## Operational Database (OLTP)

* **ชุดข้อมูลต้นทาง:** GasStationDB (HCM City - PostgreSQL) จาก Kaggle ครอบคลุมช่วงเวลา 24 วัน (15 มีนาคม – 7 เมษายน 2024)[cite: 1, 2]
* **ขอบเขตระบบ:** บันทึกธุรกรรมการขายน้ำมันประจำวัน การจัดการคลังน้ำมัน หัวจ่าย พนักงาน และลูกค้า รวม 24 วัน
* **ER Diagram ต้นทาง:** [คลิกเปิดดู ER Diagram บน Google Drive](https://drive.google.com/file/d/1JGIX7BkISNF0DNA6mARoEywLSQCLhmJH/view)

![Operational ER Diagram](ER_gas.drawio.png)

แบบจำลองฐานข้อมูลเชิงสัมพันธ์นี้ ออกแบบเพื่อรองรับการดำเนินงานบริหารจัดการสถานีบริการน้ำมัน ครอบคลุมกระบวนการขาย บุคลากรประจำสาขา และปริมาณน้ำมันคงคลัง แบ่งเป็น 3 กลุ่มหลักดังนี้:
1. **กลุ่มข้อมูลหลักและโครงสร้างสาขา:** ทำหน้าที่จัดเก็บข้อมูลพื้นฐานที่ใช้ในการอ้างอิงทั่วทั้งระบบ ได้แก่ `gasstation` (ข้อมูลสถานีบริการน้ำมัน), `employee` (ข้อมูลพนักงาน), `customer` (ข้อมูลลูกค้า พร้อมประเภทยานพาหนะและทะเบียนรถ), และ `product` (ข้อมูลสินค้า)
2. **กลุ่มธุรกรรมงานขาย:** บันทึกข้อมูลการค้าและการให้บริการลูกค้ารายวันด้วยรูปแบบ Master-Detail ประกอบด้วย `invoice` (หัวใบเสร็จ / การขาย) และ `invoicedetail` (รายการสินค้าในใบเสร็จ) เป็น Junction Table
3. **กลุ่มคลังและการเคลื่อนไหวน้ำมันเชื้อเพลิง:** ควบคุมและตรวจสอบสต็อกน้ำมันทางกายภาพ ประกอบด้วย `storagetank` (ถังเก็บน้ำมันใต้ดิน/คลังน้ำมัน) และ `inventorytransaction` (ประวัติการเคลื่อนไหวของน้ำมัน)

---
---
## Galaxy Schema

* **ER Diagram (PDF):** [คลิกเพื่อเปิดดูไฟล์ Galaxy_Schema.pdf](./Galaxy_Schema.pdf)

![Galaxy Schema Diagram](Galaxy_Schema.png) **แก้ใหม่เป็นอัปเป็นรูปนะนี่เผลอลงเป็นpdf**
---
## 15 คำถามทางธุรกิจ (Business Questions)

คลังข้อมูลชุดนี้ได้รับการออกแบบและพัฒนาตาราง Data Mart ขึ้นมา เพื่อตอบคำถามเชิงวิเคราะห์ทางธุรกิจสำหรับเครือข่ายสถานีบริการน้ำมันทั้งสิ้น 15 ข้อ ดังนี้:

### กลุ่มการวิเคราะห์ยอดขายและประสิทธิภาพสถานีบริการ (Sales & Station Performance)
1. **ยอดขายเฉลี่ยรายวันของแต่ละสถานีเป็นเท่าใด และเมื่อจัดกลุ่มสถานีตามระดับยอดขาย (Sales Tiering) แต่ละกลุ่มมีสัดส่วนเท่าใด?**
   * วิเคราะห์อัตราการเติบโตและจำแนกเกรดของสถานีบริการตามมูลค่าการขายรายวัน
2. **น้ำมันประเภทใด (RON95-III, E5 RON92-II หรือดีเซล) มียอดจำหน่ายสูงที่สุดในแต่ละสถานีบริการ ทั้งในแง่ปริมาณลิตรและมูลค่าเงิน?**
   * เปรียบเทียบความนิยมของประเภทน้ำมันเชื้อเพลิงแยกตามรายสาขา
3. **ช่วงเวลาใดในรอบวัน (ชั่วโมง 0–23 หรือช่วงกะ) ที่แต่ละสถานีมีปริมาณการออกบิลหนาแน่นที่สุด (Peak Hours)?**
   * ค้นหาช่วงเวลา Peak เพื่อวางแผนอัตรากำลังพลและการบริหารจัดการหน้าลาน
4. **สัดส่วนพฤติกรรมการชำระเงินระหว่างเงินสด (Cash) กับบัตรเครดิต (Credit Card) ในแต่ละสถานีบริการมีความแตกต่างกันอย่างไร?**
   * วิเคราะห์ช่องทางการชำระเงินยอดนิยมของลูกค้าในแต่ละพื้นที่
5. **ยอดขายรวมและปริมาณการออกบิลระหว่างวันธรรมดา (จันทร์–ศุกร์) กับวันหยุดสุดสัปดาห์ (เสาร์–อาทิตย์) มีความแตกต่างกันอย่างมีนัยสำคัญหรือไม่?**
   * เปรียบเทียบพฤติกรรมการใช้บริการตามช่วงวันในสัปดาห์

### กลุ่มการวิเคราะห์บุคลากรและพฤติกรรมลูกค้า (Employee & Customer Insights)
6. **พนักงานคนใดในแต่ละสถานีบริการมีจำนวนการออกบิลให้บริการลูกค้าสะสมสูงที่สุดตลอดช่วง 24 วัน?**
   * ติดตามผลงานและปริมาณงาน (Workload) ของพนักงานรายบุคคล
7. **สถานีบริการน้ำมันที่ตั้งอยู่บนถนนสายใดที่สร้างยอดขายรวมได้สูงที่สุดและต่ำที่สุด?**
   * ประเมินศักยภาพทำเลที่ตั้งของสถานีบริการ
8. **สัดส่วนยอดขายระหว่างน้ำมันกลุ่มเบนซิน (Gasoline) กับกลุ่มดีเซล (Diesel) ในแต่ละสถานีบริการเป็นเท่าใด?**
   * วิเคราะห์สัดส่วนประเภทพลังงานที่ทำรายได้หลักให้แก่แต่ละสาขา
9. **ในแต่ละวัน สถานีบริการใดทำยอดขายได้สูงสุดและต่ำสุด และมีส่วนต่างของยอดขายห่างกันกี่เท่า?**
   * เปรียบเทียบช่องว่างทางธุรกิจระหว่างสาขาที่ทำยอดขายสูงสุดและต่ำสุดในแต่ละวัน
10. **วันใดในรอบสัปดาห์ (จันทร์–อาทิตย์) ที่แต่ละสถานีบริการทำยอดขายเฉลี่ยได้สูงที่สุด?**
    * หาแพตเทิร์นวันขายดีประจำสัปดาห์ของแต่ละสาขา

### กลุ่มการวิเคราะห์คลังสินค้า ความเสี่ยง และความคุ้มค่า (Inventory, Risk & Cost Analysis)
11. **ปริมาณน้ำมันที่จ่ายออกจากถัง (Quantity Out) สอดคล้องกับยอดขายจริง (Quantity Sold) หรือไม่ และพบจุดคลาดเคลื่อนที่เสี่ยงต่อการสูญหายในสถานีใดบ้าง?**
    * ตรวจสอบความถูกต้องระหว่างสต็อกหน้าถังกับยอดขายจริงเพื่อป้องกันการสูญหาย (Loss Prevention)
12. **มีถังเก็บน้ำมันใบใดบ้างที่ระดับน้ำมันคงเหลือล่าสุดลดลงมาแตะเกณฑ์เตือนภัย (ประมาณ 20% ของความจุถัง) จนเสี่ยงต่อภาวะน้ำมันหมดถัง?**
    * เฝ้าระวังระดับสต็อกน้ำมันต่ำกว่ากำหนดเพื่อสั่งเติมน้ำมันได้ทันท่วงที
13. **โครงสร้างกำลังพลในแต่ละสถานีบริการประกอบด้วยตำแหน่งงานใดบ้าง และตำแหน่งใดมีสัดส่วนมากที่สุดในแต่ละสาขา?**
    * วิเคราะห์โครงสร้างบุคลากรภายในองค์กร
14. **หากกำหนดให้อัตราค่าธรรมเนียมบัตรเครดิตอยู่ที่ 2% ต้นทุนค่าธรรมเนียมธุรกรรมจำลองคิดเป็นสัดส่วนเท่าใดของยอดขายรวมในแต่ละสถานีบริการ?**
    * ประเมินผลกระทบด้านต้นทุนทางการเงินจากช่องทางการชำระเงินดิจิทัล
15. **สถานีบริการใดมีประสิทธิภาพยอดขายต่อพนักงาน (Revenue per Employee) สูงสุด และเมื่อเจาะลึกตามตำแหน่งงาน สาขาที่มียอดขายสูงมีพนักงานเติมน้ำมัน (Pump Attendant) เพียงพอต่อปริมาณงานหรือไม่?**
    * วิเคราะห์ความคุ้มค่าและประสิทธิภาพการใช้แรงงานเทียบกับรายได้ที่ทำได้
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

## 6. รายละเอียด Dimension Tables

โมเดลในชั้นนี้ทุกตัว (ยกเว้น `dim_payment_method`, `dim_vehicle_category`, `dim_date`, `dim_hour` ที่ไม่มีความเสี่ยงข้อมูลซ้ำ) ใช้รูปแบบเดียวกัน: `source CTE` (เลือก/เปลี่ยนชื่อคอลัมน์ + join ข้อมูลเสริม) ตามด้วย `unique_source CTE` (ใส่ `row_number()` แบ่งกลุ่มตามคีย์หลัก) แล้ว `select * exclude (row_num)` เอาเฉพาะแถวที่ `row_num = 1` เพื่อป้องกันคีย์ซ้ำ

* **`dim_customer`**: โหลดข้อมูลลูกค้าจาก `stg_Customer`, join ข้อมูลหมวดหมู่ยานพาหนะจาก seed `ref_vehicle_category` (จับคู่ด้วยชื่อประเภทรถตัวพิมพ์เล็ก), เปลี่ยนชื่อคอลัมน์เป็น `snake_case` (`customer_id`, `customer_name`, ...), คัดข้อมูลซ้ำออกด้วย `row_number()` แบ่งกลุ่มตาม `customer_id` แล้วเพิ่ม `ingestion_timestamp`
* **`dim_employee`**: โหลดข้อมูลพนักงานจาก `stg_Employee`, เปลี่ยนชื่อคอลัมน์เป็น `snake_case` (`employee_id`, `employee_name`, `home_gasstation_id`, ...), แปลง `StartDate` เป็น date, คัดข้อมูลซ้ำออกด้วย `row_number()` แบ่งกลุ่มตาม `employee_id` แล้วเพิ่ม `ingestion_timestamp`
* **`dim_gasstation`**: โหลดข้อมูลสถานีบริการจาก `stg_GasStation`, เปลี่ยนชื่อคอลัมน์เป็น `snake_case`, คัดข้อมูลซ้ำออกด้วย `row_number()` แบ่งกลุ่มตาม `gasstation_id` แล้วเพิ่ม `ingestion_timestamp`
* **`dim_product`**: โหลดข้อมูลสินค้าจาก `stg_Product`, join ข้อมูลการจัดประเภทน้ำมันเชื้อเพลิง (`is_fuel`, `unit_of_measure`) จาก seed `ref_product_policy`, เปลี่ยนชื่อคอลัมน์เป็น `snake_case`, คัดข้อมูลซ้ำออกด้วย `row_number()` แบ่งกลุ่มตาม `product_id` แล้วเพิ่ม `ingestion_timestamp`
* **`dim_tank`**: โหลดข้อมูลถังเก็บน้ำมันจาก `stg_StorageTank`, เปลี่ยนชื่อคอลัมน์เป็น `snake_case` (`tank_id`, `gasstation_id`, `capacity_liters`, `current_quantity`), คัดข้อมูลซ้ำออกด้วย `row_number()` แบ่งกลุ่มตาม `tank_id` แล้วเพิ่ม `ingestion_timestamp` *(เก็บเฉพาะสถานะปัจจุบันของถัง ไม่ได้ทำ SCD2 เก็บประวัติย้อนหลัง)*
* **`dim_payment_method`**: สร้างจากค่าที่ไม่ซ้ำ (`distinct`) ของวิธีชำระเงินใน `stg_Invoice` โดยตรง (`payment_method_key` เป็นตัวพิมพ์เล็กของ `PaymentMethod` ใช้เป็นคีย์, ข้อความเดิมเก็บเป็น `payment_method_label`) แล้วเพิ่ม `ingestion_timestamp`
* **`dim_vehicle_category`**: โหลดตารางหมวดหมู่ยานพาหนะจาก seed `ref_vehicle_category` โดยตรง (`vehicle_type_key`, `vehicle_type_label`, `vehicle_category`) แล้วเพิ่ม `ingestion_timestamp`
* **`dim_date`**: สร้างมิติวันที่ด้วย `generate_series()` ครอบคลุมตั้งแต่วันที่ต่ำสุดถึงสูงสุดที่พบใน `stg_Invoice` และ `stg_InventoryTransaction` (ไม่ใช่ช่วงคงที่ เพราะข้อมูลของโปรเจกต์นี้มีแค่ 24 วัน), คำนวณ `date_key` (รูปแบบ YYYYMMDD), `date_day`, `year`, `month`, `day_of_month`, `iso_weekday`, `weekday_name`, `is_weekend` และ `is_complete_day` (join จาก seed `ref_data_coverage`) แล้วเพิ่ม `ingestion_timestamp`
* **`dim_hour`**: สร้างมิติชั่วโมงด้วย `generate_series()` ครอบคลุม 0–23, join ป้ายช่วงเวลา (`day_part`) จาก seed `ref_hour_bucket` ถ้ามี ถ้าไม่มีให้ใช้ค่าเริ่มต้นตามช่วงเวลา (เช้า/เที่ยง/บ่าย/เย็น/กลางคืน) แล้วเพิ่ม `ingestion_timestamp`

---

## 7. รายละเอียด Bridge Table

* **`bridge_tank_product`**: รวมการจับคู่ถัง-สินค้าจาก 2 แหล่งตามลำดับความน่าเชื่อถือ: 
  1. การจับคู่ที่ตรวจทานด้วยมือจาก `stg_TankProductMap` เฉพาะแถวที่ `review_status = 'approved'` ใช้ช่วงเวลา `valid_from`/สะพานเวลาของตัวเอง
  2. สำหรับถังที่ไม่มีการจับคู่ด้วยมือ ให้อนุมานจากชื่อถัง (`dim_tank.tank_name` ตัดคำว่า "Tank" ออก) เทียบกับชื่อสินค้า (`dim_product.product_name`) กำหนดช่วงเวลาเริ่มต้นที่ `1900-01-01` (ถือว่าผูกกับชนิดน้ำมันมาตั้งแต่ก่อนมีข้อมูล)
  * รวมสองแหล่งนี้แล้วถังทุกใบจะมีสินค้าที่จับคู่ได้ครบ

---

## 8. รายละเอียด Fact Tables

* **`fact_invoice`** (grain: 1 แถวต่อ 1 ใบเสร็จ): โหลดข้อมูลหัวใบเสร็จจาก `stg_Invoice`, คำนวณ `date_key` และ `hour_of_day` จาก `IssueDate`, เก็บ `gasstation_id`/`customer_id`/`employee_id` เป็น foreign key และ `total_amount` เป็น measure, แปลง `PaymentMethod` เป็น `payment_method_key` (ตัวพิมพ์เล็ก) แล้วกรองแถวที่ `invoice_id` เป็นค่าว่างออก
* **`fact_sales`** (grain: 1 แถวต่อ 1 รายการสินค้าในใบเสร็จ): รวมข้อมูลรายการสินค้าจาก `stg_InvoiceDetail` เข้ากับข้อมูลหัวใบเสร็จจาก `stg_Invoice` (join ด้วย `InvoiceID`) เพื่อดึง `date_key`, `hour_of_day`, `gasstation_id`, `customer_id`, `employee_id` และ `payment_method_key` มาด้วย, เก็บ `quantity_sold`, `unit_price`, `total_price` เป็น measure และ `product_id` เป็น foreign key แล้วกรองแถวที่ `invoice_detail_id` เป็นค่าว่างออก
* **`fact_inventory_transaction`** (grain: 1 แถวต่อ 1 ธุรกรรมคลังน้ำมัน): รวมข้อมูลธุรกรรมจาก `stg_InventoryTransaction` เข้ากับข้อมูลถังจาก `stg_StorageTank` (join ด้วย `TankID`) เพื่อดึง `gasstation_id` มาด้วย, `left join` กับ `bridge_tank_product` (จับคู่ด้วย `tank_id` และเวลาธุรกรรมต้องอยู่ในช่วง `valid_from`–`valid_to` ของการจับคู่) เพื่อหา `product_id`, คำนวณ `date_key` และ `hour_of_day` จาก `TransactionDate`, เก็บ `quantity_in`, `quantity_out`, `remaining_quantity` เป็น measure แล้วกรองแถวที่ `transaction_id` เป็นค่าว่างออก

---

## 9. รายละเอียด Intermediate Tables

ตารางในชั้นนี้ไม่ใช่ dimension หรือ fact โดยตรง แต่เป็นผลรวมที่พรีคำนวณไว้ล่วงหน้า (pre-aggregated) เพื่อให้ mart หลายตัวเรียกใช้ร่วมกันได้โดยไม่ต้อง JOIN/GROUP BY ตาราง fact ระดับรายละเอียดซ้ำหลายรอบ

* **`int_sales_daily`**: พรีคำนวณผลรวมจาก `fact_sales` แบ่งกลุ่มตาม `gasstation_id`, `product_id`, `date_key` รวม `quantity_sold` และ `total_price` พร้อมนับจำนวนรายการ เพื่อไม่ต้อง join ตาราง fact ระดับรายการซ้ำหลายครั้งในมาร์ทต่างๆ
* **`int_inventory_daily`**: พรีคำนวณผลรวมจาก `fact_inventory_transaction` (ตัดแถวที่หา `product_id` ไม่ได้ออก) แบ่งกลุ่มตาม `gasstation_id`, `product_id`, `date_key` รวม `quantity_in` และ `quantity_out`

---

## 10. รายละเอียด Data Mart

ตาราง mart เป็นชั้นสุดท้ายของคลังข้อมูลแต่ละตัวถูกออกแบบให้ตอบคำถามทางธุรกิจหนึ่งข้อโดยตรง (รวมทั้งหมด 15 ข้อ) ดึงข้อมูลจากตาราง dimension, fact และ intermediate ที่กล่าวมาข้างต้น พร้อมให้แดชบอร์ดหรือรายงานดึงไปแสดงผลได้ทันทีโดยไม่ต้องคำนวณซ้ำ

1. **`mart_01_station_sales_tiering`**: คำนวณยอดขายเฉลี่ยต่อวันของแต่ละสถานีจาก `fact_invoice` แล้วจัดกลุ่มเป็นสูง/กลาง/ต่ำด้วย `ntile(3)`
2. **`mart_02_top_fuel_per_station`**: รวมปริมาณลิตรและมูลค่าขายต่อสถานีต่อสินค้าเชื้อเพลิงจาก `int_sales_daily` แล้วจัดอันดับสินค้าภายในแต่ละสถานีทั้งตามปริมาณและมูลค่า เพื่อหาสินค้าขายดีที่สุด
3. **`mart_03_peak_hours`**: นับจำนวนบิลต่อสถานีต่อชั่วโมงจาก `fact_invoice`, join `dim_hour` เพื่อดึงป้ายช่วงเวลา แล้วจัดอันดับชั่วโมงภายในแต่ละสถานีเพื่อหาชั่วโมงที่มีบิลหนาแน่นที่สุด
4. **`mart_04_payment_mix`**: รวมจำนวนบิลและยอดขายต่อสถานีต่อวิธีชำระเงินจาก `fact_invoice` แล้วคำนวณสัดส่วนร้อยละของแต่ละวิธีต่อยอดขายรวมของสถานีนั้น
5. **`mart_05_weekday_vs_weekend`**: join `fact_invoice` กับ `dim_date` แล้วรวมจำนวนบิล ยอดขายรวม และยอดขายเฉลี่ยต่อบิล แบ่งตามสถานีและวันธรรมดา/วันหยุดสุดสัปดาห์
6. **`mart_06_top_employee_per_station`**: นับจำนวนบิลต่อสถานีต่อพนักงานจาก `fact_invoice`, join `dim_employee` เพื่อดึงชื่อ แล้วจัดอันดับพนักงานภายในแต่ละสถานีเพื่อหาผู้ที่ออกบิลมากที่สุด
7. **`mart_07_sales_by_road`**: รวมยอดขายต่อสถานีจาก `fact_invoice`, join `dim_gasstation` เพื่อตัดชื่อถนนออกจากที่อยู่ แล้วจัดอันดับสถานีจากยอดขายสูงสุดไปต่ำสุด
8. **`mart_08_gasoline_vs_diesel`**: รวมมูลค่าขายและปริมาณลิตรต่อสถานีต่อกลุ่มสินค้า (เฉพาะ Gasoline และ Diesel) จาก `int_sales_daily` ที่ join กับ `dim_product` แล้วคำนวณสัดส่วนร้อยละของแต่ละกลุ่มต่อยอดขายเชื้อเพลิงรวมของสถานี
9. **`mart_09_daily_station_ranking`**: รวมยอดขายรายวันต่อสถานีจาก `int_sales_daily` แล้วหาสถานีที่ยอดขายสูงสุดและต่ำสุดในแต่ละวัน พร้อมคำนวณอัตราส่วนระหว่างสองค่านั้น
10. **`mart_10_best_weekday_per_station`**: join `fact_invoice` กับ `dim_date`, หายอดขายเฉลี่ยต่อสถานีต่อวันในสัปดาห์ (ISO weekday) แล้วจัดอันดับวันในสัปดาห์ภายในแต่ละสถานีเพื่อหาวันที่ขายดีที่สุด
11. **`mart_11_dispense_vs_sales_variance`**: `full outer join` ระหว่าง `int_sales_daily` กับ `int_inventory_daily` ด้วย `gasstation_id`, `product_id`, `date_key` เพื่อเทียบปริมาณที่ขายกับปริมาณที่จ่ายออกจากถัง คำนวณส่วนต่าง และตั้งธงวันที่ส่วนต่างเกิน 5%
12. **`mart_12_low_fuel_tanks`**: อ่านระดับน้ำมันคงเหลือปัจจุบันของทุกถังจาก `dim_tank` (`current_quantity` หารด้วย `capacity_liters`) แล้วตั้งธงถังที่ต่ำกว่าเกณฑ์เตือนภัย 20%
13. **`mart_13_staffing_structure`**: นับจำนวนพนักงานต่อสถานีต่อตำแหน่งจาก `dim_employee` แล้วคำนวณสัดส่วนร้อยละของแต่ละตำแหน่งต่อจำนวนพนักงานรวมของสถานี พร้อมระบุตำแหน่งที่มีสัดส่วนมากที่สุด
14. **`mart_14_credit_card_fee_simulation`**: รวมยอดขายรวมและยอดขายที่ชำระด้วยบัตรเครดิตต่อสถานีจาก `fact_invoice` แล้วจำลองต้นทุนค่าธรรมเนียมธุรกรรม 2% จากยอดที่ชำระด้วยบัตรเครดิต
15. **`mart_15_revenue_per_employee`**: รวมยอดขายและจำนวนบิล (จาก `fact_invoice`) เข้ากับจำนวนพนักงานและจำนวนพนักงานเติมน้ำมัน (จาก `dim_employee`) ต่อสถานี เพื่อคำนวณยอดขายต่อพนักงานและจำนวนบิลต่อพนักงานเติมน้ำมัน 1 คน

---

## 11. สรุปภาพรวมทั้งระบบ

ระบบคลังข้อมูลนี้เป็นตัวอย่างของ **Galaxy Schema (Fact Constellation)** ที่มี fact table 3 ตัว (`fact_invoice`, `fact_sales`, `fact_inventory_transaction`) แชร์ conformed dimension ร่วมกัน (`dim_gasstation`, `dim_date`, `dim_hour`, `dim_product`) ข้อมูลไหลผ่านกระบวนการ ELT ตั้งแต่ raw CSV → source ทั้งหมดเป็น VARCHAR → staging (แปลงชนิดข้อมูลเท่าที่จำเป็น) → dimension/fact (คัดข้อมูลซ้ำ + เปลี่ยนชื่อคอลัมน์) → intermediate (พรีคำนวณผลรวม) → mart (ตอบคำถามธุรกิจ 15 ข้อโดยตรง) และปิดท้ายด้วยแดชบอร์ด Streamlit ที่ดึงข้อมูลจากตาราง mart ไปแสดงผลแบบโต้ตอบได้

## การใช้งาน (Getting Started)

### ผ่าน GitHub Codespaces (แนะนำ)
เปิด repo บน GitHub → **Code** → แท็บ **Codespaces** → **Create codespace on main** รอให้ container ติดตั้งไลบรารีลง `.venv`, ติดตั้ง dbt package (`dbt deps`) และโหลดข้อมูลดิบเข้า `dev.duckdb` ให้อัตโนมัติ (ผ่าน `.devcontainer/devcontainer.json`) จากนั้นเปิด terminal แล้วรันคำสั่งได้เลยโดยไม่ต้องตั้งค่าอะไรเพิ่ม:

```
cd Gasstation_dw_duckdb
dbt seed && dbt run && dbt test
cd ..
streamlit run app.py
```

พอร์ต 8501 จะถูก forward ให้อัตโนมัติเมื่อ Streamlit เริ่มทำงาน

### รันในเครื่องตัวเอง (Local)
1. ติดตั้งไลบรารีที่จำเป็น: `pip install -r requirements.txt`
2. เข้าโฟลเดอร์โปรเจกต์ dbt: `cd Gasstation_dw_duckdb`
3. ติดตั้ง dbt package: `dbt deps`
4. โหลดข้อมูลดิบเข้า DuckDB (ครั้งแรกครั้งเดียว หรือเมื่อต้องการรีเฟรชข้อมูลดิบ): `python load_raw.py`
5. รันคลังข้อมูล: `dbt seed && dbt run && dbt test`
6. เปิดแดชบอร์ด (กลับไปที่ root ของ repo ก่อน): `cd .. && streamlit run app.py`
