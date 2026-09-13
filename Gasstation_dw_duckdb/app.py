"""
app.py — Fuel Station Analytics Dashboard  (v2 · ต่อกับ dbt warehouse จริง)
==========================================================================
อ่านข้อมูลจาก dev.duckdb ที่สร้างโดย dbt เท่านั้น
ใช้เฉพาะตาราง Dimension / Fact / Intermediate / Mart ไม่แตะ stg_* หรือ ref_*

รัน:
    streamlit run app.py

ถ้าไฟล์ฐานข้อมูลอยู่ที่อื่น ตั้งค่าผ่าน environment variable ได้:
    GAS_DW_PATH=/path/to/dev.duckdb streamlit run app.py
"""

from __future__ import annotations

import os

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# 1) การตั้งค่า — แก้ตรงนี้จุดเดียวถ้าชื่อตารางเปลี่ยน
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("GAS_DW_PATH", os.path.join(HERE, "dev.duckdb"))

T = {
    "mart_01": "mart_01_station_product_daily",
    "mart_02": "mart_02_hourly_demand",
    "mart_03": "mart_03_vehicle_fuel_station",
    "mart_04": "mart_04_payment_value",
    "mart_05": "mart_05_top10_customers",
    "mart_06": "mart_06_repeat_purchase",
    "mart_07": "mart_07_multi_station_customers",
    "mart_08": "mart_08_employee_workload",
    "mart_09": "mart_09_wow_change",
    "mart_10": "mart_10_product_affinity",
    "mart_11": "mart_11_inventory_imbalance",
    "mart_12": "mart_12_low_fuel_frequency",
    "mart_13": "mart_13_refill_pattern",
    "mart_14": "mart_14_sales_dispense_reconciliation",
    "mart_15": "mart_15_reorder_priority",
}

# schema จริงเก็บ hour_of_day เป็น TIMESTAMP และ date_day เป็น TIMESTAMP
HOUR = "extract(hour from {c})::int"
DAY = "cast({c} as date)"

# ---------------------------------------------------------------------------
# 2) ธีมสี (น้ำเงินเข้ม + ขาว)
# ---------------------------------------------------------------------------
NAVY_950, NAVY_900, NAVY_800, NAVY_700 = "#050D1F", "#0A1730", "#0E2244", "#16325F"
LINE = "rgba(255,255,255,0.09)"
INK, MUTED = "#EAF1FB", "#9CB3D1"
BLUE, SKY, CYAN = "#3B82F6", "#60A5FA", "#22D3EE"
GOLD, GREEN, RED, VIOLET = "#F5B942", "#34D399", "#F87171", "#A78BFA"
PALETTE = [BLUE, CYAN, SKY, VIOLET, GOLD, GREEN, RED, "#94A3B8"]
BLUE_SCALE = [[0.0, "#0E2244"], [0.35, "#1D4ED8"], [0.7, "#3B82F6"], [1.0, "#7DD3FC"]]

WEEKDAY_TH = {"Monday": "จันทร์", "Tuesday": "อังคาร", "Wednesday": "พุธ",
              "Thursday": "พฤหัสบดี", "Friday": "ศุกร์", "Saturday": "เสาร์",
              "Sunday": "อาทิตย์"}
WEEKDAY_ORDER = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
DAYPART_ORDER = ["เช้า", "เที่ยง", "บ่าย", "เย็น", "กลางคืน"]

