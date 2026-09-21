"""โหลดไฟล์ CSV ดิบทั้ง 8 ไฟล์เข้า dev.duckdb เป็นตาราง source (ทุกคอลัมน์เป็น VARCHAR)
รันคำสั่งนี้ครั้งเดียวก่อน `dbt seed && dbt run` ในเครื่อง/Codespace ที่ยังไม่เคยมีตารางดิบ
"""
import duckdb

RAW_TABLES = {
    "Customer": "datasets/Customer.csv",
    "Employee": "datasets/Employee.csv",
    "GasStation": "datasets/GasStation.csv",
    "Invoice": "datasets/Invoice.csv",
    "InvoiceDetail": "datasets/InvoiceDetail.csv",
    "Product": "datasets/Product.csv",
    "StorageTank": "datasets/StorageTank.csv",
    "InventoryTransaction": "datasets/InventoryTransaction.csv",
}

conn = duckdb.connect("dev.duckdb")
for table_name, csv_path in RAW_TABLES.items():
    conn.execute(f"""
        CREATE OR REPLACE TABLE main."{table_name}" AS
        SELECT * FROM read_csv_auto('{csv_path}', all_varchar=true)
    """)
    print(f"Loaded {table_name} from {csv_path}")
conn.close()
print("Done. Raw tables are ready for `dbt seed && dbt run`.")
