import duckdb
TABLES = ["dim_date","dim_hour","dim_customer","dim_employee","dim_gasstation",
"dim_product","dim_payment_method","dim_vehicle_category","dim_tank","bridge_tank_product",
"fact_sales","fact_invoice","fact_inventory_transaction","int_sales_daily","int_inventory_daily",
"mart_01_station_product_daily","mart_02_hourly_demand","mart_03_vehicle_fuel_station",
"mart_04_payment_value","mart_05_top10_customers","mart_06_repeat_purchase",
"mart_07_multi_station_customers","mart_08_employee_workload","mart_09_wow_change",
"mart_10_product_affinity","mart_11_inventory_imbalance","mart_12_low_fuel_frequency",
"mart_13_refill_pattern","mart_14_sales_dispense_reconciliation","mart_15_reorder_priority"]
con = duckdb.connect("dev.duckdb", read_only=True)
for t in TABLES:
    cols = con.execute("select column_name, data_type from duckdb_columns() where table_name = ? order by column_index", [t]).fetchall()
    if not cols:
        print(f"[MISSING] {t}"); continue
    n = con.execute(f'select count(*) from "{t}"').fetchone()[0]
    print(f"\n### {t}  ({n:,} rows)")
    print("   " + ", ".join(f"{c}:{d}" for c, d in cols))
print("\n=== sample values ===")
for sql in ["select hour_of_day from fact_sales limit 3",
            "select hour_of_day from fact_inventory_transaction limit 3",
            "select hour_of_day, day_part from dim_hour limit 3",
            "select date_day from dim_date limit 2"]:
    try: print(f"  {sql} -> {con.execute(sql).fetchall()}")
    except Exception as e: print(f"  {sql} -> ERROR {e}")