st.set_page_config(page_title="Fuel Station Analytics", page_icon="⛽",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown(f"""
<style>
  .stApp {{
      background:
        radial-gradient(1100px 600px at 12% -12%, #123262 0%, rgba(18,50,98,0) 58%),
        radial-gradient(900px 520px at 92% 0%, #0F2E5C 0%, rgba(15,46,92,0) 55%), {NAVY_950};
      color: {INK};
  }}
  [data-testid="stSidebar"] {{
      background: linear-gradient(180deg, {NAVY_900} 0%, {NAVY_950} 100%);
      border-right: 1px solid {LINE};
  }}
  [data-testid="stHeader"] {{ background: transparent; }}
  .block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1500px; }}
  h1,h2,h3,h4 {{ color:#fff; letter-spacing:.2px; }}
  .hero {{
      background: linear-gradient(120deg, {NAVY_800} 0%, {NAVY_700} 55%, #1E4B92 100%);
      border:1px solid rgba(255,255,255,.12); border-radius:20px; padding:22px 26px;
      margin-bottom:18px; box-shadow:0 18px 40px rgba(0,0,0,.38);
  }}
  .hero h1 {{ margin:0; font-size:1.75rem; font-weight:800; }}
  .hero p  {{ margin:6px 0 0; color:{MUTED}; font-size:.93rem; }}
  .pill {{ display:inline-block; margin-top:12px; margin-right:8px; padding:4px 12px;
           border-radius:999px; font-size:.75rem; font-weight:600;
           background:rgba(59,130,246,.18); color:{SKY}; border:1px solid rgba(96,165,250,.35); }}
  .kpi {{ background:linear-gradient(160deg, rgba(22,50,95,.92) 0%, rgba(10,23,48,.92) 100%);
          border:1px solid {LINE}; border-left:3px solid {BLUE}; border-radius:16px;
          padding:16px 18px; height:100%; box-shadow:0 10px 26px rgba(0,0,0,.30); }}
  .kpi .label {{ color:{MUTED}; font-size:.78rem; font-weight:600; letter-spacing:.4px;
                 text-transform:uppercase; }}
  .kpi .value {{ color:#fff; font-size:1.6rem; font-weight:800; margin-top:6px; line-height:1.15; }}
  .kpi .unit {{ font-size:.85rem; color:{MUTED}; font-weight:600; margin-left:4px; }}
  .kpi .delta {{ font-size:.80rem; font-weight:700; margin-top:6px; }}
  .up {{ color:{GREEN}; }} .down {{ color:{RED}; }} .flat {{ color:{MUTED}; }}
  .panel {{ background:rgba(14,34,68,.62); border:1px solid {LINE}; border-radius:16px;
            padding:16px 18px 6px; margin-bottom:6px; }}
  .panel h4 {{ margin:0 0 2px; font-size:1rem; font-weight:700; }}
  .panel .sub {{ color:{MUTED}; font-size:.8rem; margin:0 0 10px; }}
  .stTabs [data-baseweb="tab-list"] {{ gap:6px; border-bottom:1px solid {LINE}; }}
  .stTabs [data-baseweb="tab"] {{ background:rgba(255,255,255,.03); border-radius:10px 10px 0 0;
      padding:10px 16px; color:{MUTED}; font-weight:600; }}
  .stTabs [aria-selected="true"] {{
      background:linear-gradient(180deg, rgba(59,130,246,.28), rgba(59,130,246,.06));
      color:#fff !important; border-bottom:2px solid {BLUE}; }}
  [data-testid="stDataFrame"] {{ border:1px solid {LINE}; border-radius:12px; }}
  .stAlert {{ border-radius:12px; }}
  footer, #MainMenu {{ visibility:hidden; }}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 3) Data access
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_con() -> duckdb.DuckDBPyConnection:
    if not os.path.exists(DB_PATH):
        st.error(f"ไม่พบไฟล์ฐานข้อมูล: `{DB_PATH}`\n\n"
                 "วาง app.py ไว้โฟลเดอร์เดียวกับ dev.duckdb หรือกำหนด `GAS_DW_PATH`")
        st.stop()
    return duckdb.connect(DB_PATH, read_only=True)


@st.cache_data(show_spinner=False)
def q(sql: str, params: tuple | list | None = None) -> pd.DataFrame:
    return get_con().execute(sql, list(params) if params else []).df()


def panel(title: str, sub: str = "") -> None:
    st.markdown(f'<div class="panel"><h4>{title}</h4><p class="sub">{sub}</p></div>',
                unsafe_allow_html=True)


def style(fig: go.Figure, height: int = 340, legend_top: bool = True) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=28, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, 'IBM Plex Sans Thai', sans-serif", color=INK, size=12.5),
        hoverlabel=dict(bgcolor=NAVY_800, bordercolor=BLUE, font_color=INK),
        colorway=PALETTE)
    if legend_top:
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                                      bgcolor="rgba(0,0,0,0)", title_text=""))
    fig.update_xaxes(gridcolor=LINE, zerolinecolor=LINE, linecolor=LINE,
                     tickfont_color=MUTED, title_font_color=MUTED)
    fig.update_yaxes(gridcolor=LINE, zerolinecolor=LINE, linecolor=LINE,
                     tickfont_color=MUTED, title_font_color=MUTED)
    return fig


def kpi(col, label: str, value: str, unit: str = "", delta: float | None = None,
        delta_label: str = "vs ช่วงก่อนหน้า") -> None:
    if delta is None:
        d = f'<div class="delta flat">{delta_label}: —</div>'
    else:
        cls = "up" if delta > .0005 else ("down" if delta < -.0005 else "flat")
        arw = "▲" if delta > .0005 else ("▼" if delta < -.0005 else "▬")
        d = (f'<div class="delta {cls}">{arw} {abs(delta)*100:,.1f}% '
             f'<span style="color:{MUTED};font-weight:500">{delta_label}</span></div>')
    col.markdown(f'<div class="kpi"><div class="label">{label}</div>'
                 f'<div class="value">{value}<span class="unit">{unit}</span></div>{d}</div>',
                 unsafe_allow_html=True)


def pct_change(cur, prev) -> float | None:
    if prev in (None, 0) or pd.isna(prev) or prev == 0:
        return None
    return (cur - prev) / prev


def guard(df: pd.DataFrame, msg: str = "ไม่มีข้อมูลในเงื่อนไขที่เลือก") -> bool:
    """คืน True เมื่อมีข้อมูลให้วาด, False พร้อมแสดงข้อความเมื่อว่าง"""
    if df is None or df.empty:
        st.info(msg)
        return False
    return True


# ---------------------------------------------------------------------------
# 4) Sidebar filters
# ---------------------------------------------------------------------------
dim_station = q("select gasstation_id, gasstation_name from dim_gasstation "
                "where not is_unknown_member order by gasstation_id")
dim_prod = q("select product_id, product_name, is_fuel from dim_product "
             "where not is_unknown_member order by is_fuel desc, product_id")
bounds = q(f"select min({DAY.format(c='date_day')}) d0, max({DAY.format(c='date_day')}) d1 "
           "from dim_date where date_key <> -1")
D0, D1 = bounds.iloc[0, 0], bounds.iloc[0, 1]

with st.sidebar:
    st.markdown(f'<div style="font-size:1.15rem;font-weight:800;color:#fff">⛽ Fuel Analytics</div>'
                f'<div style="color:{MUTED};font-size:.78rem;margin-bottom:14px">'
                f'Star Schema · DuckDB · dbt</div>', unsafe_allow_html=True)

    st.markdown("##### 🗓️ ช่วงวันที่")
    dr = st.date_input("ช่วงวันที่", value=(D0, D1), min_value=D0, max_value=D1,
                       label_visibility="collapsed")
    start_d, end_d = dr if isinstance(dr, (tuple, list)) and len(dr) == 2 else (D0, D1)

    st.markdown("##### 🏪 สถานีบริการ")
    st.caption(f"คลังข้อมูลมี {len(dim_station):,} สถานี")
    scope = st.radio("ขอบเขต", ["Top 10 ตามยอดขาย", "Top 25 ตามยอดขาย", "ทั้งหมด", "เลือกเอง"],
                     label_visibility="collapsed")

    st.markdown("##### 🛢️ สินค้า")
    fuel_only = st.toggle("เฉพาะน้ำมันเชื้อเพลิง", value=True)
    pool = dim_prod[dim_prod["is_fuel"]] if fuel_only else dim_prod
    prod_names = st.multiselect("สินค้า", pool["product_name"].tolist(),
                                default=pool["product_name"].tolist(),
                                label_visibility="collapsed")

if not prod_names:
    st.warning("กรุณาเลือกอย่างน้อย 1 สินค้า")
    st.stop()

P = dim_prod.loc[dim_prod["product_name"].isin(prod_names), "product_id"].tolist()
k0 = int(pd.Timestamp(start_d).strftime("%Y%m%d"))
k1 = int(pd.Timestamp(end_d).strftime("%Y%m%d"))

# จัดอันดับสถานีตามยอดขายในช่วงที่เลือก (ใช้ int_sales_daily ซึ่งเบากว่า fact_sales)
rank_st = q("""
    select s.gasstation_id, g.gasstation_name, sum(s.sales_amount) as sales_amount
    from int_sales_daily s
    join dim_gasstation g on s.gasstation_id = g.gasstation_id
    where s.product_id = any(?) and s.date_key between ? and ?
    group by 1, 2 order by 3 desc
""", (P, k0, k1))

if scope == "ทั้งหมด":
    S = dim_station["gasstation_id"].tolist()
elif scope.startswith("Top"):
    n = int(scope.split()[1])
    S = rank_st.head(n)["gasstation_id"].tolist()
else:
    with st.sidebar:
        picked = st.multiselect("เลือกสถานี", dim_station["gasstation_name"].tolist(),
                                default=rank_st.head(5)["gasstation_name"].tolist())
    S = dim_station.loc[dim_station["gasstation_name"].isin(picked), "gasstation_id"].tolist()

if not S:
    st.warning("กรุณาเลือกอย่างน้อย 1 สถานี")
    st.stop()

with st.sidebar:
    st.divider()
    st.caption("ข้อมูลทุกกราฟดึงจากตาราง Dimension / Fact / Mart และตัดแถวที่ติดธง "
               "`is_data_quality_flagged` ออกจากการวิเคราะห์")

span = (pd.Timestamp(end_d) - pd.Timestamp(start_d)).days + 1
p0 = int((pd.Timestamp(start_d) - pd.Timedelta(days=span)).strftime("%Y%m%d"))
p1 = int((pd.Timestamp(start_d) - pd.Timedelta(days=1)).strftime("%Y%m%d"))


def FP(a: int, b: int) -> list:
    return [S, P, a, b]


FW = ("f.gasstation_id = any(?) and f.product_id = any(?) "
      "and f.date_key between ? and ? and not f.is_data_quality_flagged")
MW = "gasstation_id = any(?) and product_id = any(?) and cast(date_day as date) between ? and ?"


def MP() -> list:
    return [S, P, start_d, end_d]


# ---------------------------------------------------------------------------
# 5) Hero + KPI
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="hero">
  <h1>⛽ แดชบอร์ดวิเคราะห์สถานีบริการน้ำมัน</h1>
  <p>ยอดขาย · พฤติกรรมลูกค้า · ประสิทธิภาพพนักงาน · การบริหารคลังน้ำมัน &nbsp;|&nbsp;
     {start_d:%d %b %Y} – {end_d:%d %b %Y}</p>
  <span class="pill">{len(S)} สถานี</span>
  <span class="pill">{len(P)} สินค้า</span>
  <span class="pill">{span} วัน</span>
  <span class="pill">Source: dim_ / fact_ / mart_</span>
</div>
""", unsafe_allow_html=True)

KPI_SQL = f"""
select coalesce(sum(f.total_price), 0) sales_amount,
       coalesce(sum(case when p.is_fuel then f.quantity_sold end), 0) fuel_liters,
       count(distinct f.invoice_id) bill_count,
       count(distinct f.customer_id) customer_count
from fact_sales f join dim_product p on f.product_id = p.product_id
where {FW}"""
cur = q(KPI_SQL, FP(k0, k1)).iloc[0]
prev = q(KPI_SQL, FP(p0, p1)).iloc[0]

c = st.columns(5)
kpi(c[0], "ยอดขายรวม", f"{cur.sales_amount:,.0f}", " ฿",
    pct_change(cur.sales_amount, prev.sales_amount))
kpi(c[1], "ปริมาณน้ำมันที่ขาย", f"{cur.fuel_liters:,.0f}", " ลิตร",
    pct_change(cur.fuel_liters, prev.fuel_liters))
kpi(c[2], "จำนวนบิล", f"{cur.bill_count:,.0f}", " บิล",
    pct_change(cur.bill_count, prev.bill_count))
ab = cur.sales_amount / cur.bill_count if cur.bill_count else 0
abp = prev.sales_amount / prev.bill_count if prev.bill_count else 0
kpi(c[3], "ยอดขายเฉลี่ย/บิล", f"{ab:,.0f}", " ฿", pct_change(ab, abp))
kpi(c[4], "ลูกค้าที่ใช้บริการ", f"{cur.customer_count:,.0f}", " ราย",
    pct_change(cur.customer_count, prev.customer_count))
st.write("")

TABS = st.tabs(["📊 ภาพรวม", "⛽ การขาย", "👥 ลูกค้า", "🧑‍💼 พนักงาน & การชำระเงิน",
                "🛢️ คลังน้ำมัน", "✅ คุณภาพข้อมูล"])

# ===========================================================================
# TAB 1 — ภาพรวม
# ===========================================================================
with TABS[0]:
    L, R = st.columns([1.85, 1])
    with L:
        panel("แนวโน้มยอดขายรายวัน", "fact_sales × dim_date · เส้นประ = ค่าเฉลี่ยเคลื่อนที่ 7 วัน")
        daily = q(f"""
            select {DAY.format(c='d.date_day')} as date_day, sum(f.total_price) sales_amount
            from fact_sales f join dim_date d on f.date_key = d.date_key
            where {FW} group by 1 order by 1""", FP(k0, k1))
        if guard(daily):
            daily["ma7"] = daily["sales_amount"].rolling(7, min_periods=1).mean()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=daily.date_day, y=daily.sales_amount, name="ยอดขายรายวัน",
                                     mode="lines", line=dict(color=SKY, width=2.2),
                                     fill="tozeroy", fillcolor="rgba(96,165,250,.16)",
                                     hovertemplate="%{x|%d %b}<br>%{y:,.0f} ฿<extra></extra>"))
            fig.add_trace(go.Scatter(x=daily.date_day, y=daily.ma7, name="ค่าเฉลี่ย 7 วัน",
                                     mode="lines", line=dict(color=GOLD, width=2, dash="dash"),
                                     hovertemplate="%{y:,.0f} ฿<extra></extra>"))
            fig.update_yaxes(title_text="บาท")
            st.plotly_chart(style(fig, 330), width="stretch")

    with R:
        panel("ยอดขายตามสถานี", "แสดงสูงสุด 15 อันดับแรกในกลุ่มที่เลือก")
        bs = rank_st[rank_st["gasstation_id"].isin(S)].head(15).sort_values("sales_amount")
        if guard(bs):
            fig = px.bar(bs, x="sales_amount", y="gasstation_name", orientation="h")
            fig.update_traces(marker=dict(color=bs.sales_amount, colorscale=BLUE_SCALE),
                              hovertemplate="%{y}<br>%{x:,.0f} ฿<extra></extra>")
            fig.update_xaxes(title_text="บาท")
            fig.update_yaxes(title_text="")
            st.plotly_chart(style(fig, 330, False), width="stretch")

    A, B = st.columns([1, 1.6])
    with A:
        panel("สัดส่วนยอดขายตามสินค้า", "fact_sales × dim_product")
        mix = q(f"""
            select p.product_name, sum(f.total_price) sales_amount
            from fact_sales f join dim_product p on f.product_id = p.product_id
            where {FW} group by 1 order by 2 desc""", FP(k0, k1))
        if guard(mix):
            fig = go.Figure(go.Pie(labels=mix.product_name, values=mix.sales_amount, hole=.62,
                                   marker=dict(colors=PALETTE, line=dict(color=NAVY_950, width=2)),
                                   textinfo="percent", textfont=dict(color="#fff", size=11),
                                   hovertemplate="%{label}<br>%{value:,.0f} ฿ (%{percent})<extra></extra>"))
            fig.add_annotation(text=f"<b>{mix.sales_amount.sum()/1e6:,.1f}</b><br>"
                                    f"<span style='font-size:11px;color:{MUTED}'>ล้านบาท</span>",
                               showarrow=False, font=dict(size=20, color="#fff"))
            st.plotly_chart(style(fig, 360), width="stretch")

    with B:
        panel("ความหนาแน่นการขาย: ชั่วโมง × วันในสัปดาห์",
              "fact_sales × dim_date — สีเข้ม = จำนวนบิลมาก")
        hm = q(f"""
            select d.weekday_name, {HOUR.format(c='f.hour_of_day')} as hh,
                   count(distinct f.invoice_id) bill_count
            from fact_sales f join dim_date d on f.date_key = d.date_key
            where {FW} group by 1, 2""", FP(k0, k1))
        if guard(hm):
            hm["wd"] = hm.weekday_name.map(WEEKDAY_TH)
            piv = (hm.pivot_table(index="wd", columns="hh", values="bill_count",
                                  aggfunc="sum", fill_value=0)
                     .reindex(WEEKDAY_ORDER).fillna(0))
            fig = go.Figure(go.Heatmap(z=piv.values, x=[f"{h:02d}" for h in piv.columns],
                                       y=piv.index, colorscale=BLUE_SCALE, xgap=2, ygap=2,
                                       colorbar=dict(title="บิล", outlinewidth=0,
                                                     tickfont=dict(color=MUTED)),
                                       hovertemplate="%{y} %{x}:00<br>%{z:,.0f} บิล<extra></extra>"))
            fig.update_xaxes(title_text="ชั่วโมง")
            fig.update_yaxes(autorange="reversed", title_text="")
            st.plotly_chart(style(fig, 360, False), width="stretch")

    panel("ยอดขายรายวันแยกตามสถานี", "int_sales_daily — แสดง 8 สถานีที่ยอดสูงสุด")
    top8 = rank_st[rank_st.gasstation_id.isin(S)].head(8)["gasstation_id"].tolist()
    if top8:
        sd = q("""
            select cast(d.date_day as date) date_day, g.gasstation_name,
                   sum(s.sales_amount) sales_amount
            from int_sales_daily s
            join dim_date d on s.date_key = d.date_key
            join dim_gasstation g on s.gasstation_id = g.gasstation_id
            where s.gasstation_id = any(?) and s.product_id = any(?)
              and s.date_key between ? and ?
            group by 1, 2 order by 1""", (top8, P, k0, k1))
        if guard(sd):
            fig = px.area(sd, x="date_day", y="sales_amount", color="gasstation_name")
            fig.update_traces(line=dict(width=1.2),
                              hovertemplate="%{y:,.0f} ฿<extra>%{fullData.name}</extra>")
            fig.update_yaxes(title_text="บาท")
            fig.update_xaxes(title_text="")
            st.plotly_chart(style(fig, 320), width="stretch")

