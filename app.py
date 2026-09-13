"""
PetroNet Analytics — Executive Dashboard
==========================================
Streamlit + DuckDB + Plotly

หลักการสำคัญ: หน้าเว็บนี้ "ห้าม" คำนวณตัวเลขทางธุรกิจเอง (ห้าม SUM/COUNT ยอดขายดิบใน
app.py) ทุก query ดึงจากชั้น dim_* / fact_* / mart_* ที่ dbt สร้างไว้แล้วเท่านั้น
เพื่อให้ตรรกะทางธุรกิจ (การกันยอดคูณซ้ำ, Unknown member, การกรอง has_required_value_error
ฯลฯ) อยู่ที่จุดเดียวคือชั้น warehouse ไม่กระจายไปแก้ในหลายที่

โครงสร้างตารางที่ใช้ (ต้องมีอยู่จริงใน DuckDB ก่อนรันแอปนี้):
  dim_date, dim_hour, dim_gasstation, dim_product, dim_customer, dim_employee,
  dim_payment_method, dim_vehicle_category, dim_tank, bridge_tank_product,
  fact_sales, fact_inventory_transaction,
  mart_01_station_product_daily ... mart_15_reorder_priority

หมายเหตุ: ชื่อคอลัมน์ของ mart อ้างอิงตามที่ออกแบบไว้ในเอกสาร Fact/Mart ที่ต่อยอดจาก
Business Question ทั้ง 15 ข้อ — ถ้าตั้งชื่อคอลัมน์ในโปรเจกต์จริงต่างจากนี้ ให้แก้ที่ค่า
คงที่ในหัวไฟล์ (DB_PATH, SCHEMA) และ query string ของแต่ละฟังก์ชัน load_* เท่านั้น
ไม่ต้องแก้ตรรกะการวาดกราฟ

วิธีรัน:
    pip install -r requirements.txt
    streamlit run app.py
"""

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import date

# ----------------------------------------------------------------------------
# 0) CONFIG — แก้ตรงนี้ที่เดียวถ้า path หรือ schema เปลี่ยน
# ----------------------------------------------------------------------------
DB_PATH = "Gasstation_dw_duckdb/dev.duckdb"   # path ไปยังไฟล์ DuckDB ที่ dbt build ไว้
SCHEMA = "main"                                # schema ที่ dbt สร้างตารางไว้ (ค่า default ของ dbt-duckdb)

PRIMARY = "#12746B"      # เขียวอมฟ้าเข้ม — สีหลักของแบรนด์
PRIMARY_DARK = "#0B3B36"
ACCENT = "#F2A65A"       # ส้มอำพัน — เน้นตัวเลขสำคัญ / คำเตือน
DANGER = "#D9695F"
NEUTRAL_BG = "#F5F7F7"
CARD_BG = "#FFFFFF"

PALETTE = ["#12746B", "#F2A65A", "#4C9A9A", "#D9695F", "#7C93C9",
           "#E8C547", "#8E7CC3", "#5B8C5A", "#C97064", "#3F6B73"]

st.set_page_config(
    page_title="PetroNet Analytics",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# 1) STYLE — ธีมโมเดิร์น
# ----------------------------------------------------------------------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Prompt', 'Tahoma', sans-serif;
}}

.stApp {{
    background-color: {NEUTRAL_BG};
}}

section[data-testid="stSidebar"] {{
    background-color: {PRIMARY_DARK};
}}
section[data-testid="stSidebar"] * {{
    color: #EAF3F1 !important;
}}
section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {{
    background-color: #ffffff10;
    color: #ffffff;
}}

h1, h2, h3 {{
    color: {PRIMARY_DARK};
    font-weight: 600;
}}

