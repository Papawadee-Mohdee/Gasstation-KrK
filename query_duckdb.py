import os
import duckdb
import pandas as pd

# ตรวจสอบตำแหน่งไฟล์ dev.duckdb อัตโนมัติ
db_path = 'dev.duckdb' if os.path.exists('dev.duckdb') else 'Gasstation_dw_duckdb/dev.duckdb'
conn = duckdb.connect(db_path)

# ดึงรายชื่อตารางทั้งหมดใน main schema
tables = conn.execute(
    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY table_name"
).fetchall()

print(f"Tables in {db_path}:")
for table in tables:
    print(f"  - {table[0]}")

def show_table(table_name, limit=20):
    print("\n" + "=" * 80)
    print(f"Table: {table_name}")
    print("=" * 80)
    try:
        result = conn.execute(f'SELECT * FROM main."{table_name}" LIMIT {limit}').fetchall()
        df = pd.DataFrame(result, columns=[desc[0] for desc in conn.description])
        print(df)
        return df
    except Exception as e:
        print(f"Error reading {table_name}: {e}")

# --- Staging Layer ---
show_table("stg_Customer")
show_table("stg_Employee")
show_table("stg_GasStation")
show_table("stg_Invoice")
show_table("stg_InvoiceDetail")
show_table("stg_Product")
show_table("stg_StorageTank")
show_table("stg_InventoryTransaction")
show_table("stg_TankProductMap")

# --- Dimension & Bridge Tables ---
show_table("dim_date")
show_table("dim_hour")
show_table("dim_customer")
show_table("dim_employee")
show_table("dim_gasstation")
show_table("dim_payment_method")
show_table("dim_vehicle_category")
show_table("dim_product")
show_table("dim_tank")
show_table("bridge_tank_product")

# --- Fact Layer (เตรียมไว้เปิดใช้งานเมื่อสร้างโมเดลแล้ว) ---
# show_table("fact_sales")
# show_table("fact_inventory_transaction")

conn.close()