# ===========================================================================
# TAB 2 — การขาย (Q1, Q2, Q9)
# ===========================================================================
with TABS[1]:
    st.markdown("#### Q1 · สถานีใดสร้างยอดขายสูงสุดในแต่ละวัน และมาจากน้ำมันชนิดใด")
    c1, c2 = st.columns([1, 1.35])
    with c1:
        panel("จำนวนวันที่ครองอันดับ 1", f"{T['mart_01']} (station_day_rank = 1)")
        td = q(f"""
            select g.gasstation_name, count(distinct cast(m.date_day as date)) days_rank1
            from {T['mart_01']} m
            join dim_gasstation g on m.gasstation_id = g.gasstation_id
            where m.station_day_rank = 1 and m.gasstation_id = any(?)
              and cast(m.date_day as date) between ? and ?
            group by 1 order by 2 desc limit 15""", (S, start_d, end_d))
        if guard(td, "ไม่มีสถานีในกลุ่มที่เลือกที่ครองอันดับ 1 ในช่วงนี้"):
            fig = px.bar(td, x="gasstation_name", y="days_rank1", text="days_rank1")
            fig.update_traces(marker_color=BLUE, textposition="outside",
                              textfont=dict(color=INK),
                              hovertemplate="%{x}<br>%{y} วัน<extra></extra>")
            fig.update_xaxes(title_text="", tickangle=-25)
            fig.update_yaxes(title_text="จำนวนวัน")
            st.plotly_chart(style(fig, 340, False), width="stretch")

    with c2:
        panel("โครงสร้างยอดขาย: สถานี → สินค้า", f"{T['mart_01']} × dim_product (10 สถานีแรก)")
        top10 = rank_st[rank_st.gasstation_id.isin(S)].head(10)["gasstation_id"].tolist()
        tree = q(f"""
            select g.gasstation_name, p.product_name, sum(m.sales_amount) sales_amount
            from {T['mart_01']} m
            join dim_gasstation g on m.gasstation_id = g.gasstation_id
            join dim_product p on m.product_id = p.product_id
            where m.gasstation_id = any(?) and m.product_id = any(?)
              and cast(m.date_day as date) between ? and ?
            group by 1, 2""", (top10, P, start_d, end_d))
        if guard(tree):
            fig = px.treemap(tree, path=["gasstation_name", "product_name"],
                             values="sales_amount", color="sales_amount",
                             color_continuous_scale=BLUE_SCALE)
            fig.update_traces(marker=dict(line=dict(color=NAVY_950, width=2)),
                              textfont=dict(color="#fff", size=12),
                              hovertemplate="<b>%{label}</b><br>%{value:,.0f} ฿<extra></extra>")
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(style(fig, 340, False), width="stretch")

    st.divider()
    st.markdown("#### Q2 · ช่วงเวลาขายหนาแน่นของแต่ละสถานี")
    opts = rank_st[rank_st.gasstation_id.isin(S)]["gasstation_name"].tolist()
    sel = st.selectbox("เลือกสถานี", opts, key="q2")
    sid = int(dim_station.loc[dim_station.gasstation_name == sel, "gasstation_id"].iloc[0])

    c1, c2 = st.columns([1.55, 1])
    with c1:
        panel(f"ปริมาณขายเฉลี่ยต่อชั่วโมง — {sel}",
              f"{T['mart_02']} (สรุปทั้งช่วงข้อมูล) · ลิตรต่อชั่วโมงที่มีการขาย")
        h2 = q(f"""
            select {HOUR.format(c='hour_of_day')} as hh, weekday_name,
                   avg(avg_qty_per_hour_observed) v
            from {T['mart_02']} where gasstation_id = ? group by 1, 2""", (sid,))
        if guard(h2):
            h2["wd"] = h2.weekday_name.map(WEEKDAY_TH)
            piv = h2.pivot_table(index="wd", columns="hh", values="v",
                                 aggfunc="mean").reindex(WEEKDAY_ORDER)
            fig = go.Figure(go.Heatmap(z=piv.values, x=[f"{h:02d}" for h in piv.columns],
                                       y=piv.index, colorscale=BLUE_SCALE, xgap=2, ygap=2,
                                       colorbar=dict(title="ลิตร/ชม.", outlinewidth=0,
                                                     tickfont=dict(color=MUTED)),
                                       hovertemplate="%{y} %{x}:00<br>%{z:,.0f} ลิตร<extra></extra>"))
            fig.update_xaxes(title_text="ชั่วโมง")
            fig.update_yaxes(autorange="reversed", title_text="")
            st.plotly_chart(style(fig, 330, False), width="stretch")

    with c2:
        panel("จำนวนบิลตามช่วงเวลาของวัน", "fact_sales × dim_hour (day_part)")
        dp = q(f"""
            select h.day_part, count(distinct f.invoice_id) bill_count
            from fact_sales f
            join dim_hour h on {HOUR.format(c='f.hour_of_day')} = h.hour_of_day
            where {FW} group by 1""", FP(k0, k1))
        if guard(dp):
            dp["day_part"] = pd.Categorical(dp.day_part, DAYPART_ORDER, ordered=True)
            dp = dp.sort_values("day_part")
            fig = go.Figure(go.Barpolar(
                r=dp.bill_count, theta=dp.day_part.astype(str),
                marker=dict(color=dp.bill_count, colorscale=BLUE_SCALE,
                            line=dict(color=NAVY_950, width=1.5)),
                hovertemplate="%{theta}<br>%{r:,.0f} บิล<extra></extra>"))
            fig.update_layout(polar=dict(
                bgcolor="rgba(255,255,255,.03)",
                radialaxis=dict(gridcolor=LINE, tickfont=dict(color=MUTED, size=9), angle=90),
                angularaxis=dict(gridcolor=LINE, tickfont=dict(color=INK, size=11))))
            st.plotly_chart(style(fig, 330, False), width="stretch")

    st.divider()
    st.markdown("#### Q9 · ยอดขายเปลี่ยนแปลงจากวันเดียวกันในสัปดาห์ก่อนเท่าใด")
    c1, c2 = st.columns([1.5, 1])
    with c1:
        panel("ผลต่างยอดขายรายวัน เทียบ 7 วันก่อน",
              f"{T['mart_09']} — เขียว = โตขึ้น / แดง = ลดลง")
        wow = q(f"""select cast(date_day as date) date_day, sum(sales_diff) sales_diff
                    from {T['mart_09']} where {MW} group by 1 order by 1""", MP())
        if guard(wow, "ช่วงที่เลือกไม่มีคู่วันเทียบย้อนหลัง 7 วัน (ข้อมูลอาจสั้นเกินไป)"):
            fig = go.Figure(go.Bar(x=wow.date_day, y=wow.sales_diff,
                                   marker_color=[GREEN if v >= 0 else RED for v in wow.sales_diff],
                                   hovertemplate="%{x|%d %b}<br>%{y:+,.0f} ฿<extra></extra>"))
            fig.add_hline(y=0, line_color=MUTED, line_width=1)
            fig.update_yaxes(title_text="ผลต่าง (บาท)")
            fig.update_xaxes(title_text="")
            st.plotly_chart(style(fig, 330, False), width="stretch")

    with c2:
        panel("สินค้าที่ขับเคลื่อนการเปลี่ยนแปลง", f"{T['mart_09']} — ผลรวมผลต่างรายสินค้า")
        wp = q(f"""select p.product_name, sum(m.sales_diff) sales_diff
                   from {T['mart_09']} m join dim_product p on m.product_id = p.product_id
                   where m.gasstation_id = any(?) and m.product_id = any(?)
                     and cast(m.date_day as date) between ? and ?
                   group by 1 order by 2""", (S, P, start_d, end_d))
        if guard(wp):
            fig = go.Figure(go.Bar(x=wp.sales_diff, y=wp.product_name, orientation="h",
                                   marker_color=[GREEN if v >= 0 else RED for v in wp.sales_diff],
                                   hovertemplate="%{y}<br>%{x:+,.0f} ฿<extra></extra>"))
            fig.add_vline(x=0, line_color=MUTED, line_width=1)
            fig.update_xaxes(title_text="ผลต่างสะสม (บาท)")
            fig.update_yaxes(title_text="")
            st.plotly_chart(style(fig, 330, False), width="stretch")