.pn-header {{
    padding: 1.1rem 1.6rem;
    background: linear-gradient(120deg, {PRIMARY} 0%, {PRIMARY_DARK} 100%);
    border-radius: 16px;
    color: white;
    margin-bottom: 1.4rem;
    box-shadow: 0 6px 18px rgba(11,59,54,0.18);
}}
.pn-header h1 {{ color: white; margin: 0; font-size: 1.6rem; }}
.pn-header p {{ color: #DCEEEB; margin: 0.2rem 0 0 0; font-size: 0.92rem; }}

.pn-card {{
    background: {CARD_BG};
    border-radius: 14px;
    padding: 1rem 1.2rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    border: 1px solid #E7EEEC;
}}

div[data-testid="stMetric"] {{
    background: {CARD_BG};
    border-radius: 14px;
    padding: 0.9rem 1rem 0.6rem 1rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    border: 1px solid #E7EEEC;
}}
div[data-testid="stMetricLabel"] {{ color: {PRIMARY_DARK}; font-weight: 500; }}
div[data-testid="stMetricValue"] {{ color: {PRIMARY}; }}

.pn-section-title {{
    border-left: 6px solid {ACCENT};
    padding-left: 0.7rem;
    margin: 1.4rem 0 0.4rem 0;
}}
.pn-caption {{
    color: #5C6B69;
    font-size: 0.85rem;
    margin-bottom: 0.6rem;
}}

[data-testid="stExpander"] {{
    background: {CARD_BG};
    border-radius: 12px;
    border: 1px solid #E7EEEC;
}}
</style>
""", unsafe_allow_html=True)

PLOTLY_LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Tahoma, Segoe UI, sans-serif", size=13, color="#2A3A38"),
    colorway=PALETTE,
    margin=dict(l=10, r=10, t=48, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    plot_bgcolor="white",
    paper_bgcolor="white",
)


def style_fig(fig, title=None, height=420):
    fig.update_layout(**PLOTLY_LAYOUT)
    if title:
        fig.update_layout(title=dict(text=title, x=0.01, xanchor="left",
                                      font=dict(size=16, color=PRIMARY_DARK)))
    fig.update_layout(height=height)
    return fig


# ----------------------------------------------------------------------------
# 2) DB CONNECTION
# ----------------------------------------------------------------------------
@st.cache_resource
def get_connection():
    return duckdb.connect(DB_PATH, read_only=True)


@st.cache_data(ttl=600, show_spinner=False)
def run_query(sql: str, params: tuple | None = None) -> pd.DataFrame:
    con = get_connection()
    try:
        if params:
            return con.execute(sql, params).fetchdf()
        return con.execute(sql).fetchdf()
    except duckdb.Error as e:
        st.warning(f"ดึงข้อมูลไม่สำเร็จ (ตรวจว่าตารางถูกสร้างแล้วหรือยัง): {e}")
        return pd.DataFrame()


def T(name: str) -> str:
    """คืนชื่อตารางแบบเต็ม schema.table"""
    return f"{SCHEMA}.{name}"


# ----------------------------------------------------------------------------
# 3) GLOBAL FILTER OPTIONS (มาจาก dim เท่านั้น)
# ----------------------------------------------------------------------------
@st.cache_data(ttl=600, show_spinner=False)
def load_filter_options():
    date_bounds = run_query(f"""
        select min(date_day) as min_d, max(date_day) as max_d
        from {T('dim_date')}
        where date_key <> -1
    """)
    stations = run_query(f"""
        select gasstation_id, gasstation_name
        from {T('dim_gasstation')}
        where coalesce(is_unknown_member, false) = false
        order by gasstation_name
    """)
    return date_bounds, stations


date_bounds_df, stations_df = load_filter_options()

if date_bounds_df.empty or pd.isna(date_bounds_df.loc[0, "min_d"]):
    MIN_DATE, MAX_DATE = date(2024, 3, 15), date(2024, 4, 7)
else:
    MIN_DATE = pd.to_datetime(date_bounds_df.loc[0, "min_d"]).date()
    MAX_DATE = pd.to_datetime(date_bounds_df.loc[0, "max_d"]).date()

STATION_OPTIONS = dict(zip(stations_df.get("gasstation_id", []),
                            stations_df.get("gasstation_name", [])))

# ----------------------------------------------------------------------------
# 4) SIDEBAR — เมนู + ตัวกรองส่วนกลาง
# ----------------------------------------------------------------------------
st.sidebar.markdown("## ⛽ PetroNet Analytics")
st.sidebar.caption("แดชบอร์ดสำหรับผู้บริหาร — ข้อมูลจากชั้น dim / fact / mart เท่านั้น")

PAGES = [
    "ภาพรวมผู้บริหาร",
    "1) ยอดขายและความต้องการ",
    "2) การชำระเงินและลูกค้าหลัก",
    "3) พฤติกรรมและการปฏิบัติงาน",
    "4) รูปแบบการซื้อและสต็อก",
    "5) การเติมและกระทบยอดน้ำมัน",
]
page = st.sidebar.radio("เลือกหมวดคำถาม", PAGES, index=0)

st.sidebar.markdown("---")
st.sidebar.markdown("#### ตัวกรองข้อมูล")
date_range = st.sidebar.date_input(
    "ช่วงวันที่", value=(MIN_DATE, MAX_DATE), min_value=MIN_DATE, max_value=MAX_DATE
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = MIN_DATE, MAX_DATE

selected_station_names = st.sidebar.multiselect(
    "สถานีบริการ", options=list(STATION_OPTIONS.values()),
    default=list(STATION_OPTIONS.values()),
)
selected_station_ids = [k for k, v in STATION_OPTIONS.items() if v in selected_station_names]

st.sidebar.caption(
    "ช่วงข้อมูลต้นทาง: 15 มี.ค.–7 เม.ย. 2024 (ไม่ครบเดือน) "
    "การเปรียบเทียบยอดรวมรายเดือนควรระวังตามที่ระบุใน dim_date.is_complete_day"
)


def station_filter_sql(alias="gasstation_id"):
    """สร้างเงื่อนไข IN สำหรับสถานีที่เลือก (รายการมาจาก dim เอง ไม่ใช่ข้อความอิสระจากผู้ใช้)"""
    if not selected_station_ids:
        return "1 = 0"
    ids = ", ".join(f"'{sid}'" for sid in selected_station_ids)
    return f"{alias} in ({ids})"


DATE_PARAMS = (start_date, end_date)

# ----------------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------------
st.markdown(f"""
<div class="pn-header">
    <h1>PetroNet Analytics — {page}</h1>
    <p>ข้อมูล {start_date.strftime('%d %b %Y')} – {end_date.strftime('%d %b %Y')} ·
       {len(selected_station_ids)} สถานีที่เลือก</p>
</div>
""", unsafe_allow_html=True)


def section_title(text, caption=None):
    st.markdown(f'<div class="pn-section-title"><h3>{text}</h3></div>', unsafe_allow_html=True)
    if caption:
        st.markdown(f'<p class="pn-caption">{caption}</p>', unsafe_allow_html=True)


def empty_state(name):
    st.info(f"ยังไม่มีข้อมูลสำหรับ '{name}' ในช่วง/สถานีที่เลือก หรือยังไม่ได้ build ตารางนี้")


# ==============================================================================
# PAGE: ภาพรวมผู้บริหาร (KPI + แนวโน้มรวม)
# ==============================================================================
if page == "ภาพรวมผู้บริหาร":

    kpi = run_query(f"""
        select
            sum(total_price)                         as total_sales,
            sum(quantity_sold)                        as total_qty,
            count(distinct invoice_id)                as total_bills,
            count(distinct gasstation_id)              as total_stations
        from {T('fact_sales')}
        join {T('dim_date')} d on {T('fact_sales')}.date_key = d.date_key
        where d.date_day between ? and ?
          and {station_filter_sql(f"{T('fact_sales')}.gasstation_id")}
    """, DATE_PARAMS)

    c1, c2, c3, c4 = st.columns(4)
    if not kpi.empty:
        row = kpi.iloc[0]
        c1.metric("ยอดขายรวม (บาท)", f"{row['total_sales']:,.0f}" if pd.notna(row['total_sales']) else "—")
        c2.metric("ปริมาณขายรวม (ลิตร)", f"{row['total_qty']:,.0f}" if pd.notna(row['total_qty']) else "—")
        c3.metric("จำนวนบิล", f"{row['total_bills']:,.0f}" if pd.notna(row['total_bills']) else "—")
        c4.metric("สถานีที่มีข้อมูล", f"{row['total_stations']:,.0f}" if pd.notna(row['total_stations']) else "—")
    else:
        empty_state("KPI ภาพรวม")

    col1, col2 = st.columns([1.4, 1])

    with col1:
        section_title("แนวโน้มยอดขายรายวัน", "รวมทุกสถานีที่เลือก เทียบปริมาณขาย (เส้น) กับยอดขาย (แท่ง)")
        trend = run_query(f"""
            select d.date_day,
                   sum(f.total_price)  as sales_amount,
                   sum(f.quantity_sold) as quantity_sold
            from {T('fact_sales')} f
            join {T('dim_date')} d on f.date_key = d.date_key
            where d.date_day between ? and ?
              and {station_filter_sql('f.gasstation_id')}
            group by d.date_day
            order by d.date_day
        """, DATE_PARAMS)
        if not trend.empty:
            fig = go.Figure()
            fig.add_bar(x=trend["date_day"], y=trend["sales_amount"], name="ยอดขาย (บาท)",
                        marker_color=PRIMARY, opacity=0.85)
            fig.add_scatter(x=trend["date_day"], y=trend["quantity_sold"], name="ปริมาณขาย (ลิตร)",
                             yaxis="y2", mode="lines+markers", line=dict(color=ACCENT, width=3))
            fig.update_layout(yaxis=dict(title="บาท"), yaxis2=dict(title="ลิตร", overlaying="y", side="right"))
            st.plotly_chart(style_fig(fig), use_container_width=True)
        else:
            empty_state("แนวโน้มยอดขายรายวัน")

    with col2:
        section_title("สัดส่วนยอดขายตามสถานี", "รวมทั้งช่วงที่เลือก")
        by_station = run_query(f"""
            select g.gasstation_name, sum(f.total_price) as sales_amount
            from {T('fact_sales')} f
            join {T('dim_date')} d on f.date_key = d.date_key
            join {T('dim_gasstation')} g on f.gasstation_id = g.gasstation_id
            where d.date_day between ? and ?
              and {station_filter_sql('f.gasstation_id')}
            group by g.gasstation_name
            order by sales_amount desc
        """, DATE_PARAMS)
        if not by_station.empty:
            fig = px.pie(by_station, names="gasstation_name", values="sales_amount", hole=0.55,
                         color_discrete_sequence=PALETTE)
            fig.update_traces(textinfo="percent+label")
            st.plotly_chart(style_fig(fig, height=420), use_container_width=True)
        else:
            empty_state("สัดส่วนยอดขายตามสถานี")

    section_title("อันดับสถานีตามยอดขายและกำไรขั้นต้นโดยประมาณ (จำนวนบิล x ยอดขายเฉลี่ย)")
    rank = run_query(f"""
        select g.gasstation_name,
               sum(f.total_price) as sales_amount,
               count(distinct f.invoice_id) as bill_count
        from {T('fact_sales')} f
        join {T('dim_date')} d on f.date_key = d.date_key
        join {T('dim_gasstation')} g on f.gasstation_id = g.gasstation_id
        where d.date_day between ? and ?
          and {station_filter_sql('f.gasstation_id')}
        group by g.gasstation_name
        order by sales_amount desc
    """, DATE_PARAMS)
    if not rank.empty:
        fig = px.bar(rank, x="sales_amount", y="gasstation_name", orientation="h",
                     color="bill_count", color_continuous_scale=[PRIMARY, ACCENT],
                     labels={"sales_amount": "ยอดขาย (บาท)", "gasstation_name": "",
                             "bill_count": "จำนวนบิล"})
        fig.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(style_fig(fig, height=max(320, 40 * len(rank))), use_container_width=True)
    else:
        empty_state("อันดับสถานี")


# ==============================================================================
# PAGE 1: ยอดขายและความต้องการ (Q1–Q3)  →  mart_01, mart_02, mart_03
# ==============================================================================
elif page == "1) ยอดขายและความต้องการ":

    section_title("Q1 · สถานีใดสร้างยอดขายสูงสุดในแต่ละวัน และมาจากน้ำมันชนิดใดเป็นหลัก?",
                   "grain: สถานี × ชนิดน้ำมัน × วัน — เลือกดูวันใดวันหนึ่งเพื่อดูสัดส่วนภายในสถานี")
    q1 = run_query(f"""
        select m.date_day, g.gasstation_name, p.product_name, p.is_fuel,
               m.sales_amount, m.quantity_sold, m.pct_of_station_day
        from {T('mart_01_station_product_daily')} m
        join {T('dim_gasstation')} g on m.gasstation_id = g.gasstation_id
        join {T('dim_product')} p on m.product_id = p.product_id
        where m.date_day between ? and ?
          and {station_filter_sql('m.gasstation_id')}
    """, DATE_PARAMS)
    if not q1.empty:
        c1, c2 = st.columns([1.3, 1])
        with c1:
            daily_top = q1.groupby(["date_day", "gasstation_name"], as_index=False)["sales_amount"].sum()
            fig = px.bar(daily_top, x="date_day", y="sales_amount", color="gasstation_name",
                         barmode="group", labels={"sales_amount": "ยอดขาย (บาท)", "date_day": ""})
            st.plotly_chart(style_fig(fig, "ยอดขายรายวันต่อสถานี (สถานีแท่งสูงสุด = ผู้นำวันนั้น)"),
                             use_container_width=True)
        with c2:
            pick_day = st.selectbox("เลือกวันที่ดูสัดส่วนน้ำมัน", sorted(q1["date_day"].unique()),
                                     index=len(q1["date_day"].unique()) - 1)
            fuel_share = q1[(q1["date_day"] == pick_day) & (q1["is_fuel"] == True)]  # noqa: E712
            fig2 = px.treemap(fuel_share, path=["gasstation_name", "product_name"], values="sales_amount",
                               color="pct_of_station_day", color_continuous_scale=[NEUTRAL_BG, PRIMARY])
            st.plotly_chart(style_fig(fig2, "สัดส่วนยอดขายน้ำมันในแต่ละสถานี (วันที่เลือก)"),
                             use_container_width=True)
    else:
        empty_state("mart_01_station_product_daily")

    section_title("Q2 · แต่ละสถานีขายหนาแน่นช่วงเวลาใด เมื่อแยกวันในสัปดาห์และชนิดน้ำมัน?",
                   "grain: สถานี × ชั่วโมง × วันในสัปดาห์ × ชนิดน้ำมัน — heatmap อ่านง่ายสำหรับวางแผนกำลังคน/เติมน้ำมัน")
    q2 = run_query(f"""
        select m.gasstation_name, m.hour_of_day, m.weekday_name, m.iso_weekday,
               sum(m.bill_count) as bill_count
        from {T('mart_02_hourly_demand')} m
        where {station_filter_sql('m.gasstation_id')}
        group by m.gasstation_name, m.hour_of_day, m.weekday_name, m.iso_weekday
    """)
    if not q2.empty:
        station_pick = st.selectbox("เลือกสถานีดู heatmap", sorted(q2["gasstation_name"].unique()))
        heat = q2[q2["gasstation_name"] == station_pick].sort_values("iso_weekday")
        pivot = heat.pivot_table(index="weekday_name", columns="hour_of_day", values="bill_count",
                                  aggfunc="sum").reindex(heat.sort_values("iso_weekday")["weekday_name"].unique())
        fig = px.imshow(pivot, color_continuous_scale=[NEUTRAL_BG, PRIMARY, PRIMARY_DARK],
                         labels=dict(x="ชั่วโมง", y="วันในสัปดาห์", color="จำนวนบิล"), aspect="auto")
        st.plotly_chart(style_fig(fig, f"ความหนาแน่นการขาย — {station_pick}", height=380),
                         use_container_width=True)
    else:
        empty_state("mart_02_hourly_demand")

    section_title("Q3 · ลูกค้าแต่ละประเภทรถนิยมซื้อน้ำมันชนิดใด และรูปแบบต่างกันระหว่างสถานีอย่างไร?",
                   "grain: ประเภทรถ × ชนิดน้ำมัน × สถานี")
    q3 = run_query(f"""
        select m.vehicle_category, m.product_name, m.gasstation_name,
               m.quantity_sold, m.bill_count, m.avg_qty_per_bill
        from {T('mart_03_vehicle_fuel_station')} m
        where {station_filter_sql('m.gasstation_id')}
    """)
    if not q3.empty:
        fig = px.bar(q3, x="vehicle_category", y="quantity_sold", color="product_name",
                     facet_col="gasstation_name", facet_col_wrap=3,
                     labels={"quantity_sold": "ปริมาณขาย (ลิตร)", "vehicle_category": "ประเภทรถ"})
        fig.update_xaxes(tickangle=-30)
        st.plotly_chart(style_fig(fig, height=460), use_container_width=True)
    else:
        empty_state("mart_03_vehicle_fuel_station")


# ==============================================================================
# PAGE 2: การชำระเงินและลูกค้าหลัก (Q4–Q6)  →  mart_04, mart_05, mart_06
# ==============================================================================
elif page == "2) การชำระเงินและลูกค้าหลัก":

    section_title("Q4 · วิธีชำระเงินสัมพันธ์กับมูลค่าการซื้ออย่างไร?",
                   "grain: วิธีชำระเงิน × ประเภทรถ × สถานี × ช่วงเวลา")
    q4 = run_query(f"""
        select payment_method_label, vehicle_category, day_part,
               bill_count, avg_sales_per_bill, pct_bills_by_method
        from {T('mart_04_payment_value')}
        where {station_filter_sql('gasstation_id')}
    """)
    if not q4.empty:
        c1, c2 = st.columns(2)
        with c1:
            share = q4.groupby("payment_method_label", as_index=False)["bill_count"].sum()
            fig = px.pie(share, names="payment_method_label", values="bill_count", hole=0.5,
                         color_discrete_sequence=PALETTE)
            st.plotly_chart(style_fig(fig, "สัดส่วนจำนวนบิลตามวิธีชำระเงิน"), use_container_width=True)
        with c2:
            fig2 = px.box(q4, x="payment_method_label", y="avg_sales_per_bill", color="vehicle_category",
                          labels={"avg_sales_per_bill": "ยอดขายเฉลี่ยต่อบิล (บาท)", "payment_method_label": ""})
            st.plotly_chart(style_fig(fig2, "การกระจายมูลค่าเฉลี่ยต่อบิล ตามวิธีชำระ x ประเภทรถ"),
                             use_container_width=True)
    else:
        empty_state("mart_04_payment_value")

    section_title("Q5 · ลูกค้า Top 10 ของแต่ละสถานีใช้รถประเภทใด ซื้อน้ำมันชนิดใดเป็นหลัก?",
                   "grain: ลูกค้า × ประเภทรถ × สถานี × ชนิดน้ำมัน")
    q5 = run_query(f"""
        select gasstation_name, customer_name, vehicle_category, product_name,
               customer_sales, bill_count, pct_from_top10, rank_in_station
        from {T('mart_05_top10_customers')}
        where {station_filter_sql('gasstation_id')}
    """)
    if not q5.empty:
        station_pick5 = st.selectbox("เลือกสถานี", sorted(q5["gasstation_name"].unique()), key="q5_station")
        top10 = q5[q5["gasstation_name"] == station_pick5].sort_values("rank_in_station")
        fig = px.bar(top10, x="customer_sales", y="customer_name", color="vehicle_category",
                     orientation="h", hover_data=["product_name", "bill_count", "pct_from_top10"],
                     labels={"customer_sales": "ยอดขายสะสม (บาท)", "customer_name": ""})
        fig.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(style_fig(fig, f"ลูกค้า Top 10 — {station_pick5}", height=440),
                         use_container_width=True)
    else:
        empty_state("mart_05_top10_customers")

    section_title("Q6 · ลูกค้ารถแต่ละประเภทกลับมาซื้อซ้ำที่สถานีเดิมมากน้อยเพียงใด?",
                   "grain: ประเภทรถ × สถานี — อัตราซื้อซ้ำ = ลูกค้าซื้อซ้ำ ÷ ลูกค้าทั้งหมดในกลุ่ม")
    q6 = run_query(f"""
        select gasstation_name, vehicle_category, total_customers, repeat_customers,
               repeat_rate, avg_purchase_days_per_customer
        from {T('mart_06_repeat_purchase')}
        where {station_filter_sql('gasstation_id')}
    """)
    if not q6.empty:
        fig = px.bar(q6, x="gasstation_name", y="repeat_rate", color="vehicle_category", barmode="group",
                     text_auto=".0%", labels={"repeat_rate": "อัตราซื้อซ้ำ", "gasstation_name": ""})
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(style_fig(fig, "อัตราซื้อซ้ำตามประเภทรถและสถานี"), use_container_width=True)
    else:
        empty_state("mart_06_repeat_purchase")


# ==============================================================================
# PAGE 3: พฤติกรรมและการปฏิบัติงาน (Q7–Q9)  →  mart_07, mart_08, mart_09
# ==============================================================================
elif page == "3) พฤติกรรมและการปฏิบัติงาน":

    section_title("Q7 · ลูกค้ากลุ่มใดใช้บริการหลายสถานี และยอดขายกระจายอย่างไร?",
                   "grain: ลูกค้า × สถานี × ชนิดน้ำมัน — วงกลมใหญ่ = ลูกค้าที่ใช้หลายสถานี")
    q7 = run_query(f"""
        select customer_name, vehicle_category, gasstation_name, product_name,
               station_count, sales_amount, pct_of_customer_sales, is_multi_station
        from {T('mart_07_multi_station_customers')}
        where {station_filter_sql('gasstation_id')}
    """)
    if not q7.empty:
        multi = q7[q7["is_multi_station"] == True]  # noqa: E712
        if not multi.empty:
            fig = px.sunburst(multi, path=["customer_name", "gasstation_name"], values="sales_amount",
                               color="station_count", color_continuous_scale=[PRIMARY, ACCENT])
            st.plotly_chart(style_fig(fig, "ลูกค้าที่ใช้บริการหลายสถานี และการกระจายยอดขาย", height=520),
                             use_container_width=True)
        else:
            st.info("ไม่พบลูกค้าที่ใช้บริการมากกว่า 1 สถานีในช่วง/สถานีที่เลือก")
    else:
        empty_state("mart_07_multi_station_customers")

    section_title("Q8 · พนักงานและตำแหน่งมีปริมาณรายการขายต่างกันอย่างไร ตามสถานี วัน ช่วงเวลา?",
                   "grain: พนักงาน × ตำแหน่ง × สถานี × วัน/ชั่วโมง — ใช้วางแผนกำลังคน")
    q8 = run_query(f"""
        select employee_name, position, gasstation_name, date_day, hour_of_day,
               bill_count, sales_amount
        from {T('mart_08_employee_workload')}
        where date_day between ? and ?
          and {station_filter_sql('gasstation_id')}
    """, DATE_PARAMS)
    if not q8.empty:
        by_emp = q8.groupby(["employee_name", "position"], as_index=False).agg(
            bill_count=("bill_count", "sum"), sales_amount=("sales_amount", "sum"))
        fig = px.bar(by_emp.sort_values("bill_count", ascending=True), x="bill_count", y="employee_name",
                     color="position", orientation="h",
                     labels={"bill_count": "จำนวนบิลที่บันทึก", "employee_name": ""})
        st.plotly_chart(style_fig(fig, "ปริมาณงานต่อพนักงาน (รวมช่วงที่เลือก)",
                                   height=max(320, 28 * len(by_emp))), use_container_width=True)

        heat8 = q8.groupby(["gasstation_name", "hour_of_day"], as_index=False)["bill_count"].sum()
        pivot8 = heat8.pivot_table(index="gasstation_name", columns="hour_of_day", values="bill_count",
                                    aggfunc="sum")
        fig2 = px.imshow(pivot8, color_continuous_scale=[NEUTRAL_BG, PRIMARY, PRIMARY_DARK],
                          labels=dict(x="ชั่วโมง", y="สถานี", color="จำนวนบิล"), aspect="auto")
        st.plotly_chart(style_fig(fig2, "ช่วงเวลาที่มีรายการขายหนาแน่น ตามสถานี", height=340),
                         use_container_width=True)
    else:
        empty_state("mart_08_employee_workload")

    section_title("Q9 · ยอดขายแต่ละสถานีเพิ่ม/ลดจากวันเดียวกันสัปดาห์ก่อนเท่าใด?",
                   "grain: สถานี × ชนิดน้ำมัน × วัน — เทียบ 7 วันก่อนหน้า")
    q9 = run_query(f"""
        select gasstation_name, product_name, date_day, weekday_name,
               sales_amount, sales_amount_prior_week, sales_diff, pct_change
        from {T('mart_09_wow_change')}
        where date_day between ? and ?
          and {station_filter_sql('gasstation_id')}
    """, DATE_PARAMS)
    if not q9.empty:
        agg9 = q9.groupby(["gasstation_name", "date_day"], as_index=False)["sales_diff"].sum()
        fig = px.bar(agg9, x="date_day", y="sales_diff", color="gasstation_name", barmode="group",
                     labels={"sales_diff": "ผลต่างยอดขาย เทียบสัปดาห์ก่อน (บาท)", "date_day": ""})
        fig.add_hline(y=0, line_color="#999999", line_width=1)
        st.plotly_chart(style_fig(fig, "การเปลี่ยนแปลงยอดขาย Week-over-Week"), use_container_width=True)
    else:
        empty_state("mart_09_wow_change")


# ==============================================================================
# PAGE 4: รูปแบบการซื้อและสต็อก (Q10–Q12)  →  mart_10, mart_11, mart_12
# ==============================================================================
elif page == "4) รูปแบบการซื้อและสต็อก":

    section_title("Q10 · คู่สินค้าใดถูกซื้อร่วมกันบ่อยที่สุดในบิลเดียว?",
                   "grain: คู่สินค้า × ประเภทรถ × สถานี")
    q10 = run_query(f"""
        select gasstation_name, vehicle_category, product_name_a, product_name_b,
               bill_count_with_pair, pct_of_group_bills, avg_bill_value
        from {T('mart_10_product_affinity')}
        where {station_filter_sql('gasstation_id')}
        order by bill_count_with_pair desc
        limit 300
    """)
    if not q10.empty:
        station_pick10 = st.selectbox("เลือกสถานี", sorted(q10["gasstation_name"].unique()), key="q10_station")
        sub10 = q10[q10["gasstation_name"] == station_pick10]
        pivot10 = sub10.pivot_table(index="product_name_a", columns="product_name_b",
                                     values="bill_count_with_pair", aggfunc="sum", fill_value=0)
        fig = px.imshow(pivot10, color_continuous_scale=[NEUTRAL_BG, PRIMARY, PRIMARY_DARK],
                         labels=dict(color="จำนวนบิลที่พบคู่นี้"), aspect="auto")
        st.plotly_chart(style_fig(fig, f"เมทริกซ์คู่สินค้าที่ซื้อร่วมกัน — {station_pick10}", height=420),
                         use_container_width=True)
    else:
        empty_state("mart_10_product_affinity")

    section_title("Q11 · สถานีและชนิดน้ำมันใดมีปริมาณรับเข้าไม่สมดุลกับจ่ายออก?",
                   "grain: สถานี × ถัง × ชนิดน้ำมัน × วัน")
    q11 = run_query(f"""
        select gasstation_name, product_name, date_day, quantity_in, quantity_out, imbalance
        from {T('mart_11_inventory_imbalance')}
        where date_day between ? and ?
          and {station_filter_sql('gasstation_id')}
    """, DATE_PARAMS)
    if not q11.empty:
        agg11 = q11.groupby(["gasstation_name", "date_day"], as_index=False)["imbalance"].sum()
        fig = px.line(agg11, x="date_day", y="imbalance", color="gasstation_name", markers=True,
                      labels={"imbalance": "ปริมาณรับเข้า − จ่ายออก (ลิตร)", "date_day": ""})
        fig.add_hline(y=0, line_color="#999999", line_width=1)
        st.plotly_chart(style_fig(fig, "ความไม่สมดุลของปริมาณรับเข้า/จ่ายออกรายวัน"), use_container_width=True)
    else:
        empty_state("mart_11_inventory_imbalance")

    section_title("Q12 · ถังของสถานีใดมีระดับน้ำมันต่ำกว่าเกณฑ์บ่อยที่สุด?",
                   "grain: สถานี × ถัง × ชนิดน้ำมัน × วัน/ชั่วโมง — เกณฑ์ต่ำกว่า 20% ของความจุ (ปรับได้)")
    q12 = run_query(f"""
        select gasstation_name, product_name, date_day, hour_of_day,
               pct_remaining, is_below_threshold
        from {T('mart_12_low_fuel_frequency')}
        where date_day between ? and ?
          and {station_filter_sql('gasstation_id')}
    """, DATE_PARAMS)
    if not q12.empty:
        low_count = (q12[q12["is_below_threshold"] == True]  # noqa: E712
                     .groupby(["gasstation_name", "product_name"], as_index=False)
                     .size().rename(columns={"size": "low_hours_count"}))
        fig = px.bar(low_count.sort_values("low_hours_count", ascending=True),
                     x="low_hours_count", y="gasstation_name", color="product_name", orientation="h",
                     labels={"low_hours_count": "จำนวนช่วงชั่วโมงที่ต่ำกว่าเกณฑ์", "gasstation_name": ""})
        st.plotly_chart(style_fig(fig, "ความถี่ที่ระดับน้ำมันต่ำกว่าเกณฑ์", height=420),
                         use_container_width=True)
    else:
        empty_state("mart_12_low_fuel_frequency")


# ==============================================================================
# PAGE 5: การเติมและกระทบยอดน้ำมัน (Q13–Q15)  →  mart_13, mart_14, mart_15
# ==============================================================================
elif page == "5) การเติมและกระทบยอดน้ำมัน":

    section_title("Q13 · การเติมน้ำมันแต่ละครั้งมีขนาดและความถี่เหมาะสมกับความจุถังเพียงใด?",
                   "grain: สถานี × ถัง/ความจุ × ชนิดน้ำมัน × วัน")
    q13 = run_query(f"""
        select gasstation_name, product_name, capacity_liters, date_day,
               refill_count, avg_qty_per_refill, pct_refill_of_capacity, quantity_out_per_day
        from {T('mart_13_refill_pattern')}
        where date_day between ? and ?
          and {station_filter_sql('gasstation_id')}
    """, DATE_PARAMS)
    if not q13.empty:
        fig = px.scatter(q13, x="avg_qty_per_refill", y="quantity_out_per_day", size="refill_count",
                          color="gasstation_name", hover_data=["product_name", "capacity_liters"],
                          labels={"avg_qty_per_refill": "ปริมาณเฉลี่ยต่อการเติม (ลิตร)",
                                  "quantity_out_per_day": "ปริมาณจ่ายออกต่อวัน (ลิตร)"})
        st.plotly_chart(style_fig(fig, "ขนาดการเติมเทียบอัตราการใช้ (ฟองใหญ่ = เติมบ่อย)"),
                         use_container_width=True)
    else:
        empty_state("mart_13_refill_pattern")

    section_title("Q14 · ปริมาณขายตามใบเสร็จตรงกับปริมาณจ่ายออกจากถังหรือไม่?",
                   "grain: สถานี × ชนิดน้ำมัน × วัน — ส่วนต่าง = ปริมาณขาย − ปริมาณจ่ายออก")
    q14 = run_query(f"""
        select gasstation_name, product_name, date_day, quantity_sold, quantity_out, diff, pct_diff
        from {T('mart_14_sales_dispense_reconciliation')}
        where date_day between ? and ?
          and {station_filter_sql('gasstation_id')}
    """, DATE_PARAMS)
    if not q14.empty:
        agg14 = q14.groupby(["gasstation_name", "date_day"], as_index=False)["diff"].sum()
        fig = px.bar(agg14, x="date_day", y="diff", color="gasstation_name", barmode="group",
                     labels={"diff": "ส่วนต่าง ขาย − จ่ายออก (ลิตร)", "date_day": ""})
        fig.add_hline(y=0, line_color="#999999", line_width=1)
        st.plotly_chart(style_fig(fig, "ส่วนต่างที่ควรตรวจสอบ (ไม่ใช่ข้อสรุปว่าสูญหาย)"),
                         use_container_width=True)
    else:
        empty_state("mart_14_sales_dispense_reconciliation")

    section_title("Q15 · สถานีและน้ำมันชนิดใดควรได้รับการเติมก่อน?",
                   "grain: สถานี × ถัง × ชนิดน้ำมัน — ประมาณจากยอดคงเหลือล่าสุด ÷ อัตราขายเฉลี่ย 7 วัน")
    q15 = run_query(f"""
        select gasstation_name, product_name, latest_remaining_quantity,
               avg_daily_sales_qty_7d, estimated_days_to_stockout
        from {T('mart_15_reorder_priority')}
        where {station_filter_sql('gasstation_id')}
    """)
    if not q15.empty:
        ranked15 = q15.dropna(subset=["estimated_days_to_stockout"]).sort_values("estimated_days_to_stockout")
        fig = px.bar(ranked15, x="estimated_days_to_stockout", y="gasstation_name", color="product_name",
                     orientation="h",
                     labels={"estimated_days_to_stockout": "จำนวนวันที่คาดว่าจะขายได้ก่อนหมด",
                             "gasstation_name": ""})
        fig.add_vline(x=3, line_dash="dash", line_color=DANGER,
                      annotation_text="เตือนเติมด่วน (< 3 วัน)", annotation_position="top")
        st.plotly_chart(style_fig(fig, "ลำดับความสำคัญในการเติมน้ำมัน (น้อยสุด = เร่งด่วนสุด)",
                                   height=max(340, 30 * len(ranked15))), use_container_width=True)

        no_estimate = q15[q15["estimated_days_to_stockout"].isna()]
        if not no_estimate.empty:
            st.caption(
                f"มี {len(no_estimate)} รายการที่อัตราขายเฉลี่ยเป็นศูนย์ในช่วง 7 วันย้อนหลัง "
                "จึงไม่สามารถประมาณจำนวนวันด้วยสูตรนี้ได้ (ไม่ได้แปลว่าไม่ต้องเติม)"
            )
    else:
        empty_state("mart_15_reorder_priority")

st.markdown("---")
st.caption(
    "PetroNet Analytics · ข้อมูลทั้งหมดคำนวณไว้ล่วงหน้าในชั้น dim/fact/mart (dbt + DuckDB) "
    "แดชบอร์ดนี้ทำหน้าที่ query และแสดงผลเท่านั้น ไม่มีการคำนวณตัวเลขธุรกิจซ้ำในแอป"
)