# ===========================================================================
# TAB 3 — ลูกค้า
# ===========================================================================
with TABS[2]:
    nvc = q("select count(*) n from dim_vehicle_category where not is_unknown_member").iloc[0].n
    if nvc == 0:
        st.warning("⚠️ `dim_vehicle_category` มีแต่สมาชิก Unknown — seed `ref_vehicle_category` ว่าง "
                   "ทำให้ลูกค้าทุกรายถูกจัดเป็น \"Unknown\" กราฟที่แยกตามประเภทรถจึงมีกลุ่มเดียว "
                   "แก้ได้โดยเติมข้อมูลใน seed แล้วรัน `dbt seed && dbt run`")

    st.markdown("#### Q3 · ลูกค้าแต่ละประเภทรถนิยมน้ำมันชนิดใด")
    c1, c2 = st.columns([1.4, 1])
    with c1:
        panel("สัดส่วนปริมาณขาย: ประเภทรถ × สินค้า", f"{T['mart_03']} — แกน Y เป็นสัดส่วน 100%")
        vp = q(f"""select vehicle_category, product_name, sum(quantity_sold) quantity_sold
                   from {T['mart_03']}
                   where gasstation_id = any(?) and product_id = any(?)
                   group by 1, 2""", (S, P))
        if guard(vp):
            vp["share"] = vp.quantity_sold / vp.groupby("vehicle_category")["quantity_sold"].transform("sum")
            fig = px.bar(vp, x="vehicle_category", y="share", color="product_name",
                         custom_data=["quantity_sold"])
            fig.update_traces(hovertemplate="%{x}<br>%{y:.1%} (%{customdata[0]:,.0f} ลิตร)"
                                            "<extra>%{fullData.name}</extra>")
            fig.update_yaxes(tickformat=".0%", title_text="สัดส่วนปริมาณ")
            fig.update_xaxes(title_text="")
            st.plotly_chart(style(fig, 350), width="stretch")

    with c2:
        panel("ปริมาณเฉลี่ยต่อบิลตามสินค้า", f"{T['mart_03']} — ลิตร/บิล")
        aq = q(f"""select product_name,
                          sum(quantity_sold)/nullif(sum(bill_count),0) avg_qty
                   from {T['mart_03']}
                   where gasstation_id = any(?) and product_id = any(?)
                   group by 1 order by 2""", (S, P))
        if guard(aq):
            fig = px.bar(aq, x="avg_qty", y="product_name", orientation="h",
                         text=aq.avg_qty.map(lambda v: f"{v:,.1f} ล."))
            fig.update_traces(marker=dict(color=aq.avg_qty, colorscale=BLUE_SCALE),
                              textposition="outside", textfont=dict(color=INK, size=11),
                              hovertemplate="%{y}<br>%{x:,.1f} ลิตร/บิล<extra></extra>")
            fig.update_xaxes(title_text="ลิตร/บิล")
            fig.update_yaxes(title_text="")
            st.plotly_chart(style(fig, 350, False), width="stretch")

    st.divider()
    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.markdown("#### Q5 · ลูกค้า 10 อันดับแรกของสถานี")
        sel5 = st.selectbox("เลือกสถานี", opts, key="q5")
        sid5 = int(dim_station.loc[dim_station.gasstation_name == sel5, "gasstation_id"].iloc[0])
        t10 = q(f"""select customer_name, vehicle_category, product_name, customer_sales,
                           bill_count, rank_in_station
                    from {T['mart_05']} where gasstation_id = ?
                    order by rank_in_station""", (sid5,))
        if guard(t10):
            t10 = t10.sort_values("customer_sales")
            fig = px.bar(t10, x="customer_sales", y="customer_name", orientation="h",
                         custom_data=["product_name", "bill_count", "rank_in_station"])
            fig.update_traces(marker=dict(color=t10.customer_sales, colorscale=BLUE_SCALE),
                              hovertemplate="อันดับ %{customdata[2]} · %{y}<br>%{x:,.0f} ฿ · "
                                            "%{customdata[1]} บิล<br>สินค้าหลัก: %{customdata[0]}"
                                            "<extra></extra>")
            fig.update_xaxes(title_text="ยอดซื้อน้ำมันสะสม (บาท)")
            fig.update_yaxes(title_text="")
            st.plotly_chart(style(fig, 400, False), width="stretch")

    with c2:
        st.markdown("#### Q6 · อัตราการกลับมาซื้อซ้ำ")
        panel("Repeat rate ตามประเภทรถ", f"{T['mart_06']} — ซื้อ ≥ 2 วัน ÷ ลูกค้าทั้งหมด")
        rp = q(f"""select vehicle_category, sum(repeat_customers) rc, sum(total_customers) tc,
                          sum(repeat_customers)/nullif(sum(total_customers),0) repeat_rate
                   from {T['mart_06']} where gasstation_id = any(?)
                   group by 1 order by 4 desc""", (S,))
        if guard(rp):
            fig = go.Figure(go.Bar(
                x=rp.vehicle_category, y=rp.repeat_rate,
                marker=dict(color=rp.repeat_rate, colorscale=BLUE_SCALE),
                text=[f"{v:.0%}" for v in rp.repeat_rate], textposition="outside",
                textfont=dict(color=INK), customdata=rp[["rc", "tc"]].values,
                hovertemplate="%{x}<br>%{y:.1%}<br>%{customdata[0]:,.0f} / "
                              "%{customdata[1]:,.0f} ราย<extra></extra>"))
            fig.update_yaxes(tickformat=".0%", title_text="อัตราซื้อซ้ำ", range=[0, 1.05])
            fig.update_xaxes(title_text="")
            st.plotly_chart(style(fig, 400, False), width="stretch")

    st.divider()
    c1, c2 = st.columns([1, 1.25])
    with c1:
        st.markdown("#### Q7 · ลูกค้าที่ใช้บริการหลายสถานี")
        panel("จำนวนลูกค้าแยกตามจำนวนสถานีที่ใช้บริการ", T["mart_07"])
        ms = q(f"""select station_count, count(distinct customer_id) customers
                   from {T['mart_07']} group by 1 order by 1""")
        if guard(ms):
            fig = px.bar(ms, x="station_count", y="customers")
            fig.update_traces(marker=dict(color=ms.customers, colorscale=BLUE_SCALE),
                              hovertemplate="ใช้บริการ %{x} สถานี<br>%{y:,.0f} ราย<extra></extra>")
            fig.update_xaxes(title_text="จำนวนสถานีที่ใช้บริการ")
            fig.update_yaxes(title_text="จำนวนลูกค้า")
            st.plotly_chart(style(fig, 360, False), width="stretch")

    with c2:
        st.markdown("#### Q10 · คู่สินค้าที่พบร่วมกันในบิลเดียว")
        panel("Top 12 คู่สินค้า", f"{T['mart_10']} — นับคู่ละครั้งต่อบิล")
        pr = q(f"""select product_name_a || '  +  ' || product_name_b pair,
                          sum(bill_count_with_pair) bills, avg(avg_bill_value) abv
                   from {T['mart_10']} where gasstation_id = any(?)
                   group by 1 order by 2 desc limit 12""", (S,))
        if guard(pr, "ไม่พบบิลที่มีสินค้ามากกว่า 1 ชนิดในกลุ่มที่เลือก"):
            pr = pr.sort_values("bills")
            fig = px.bar(pr, x="bills", y="pair", orientation="h", custom_data=["abv"])
            fig.update_traces(marker=dict(color=pr.bills, colorscale=BLUE_SCALE),
                              hovertemplate="%{y}<br>%{x:,.0f} บิล<br>"
                                            "ยอดบิลเฉลี่ย %{customdata[0]:,.0f} ฿<extra></extra>")
            fig.update_xaxes(title_text="จำนวนบิลที่พบคู่นี้")
            fig.update_yaxes(title_text="")
            st.plotly_chart(style(fig, 360, False), width="stretch")

# ===========================================================================
# TAB 4 — พนักงาน & การชำระเงิน
# ===========================================================================
with TABS[3]:
    st.markdown("#### Q4 · วิธีชำระเงินสัมพันธ์กับมูลค่าการซื้ออย่างไร")
    st.caption(f"หมายเหตุ: {T['mart_04']} เก็บเฉพาะ avg_sales_per_bill "
               "ยอดรวมจึงคำนวณกลับเป็น avg_sales_per_bill × bill_count")
    c1, c2, c3 = st.columns([1, 1.25, 1.1])

    with c1:
        panel("สัดส่วนจำนวนบิลตามวิธีชำระเงิน", T["mart_04"])
        pm = q(f"""select payment_method_label, sum(bill_count) bill_count
                   from {T['mart_04']} where gasstation_id = any(?)
                   group by 1 order by 2 desc""", (S,))
        if guard(pm):
            fig = go.Figure(go.Pie(labels=pm.payment_method_label, values=pm.bill_count, hole=.6,
                                   marker=dict(colors=PALETTE, line=dict(color=NAVY_950, width=2)),
                                   textinfo="percent", textfont=dict(color="#fff", size=11),
                                   hovertemplate="%{label}<br>%{value:,.0f} บิล (%{percent})<extra></extra>"))
            fig.add_annotation(text=f"<b>{pm.bill_count.sum():,.0f}</b><br>"
                                    f"<span style='font-size:11px;color:{MUTED}'>บิล</span>",
                               showarrow=False, font=dict(size=18, color="#fff"))
            st.plotly_chart(style(fig, 340), width="stretch")

    with c2:
        panel("ยอดขายเฉลี่ยต่อบิล: วิธีชำระ × ช่วงเวลา", f"{T['mart_04']} — ถ่วงน้ำหนักด้วยจำนวนบิล")
        pv = q(f"""select payment_method_label, day_part,
                          sum(avg_sales_per_bill * bill_count)/nullif(sum(bill_count),0) v
                   from {T['mart_04']} where gasstation_id = any(?)
                   group by 1, 2""", (S,))
        if guard(pv):
            piv = pv.pivot(index="payment_method_label", columns="day_part", values="v")
            piv = piv.reindex(columns=[d for d in DAYPART_ORDER if d in piv.columns])
            fig = go.Figure(go.Heatmap(
                z=piv.values, x=piv.columns, y=piv.index, colorscale=BLUE_SCALE, xgap=3, ygap=3,
                text=[[f"{v:,.0f}" if pd.notna(v) else "" for v in r] for r in piv.values],
                texttemplate="%{text}", textfont=dict(color="#fff", size=11),
                colorbar=dict(title="฿/บิล", outlinewidth=0, tickfont=dict(color=MUTED)),
                hovertemplate="%{y} · %{x}<br>%{z:,.0f} ฿/บิล<extra></extra>"))
            fig.update_xaxes(title_text="")
            fig.update_yaxes(title_text="")
            st.plotly_chart(style(fig, 340, False), width="stretch")

    with c3:
        panel("ยอดรวมตามวิธีชำระเงิน", f"{T['mart_04']} — avg_sales_per_bill × bill_count")
        tt = q(f"""select payment_method_label, sum(avg_sales_per_bill * bill_count) amt
                   from {T['mart_04']} where gasstation_id = any(?)
                   group by 1 order by 2""", (S,))
        if guard(tt):
            fig = px.bar(tt, x="amt", y="payment_method_label", orientation="h")
            fig.update_traces(marker=dict(color=tt.amt, colorscale=BLUE_SCALE),
                              hovertemplate="%{y}<br>%{x:,.0f} ฿<extra></extra>")
            fig.update_xaxes(title_text="บาท")
            fig.update_yaxes(title_text="")
            st.plotly_chart(style(fig, 340, False), width="stretch")

    st.divider()
    st.markdown("#### Q8 · ปริมาณรายการขายของพนักงานและตำแหน่ง")
    c1, c2 = st.columns([1, 1.4])
    with c1:
        panel("จำนวนบิลเฉลี่ยต่อคนต่อวันตามตำแหน่ง", f"{T['mart_08']} × dim_employee")
        pos = q(f"""select position, sum(bill_count) bills,
                           count(distinct cast(date_day as date)) n_days,
                           count(distinct employee_id) emps
                    from {T['mart_08']}
                    where gasstation_id = any(?) and cast(date_day as date) between ? and ?
                    group by 1""", (S, start_d, end_d))
        if guard(pos):
            pos["v"] = pos.bills / (pos.n_days * pos.emps)
            pos = pos.sort_values("v")
            fig = px.bar(pos, x="v", y="position", orientation="h",
                         text=pos.v.map(lambda x: f"{x:,.1f}"))
            fig.update_traces(marker=dict(color=pos.v, colorscale=BLUE_SCALE),
                              textposition="outside", textfont=dict(color=INK),
                              hovertemplate="%{y}<br>%{x:,.1f} บิล/คน/วัน<extra></extra>")
            fig.update_xaxes(title_text="บิล / คน / วัน")
            fig.update_yaxes(title_text="")
            st.plotly_chart(style(fig, 360, False), width="stretch")

    with c2:
        panel("พนักงานรายบุคคล: จำนวนบิล vs ยอดขาย",
              f"{T['mart_08']} — ขนาดจุด = ยอดขายเฉลี่ยต่อบิล (สุ่มแสดง 400 คน)")
        emp = q(f"""select employee_name, position, gasstation_name,
                           sum(bill_count) bills, sum(sales_amount) sales
                    from {T['mart_08']}
                    where gasstation_id = any(?) and cast(date_day as date) between ? and ?
                    group by 1, 2, 3 order by sales desc limit 400""", (S, start_d, end_d))
        if guard(emp):
            emp["avg_bill"] = emp.sales / emp.bills
            fig = px.scatter(emp, x="bills", y="sales", color="position", size="avg_bill",
                             size_max=20, hover_name="employee_name",
                             custom_data=["gasstation_name", "avg_bill"])
            fig.update_traces(marker=dict(line=dict(width=.6, color=NAVY_950), opacity=.85),
                              hovertemplate="<b>%{hovertext}</b><br>%{customdata[0]}<br>"
                                            "%{x:,.0f} บิล · %{y:,.0f} ฿<br>"
                                            "เฉลี่ย %{customdata[1]:,.0f} ฿/บิล<extra></extra>")
            fig.update_xaxes(title_text="จำนวนบิล")
            fig.update_yaxes(title_text="ยอดขาย (บาท)")
            st.plotly_chart(style(fig, 360), width="stretch")

# ===========================================================================
# TAB 5 — คลังน้ำมัน
# ===========================================================================
with TABS[4]:
    diag = q("""
        select
          (select count(*) from fact_inventory_transaction) total_txn,
          (select count(*) from fact_inventory_transaction where is_data_quality_flagged) flagged,
          (select count(*) from bridge_tank_product) bridge_rows,
          (select count(*) from dim_tank where tank_id <> -1) tanks,
          (select min(valid_from) from dim_tank where tank_id <> -1) tank_valid_from,
          (select min(cast(date_day as date)) from dim_date where date_key <> -1) first_day
    """).iloc[0]

    if diag.total_txn > 0 and diag.flagged == diag.total_txn:
        st.error(
            f"**ตารางฝั่งคลังน้ำมันยังไม่มีข้อมูลให้วิเคราะห์**\n\n"
            f"`fact_inventory_transaction` มี {diag.total_txn:,} แถว และติดธง "
            f"`is_data_quality_flagged` ทั้งหมด mart ที่กรอง `not is_data_quality_flagged` "
            f"จึงว่างเปล่า สาเหตุที่ตรวจพบ:"
        )
        st.markdown(f"""
1. **`bridge_tank_product` มี {diag.bridge_rows:,} แถว** แต่มีถังทั้งหมด {diag.tanks:,} ใบ
   → ธุรกรรมเกือบทั้งหมด map สินค้าไม่ได้ ทำให้ `product_id = -1`
   แก้ที่ seed `ref_tank_product_map` ให้ครบทุกถัง
2. **ช่วงเวลา validity ของถังไม่ครอบคลุมข้อมูลธุรกรรม**
   `dim_tank.valid_from` เริ่มที่ `{diag.tank_valid_from}` แต่ข้อมูลเริ่มที่ `{diag.first_day}`
   เงื่อนไข `transaction_timestamp >= valid_from` จึงไม่เป็นจริง ทำให้ join กับถังล้มเหลว
   → แก้โดยตั้ง `dbt_valid_from` ของ snapshot ให้ย้อนไปก่อนข้อมูลจริง หรือใช้ `updated_at`
   ที่อ้างอิงเวลาของข้อมูลแทนเวลารัน snapshot

หลังแก้แล้วรัน `dbt seed && dbt snapshot && dbt run` ใหม่ แท็บนี้จะแสดงผลเองโดยไม่ต้องแก้โค้ดแดชบอร์ด
        """)

    st.markdown("#### Q15 · ควรเติมน้ำมันถังใดก่อน")
    ro = q(f"""select gasstation_name, product_name, tank_id, latest_remaining_quantity,
                      avg_daily_sales_qty_7d, estimated_days_to_stockout
               from {T['mart_15']}
               where gasstation_id = any(?) and product_id = any(?)
               order by estimated_days_to_stockout nulls last limit 20""", (S, P))
    if guard(ro, "ยังไม่มีข้อมูลลำดับการเติมน้ำมัน (ดูสาเหตุด้านบน)"):
        show = ro.dropna(subset=["estimated_days_to_stockout"]).copy()
        if guard(show, "มีข้อมูลถังแต่คำนวณวันหมดไม่ได้ (อัตราขายเฉลี่ยเป็นศูนย์)"):
            show["label"] = show.gasstation_name + " · " + show.product_name
            show = show.sort_values("estimated_days_to_stockout", ascending=False)
            fig = go.Figure(go.Bar(
                x=show.estimated_days_to_stockout, y=show.label, orientation="h",
                marker_color=[RED if v < 3 else (GOLD if v < 7 else GREEN)
                              for v in show.estimated_days_to_stockout],
                customdata=show[["latest_remaining_quantity", "avg_daily_sales_qty_7d"]].values,
                hovertemplate="%{y}<br>เหลือ %{customdata[0]:,.0f} ลิตร<br>"
                              "ขายเฉลี่ย %{customdata[1]:,.0f} ลิตร/วัน<br>"
                              "<b>%{x:,.1f} วัน</b><extra></extra>"))
            fig.add_vline(x=3, line_color=RED, line_dash="dot")
            fig.update_xaxes(title_text="วันคงเหลือก่อนหมด")
            fig.update_yaxes(title_text="")
            st.plotly_chart(style(fig, 440, False), width="stretch")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Q12 · ถังที่ระดับต่ำกว่าเกณฑ์")
        low = q(f"""select gasstation_name, product_name,
                           count(*) filter (where is_below_threshold) low_events
                    from {T['mart_12']} where {MW} group by 1, 2
                    order by 3 desc limit 20""", MP())
        if guard(low, "ยังไม่มีข้อมูลระดับน้ำมันต่ำกว่าเกณฑ์"):
            low["label"] = low.gasstation_name + " · " + low.product_name
            low = low.sort_values("low_events")
            fig = px.bar(low, x="low_events", y="label", orientation="h")
            fig.update_traces(marker=dict(color=low.low_events, colorscale=BLUE_SCALE),
                              hovertemplate="%{y}<br>%{x:,.0f} ครั้ง<extra></extra>")
            fig.update_xaxes(title_text="จำนวนครั้ง")
            fig.update_yaxes(title_text="")
            st.plotly_chart(style(fig, 380, False), width="stretch")

    with c2:
        st.markdown("#### Q11 · รับเข้า vs จ่ายออก")
        imb = q(f"""select cast(date_day as date) date_day, sum(quantity_in) qin,
                           sum(quantity_out) qout
                    from {T['mart_11']} where {MW} group by 1 order by 1""", MP())
        if guard(imb, "ยังไม่มีข้อมูลการรับเข้า–จ่ายออก"):
            imb["cum"] = (imb.qin - imb.qout).cumsum()
            fig = go.Figure()
            fig.add_trace(go.Bar(x=imb.date_day, y=imb.qin, name="รับเข้า", marker_color=BLUE))
            fig.add_trace(go.Bar(x=imb.date_day, y=-imb.qout, name="จ่ายออก", marker_color=CYAN))
            fig.add_trace(go.Scatter(x=imb.date_day, y=imb.cum, name="ส่วนต่างสะสม",
                                     yaxis="y2", line=dict(color=GOLD, width=2.2)))
            fig.update_layout(barmode="relative",
                              yaxis2=dict(overlaying="y", side="right", showgrid=False,
                                          tickfont=dict(color=GOLD)))
            fig.update_yaxes(title_text="ลิตร")
            fig.update_xaxes(title_text="")
            st.plotly_chart(style(fig, 380), width="stretch")

    st.divider()
    st.markdown("#### Q14 · ยอดขายตามใบเสร็จ vs ปริมาณจ่ายออกจากถัง")
    st.caption("ส่วนต่างเป็น “จุดให้ตรวจสอบ” ไม่ใช่ข้อสรุปว่ามีน้ำมันสูญหาย")
    rec = q(f"""select cast(date_day as date) date_day, sum(quantity_sold) sold,
                       sum(quantity_out) qout, sum(diff) diff
                from {T['mart_14']} where {MW} group by 1 order by 1""", MP())
    if guard(rec):
        if rec["qout"].sum() == 0:
            st.warning("ปริมาณจ่ายออกจากถังเป็นศูนย์ทั้งหมด เพราะฝั่งคลังยังไม่มีข้อมูลที่ผ่านเกณฑ์ "
                       "ส่วนต่างที่เห็นจึงเท่ากับยอดขายทั้งหมด ไม่ใช่ความคลาดเคลื่อนจริง")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=rec.date_day, y=rec.sold, name="ขายตามใบเสร็จ", marker_color=BLUE))
        fig.add_trace(go.Bar(x=rec.date_day, y=rec.qout, name="จ่ายออกจากถัง", marker_color=CYAN))
        fig.update_layout(barmode="group")
        fig.update_yaxes(title_text="ลิตร")
        fig.update_xaxes(title_text="")
        st.plotly_chart(style(fig, 340), width="stretch")

# ===========================================================================
# TAB 6 — คุณภาพข้อมูล
# ===========================================================================
with TABS[5]:
    st.markdown("#### ธรรมาภิบาลข้อมูล (Data Quality & Governance)")
    st.caption("แถวที่มีปัญหาไม่ถูกลบทิ้ง แต่ติดธง `is_data_quality_flagged` "
               "และทุกมิติมี Unknown member รองรับคีย์ที่หาคู่ไม่ได้")

    dq = q("""
        select 'fact_sales' table_name, count(*) total_rows,
               count(*) filter (where is_data_quality_flagged) flagged_rows from fact_sales
        union all select 'fact_invoice', count(*),
               count(*) filter (where is_data_quality_flagged) from fact_invoice
        union all select 'fact_inventory_transaction', count(*),
               count(*) filter (where is_data_quality_flagged) from fact_inventory_transaction
    """)
    dq["pct"] = dq.flagged_rows / dq.total_rows.replace(0, pd.NA)

    cols = st.columns(3)
    for col, r in zip(cols, dq.itertuples()):
        kpi(col, r.table_name, f"{r.flagged_rows:,}", f" / {r.total_rows:,} แถว")
        col.caption(f"สัดส่วนที่ติดธง {0 if pd.isna(r.pct) else r.pct:.2%}")

    st.write("")
    c1, c2 = st.columns([1.2, 1])
    with c1:
        panel("สัดส่วนแถวที่ติดธงในแต่ละ Fact table", "fact_* · is_data_quality_flagged")
        d2 = dq.fillna({"pct": 0})
        fig = go.Figure(go.Bar(x=d2.table_name, y=d2.pct,
                               marker_color=[RED if v > .5 else (GOLD if v > .02 else GREEN)
                                             for v in d2.pct],
                               text=[f"{v:.1%}" for v in d2.pct], textposition="outside",
                               textfont=dict(color=INK),
                               hovertemplate="%{x}<br>%{y:.2%}<extra></extra>"))
        fig.update_yaxes(tickformat=".0%", title_text="สัดส่วนที่ติดธง", range=[0, 1.15])
        fig.update_xaxes(title_text="")
        st.plotly_chart(style(fig, 320, False), width="stretch")

    with c2:
        panel("Unknown member ในแต่ละมิติ", "แถวที่ is_unknown_member = true")
        um = q("""
            select 'dim_customer' d, count(*) filter (where is_unknown_member) unk, count(*) n from dim_customer
            union all select 'dim_employee', count(*) filter (where is_unknown_member), count(*) from dim_employee
            union all select 'dim_gasstation', count(*) filter (where is_unknown_member), count(*) from dim_gasstation
            union all select 'dim_product', count(*) filter (where is_unknown_member), count(*) from dim_product
            union all select 'dim_vehicle_category', count(*) filter (where is_unknown_member), count(*) from dim_vehicle_category
            union all select 'dim_tank', count(*) filter (where is_unknown_member), count(*) from dim_tank
        """)
        um["real"] = um.n - um.unk
        st.dataframe(um[["d", "real", "unk", "n"]], width="stretch", hide_index=True,
                     column_config={"d": "มิติ", "real": "สมาชิกจริง",
                                    "unk": "Unknown", "n": "รวม"})

    st.markdown("##### ตารางในคลังข้อมูลที่แดชบอร์ดใช้")
    names = ["dim_date", "dim_hour", "dim_customer", "dim_employee", "dim_gasstation",
             "dim_product", "dim_payment_method", "dim_vehicle_category", "dim_tank",
             "bridge_tank_product", "fact_sales", "fact_invoice",
             "fact_inventory_transaction", "int_sales_daily", "int_inventory_daily"] \
        + list(T.values())
    rows = []
    for n in names:
        try:
            rows.append({"table": n,
                         "rows": q(f'select count(*) c from "{n}"').iloc[0].c})
        except Exception:
            rows.append({"table": n, "rows": None})
    tb = pd.DataFrame(rows)
    tb["สถานะ"] = tb["rows"].map(lambda v: "ว่าง" if v == 0 else ("ไม่พบตาราง" if pd.isna(v) else "ปกติ"))
    st.dataframe(tb, width="stretch", hide_index=True,
                 column_config={"table": "ตาราง",
                                "rows": st.column_config.NumberColumn("จำนวนแถว", format="%d")})

st.markdown(f'<div style="text-align:center;color:{MUTED};font-size:.78rem;padding-top:18px;'
            f'border-top:1px solid {LINE};margin-top:22px">Fuel Station Analytics · '
            f'Star Schema (dbt + DuckDB) · ข้อมูลจาก Dimension / Fact / Mart เท่านั้น</div>',
            unsafe_allow_html=True)
